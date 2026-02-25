"""
Draft Manager.

Creates human-reviewable approval request files (Pending_Approval/) by drafting
the *exact* content to be sent/posted later by the Local executor.

This is the Platinum pattern:
Cloud drafts -> Pending_Approval -> Human moves to Approved -> Local executes via MCP.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.lib.logging import get_gold_tier_logger
from src.lib.vault import vault


_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_qwen_path() -> Optional[str]:
    default_bin = "qwen.cmd" if os.name == "nt" else "qwen"
    configured = os.getenv("QWEN_PATH", default_bin)
    resolved = shutil.which(configured)
    if resolved:
        return resolved
    # Common npm path on Windows.
    if os.name == "nt":
        npm_path = os.path.expandvars(r"%APPDATA%\\npm\\qwen.cmd")
        if os.path.exists(npm_path):
            return npm_path
    return None


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


@dataclass
class EmailDraft:
    to: str
    subject: str
    body: str


@dataclass
class SocialDraft:
    platform: str
    content: str


class DraftManager:
    def __init__(self, agent_id: str, agent_role: str):
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.logger = get_gold_tier_logger("draft_manager")
        self.qwen_path = _resolve_qwen_path()

    @property
    def qwen_available(self) -> bool:
        return bool(self.qwen_path)

    def _run_qwen(self, prompt: str, timeout_seconds: int = 120) -> str:
        if not self.qwen_path:
            raise RuntimeError("Qwen CLI is not available (set QWEN_PATH or add qwen to PATH).")

        result = subprocess.run(
            [self.qwen_path, "-y", "--input-format", "text"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "").strip()[:500])
        return (result.stdout or "").strip()

    def _write_pending_approval(
        self,
        filename: str,
        frontmatter: Dict[str, Any],
        body: str,
        domain: Optional[str] = None,
    ) -> Path:
        vault.ensure_structure()
        dir_path = vault.get_domain_dir("pending_approval", domain)
        dir_path.mkdir(parents=True, exist_ok=True)
        path = dir_path / filename
        content = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False).strip() + "\n---\n\n" + body.strip() + "\n"
        path.write_text(content, encoding="utf-8")
        return path

    def draft_email_reply(self, action_file: Path) -> Optional[Path]:
        """Create a Pending_Approval email draft from an email Action File."""
        try:
            raw = vault.read_file(action_file)
        except Exception as exc:
            self.logger.log_action_with_duration(
                action_type="draft_email",
                result="error",
                target=str(action_file),
                error=exc,
            )
            return None

        parts = raw.split("---", 2)
        if len(parts) < 3:
            self.logger.log_action_with_duration(
                action_type="draft_email",
                result="failure",
                target=str(action_file),
                details={"reason": "missing_frontmatter"},
            )
            return None

        meta = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()
        domain = str(meta.get("domain") or "").strip().lower() or "general"

        sender = (meta.get("metadata", {}) or {}).get("sender") or meta.get("sender") or ""
        subject_in = (meta.get("metadata", {}) or {}).get("subject") or meta.get("subject") or ""
        action_id = meta.get("id") or action_file.stem

        # Best-effort: reply-to sender.
        to = sender
        if "<" in sender and ">" in sender:
            candidate = sender.split("<", 1)[1].split(">", 1)[0].strip()
            if candidate:
                to = candidate

        if not to or not _EMAIL_RE.search(to):
            # Don't guess recipients.
            self.logger.log_action_with_duration(
                action_type="draft_email",
                result="failure",
                target=str(action_file),
                details={"reason": "invalid_sender_email", "sender": sender[:120]},
            )
            return None

        prompt = (
            "You are an AI assistant drafting an email reply.\n"
            "Return ONLY a JSON object with keys: to, subject, body.\n"
            "Rules:\n"
            "- body must be plain text, no markdown.\n"
            "- be concise and professional.\n"
            "- do not invent facts.\n"
            "- if missing info, ask 1-2 clarifying questions in the body.\n\n"
            f"EMAIL TO REPLY TO:\n{body}\n\n"
            f"RECIPIENT (reply-to): {to}\n"
            f"SUBJECT: {subject_in}\n\n"
            'OUTPUT JSON ONLY:\n{"to":"...","subject":"...","body":"..."}\n'
        )

        try:
            raw_out = self._run_qwen(prompt, timeout_seconds=int(os.getenv("QWEN_TIMEOUT_SECONDS", "120")))
            payload = _extract_json_object(raw_out)
            if not payload:
                raise RuntimeError("Qwen did not return valid JSON.")

            draft = EmailDraft(
                to=str(payload.get("to", to)).strip(),
                subject=str(payload.get("subject", "")).strip(),
                body=str(payload.get("body", "")).strip(),
            )

            if not draft.to or not _EMAIL_RE.search(draft.to):
                raise RuntimeError("Draft missing/invalid 'to'.")
            if not draft.subject:
                draft.subject = f"Re: {subject_in}".strip() if subject_in else "Re:"
            if not draft.body:
                raise RuntimeError("Draft missing 'body'.")

        except Exception as exc:
            self.logger.log_action_with_duration(
                action_type="draft_email",
                result="warning",
                target=str(action_file),
                error=exc,
                details={"action_id": action_id, "fallback": "template_email_draft"},
            )
            # Fallback: deterministic template draft so cloud->local handover still works.
            fallback_subject = f"Re: {subject_in}".strip() if subject_in else "Re:"
            fallback_body = (
                "Thanks for your message. I reviewed your request and prepared the next steps.\n\n"
                "Please confirm the exact details you'd like us to include, and we will send the final response promptly."
            )
            draft = EmailDraft(
                to=to,
                subject=fallback_subject,
                body=fallback_body,
            )

        timestamp = int(time.time())
        filename = f"{timestamp}_EMAIL_{action_id}.md"
        frontmatter = {
            "type": "approval_request",
            "action": "send_email",
            "created": _utc_now_iso(),
            "status": "pending",
            "agent_role": self.agent_role,
            "agent_id": self.agent_id,
            "source_action_id": action_id,
            "domain": domain,
            "to": draft.to,
            "subject": draft.subject,
        }
        approval_body = f"# Email Draft\n\n## Content\n{draft.body}\n\n---\n\nMove this file to `Approved/` to send, or `Rejected/` to cancel.\n"

        try:
            approval_path = self._write_pending_approval(filename, frontmatter, approval_body, domain=domain)
            self.logger.log_action_with_duration(
                action_type="draft_email",
                result="success",
                target=str(approval_path),
                details={"source_action_id": action_id},
                approval_status="pending",
            )
            return approval_path
        except Exception as exc:
            self.logger.log_action_with_duration(
                action_type="draft_email",
                result="error",
                target=str(action_file),
                error=exc,
                details={"filename": filename},
            )
            return None

    def draft_social_post(
        self,
        platform: str,
        prompt_text: str,
        source_action_id: str,
        *,
        domain: str = "business",
        auto_approve: bool = False,
    ) -> Optional[Path]:
        """Create a Pending_Approval social draft for the given platform."""
        platform_norm = (platform or "").strip().lower()
        if platform_norm not in {"twitter", "linkedin", "facebook", "instagram", "whatsapp"}:
            self.logger.log_action_with_duration(
                action_type="draft_social",
                result="failure",
                target=platform_norm or "unknown",
                details={"reason": "unsupported_platform"},
            )
            return None

        # Note: Facebook/Instagram final execution in this repo may be Playwright; still draft here.
        prompt = (
            "You are an AI assistant drafting a social media post.\n"
            "Return ONLY a JSON object with keys: platform, content.\n"
            "Rules:\n"
            "- content must be plain text.\n"
            "- do not include markdown.\n"
            "- do not invent facts.\n"
            "- keep within typical platform limits (Twitter <= 280 chars, WhatsApp <= 4096 chars).\n\n"
            f"PLATFORM: {platform_norm}\n"
            f"TOPIC / INSTRUCTIONS:\n{prompt_text}\n\n"
            'OUTPUT JSON ONLY:\n{"platform":"...","content":"..."}\n'
        )

        try:
            raw_out = self._run_qwen(prompt, timeout_seconds=int(os.getenv("QWEN_TIMEOUT_SECONDS", "120")))
            payload = _extract_json_object(raw_out)
            if not payload:
                raise RuntimeError("Qwen did not return valid JSON.")

            draft = SocialDraft(
                platform=str(payload.get("platform", platform_norm)).strip().lower(),
                content=str(payload.get("content", "")).strip(),
            )
            if draft.platform != platform_norm:
                draft.platform = platform_norm
            if not draft.content:
                raise RuntimeError("Draft missing 'content'.")
            if platform_norm == "twitter" and len(draft.content) > 280:
                draft.content = draft.content[:277].rstrip() + "..."
            if platform_norm == "whatsapp" and len(draft.content) > 4096:
                draft.content = draft.content[:4093].rstrip() + "..."

        except Exception as exc:
            self.logger.log_action_with_duration(
                action_type="draft_social",
                result="warning",
                target=platform_norm,
                error=exc,
                details={"source_action_id": source_action_id, "fallback": "template_social_draft"},
            )
            # Fallback: deterministic text from prompt so HITL queue is still produced.
            fallback = "Planned update: " + " ".join((prompt_text or "").split())
            if not fallback.strip():
                fallback = f"Scheduled {platform_norm} update."
            if platform_norm == "twitter" and len(fallback) > 280:
                fallback = fallback[:277].rstrip() + "..."
            if platform_norm == "whatsapp" and len(fallback) > 4096:
                fallback = fallback[:4093].rstrip() + "..."
            draft = SocialDraft(platform=platform_norm, content=fallback)

        timestamp = int(time.time())
        filename = f"{timestamp}_SOCIAL_{platform_norm}_{source_action_id}.md"
        frontmatter = {
            "type": "approval_request",
            "action": "social_post",
            "platform": platform_norm,
            "created": _utc_now_iso(),
            "status": "pending",
            "agent_role": self.agent_role,
            "agent_id": self.agent_id,
            "source_action_id": source_action_id,
        }
        approval_body = f"# Social Post Draft ({platform_norm})\n\n## Content\n{draft.content}\n\n---\n\nMove this file to `Approved/` to post, or `Rejected/` to cancel.\n"

        try:
            domain = str(domain or "").strip().lower() or "general"
            frontmatter["domain"] = domain
            if auto_approve:
                frontmatter["auto_approve"] = True
            approval_path = self._write_pending_approval(filename, frontmatter, approval_body, domain=domain)
            self.logger.log_action_with_duration(
                action_type="draft_social",
                result="success",
                target=str(approval_path),
                details={"platform": platform_norm, "source_action_id": source_action_id},
                approval_status="pending",
            )
            return approval_path
        except Exception as exc:
            self.logger.log_action_with_duration(
                action_type="draft_social",
                result="error",
                target=platform_norm,
                error=exc,
                details={"filename": filename},
            )
            return None
