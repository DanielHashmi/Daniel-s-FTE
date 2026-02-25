"""
Approval Manager.

Handles creating approval request files and processing results.
"""

import time
import hashlib
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from src.lib.logging import get_logger
from src.lib.vault import vault
import os

from src.mcp.stdio_client import call_node_mcp_tool
from src.orchestration.rate_limiter import HourlyRateLimiter

class ApprovalManager:
    def __init__(self):
        self.logger = get_logger("approval_manager")
        # DEV_MODE forces dry-run behavior even when approvals are granted.
        self.dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        self.rate_limiter = HourlyRateLimiter(vault.root / "Config" / "rate_limits.json")

        self.rate_limits = {
            "send_email": int(os.getenv("RATE_LIMIT_EMAIL_PER_HOUR", "10")),
            "twitter_post": int(os.getenv("RATE_LIMIT_SOCIAL_PER_HOUR", "10")),
            "linkedin_post": int(os.getenv("RATE_LIMIT_SOCIAL_PER_HOUR", "10")),
            "facebook_post": int(os.getenv("RATE_LIMIT_SOCIAL_PER_HOUR", "10")),
            "instagram_post": int(os.getenv("RATE_LIMIT_SOCIAL_PER_HOUR", "10")),
            "whatsapp_post": int(os.getenv("RATE_LIMIT_SOCIAL_PER_HOUR", "10")),
            "odoo_post_invoice": int(os.getenv("RATE_LIMIT_INVOICE_POST_PER_HOUR", "20")),
        }

    @staticmethod
    def _env_int(name: str, fallback: int) -> int:
        try:
            return int(os.getenv(name, str(fallback)))
        except (TypeError, ValueError):
            return fallback

    def _facebook_timeout_seconds(self) -> int:
        """
        Return a timeout budget suitable for Playwright-based Facebook posting.

        Playwright mode may wait for human login in a visible browser tab.
        Use a higher timeout than the generic MCP default to avoid false failures.
        """
        base_timeout = max(5, self._env_int("MCP_TIMEOUT_SECONDS", 60))
        explicit_timeout = self._env_int("FACEBOOK_MCP_TIMEOUT_SECONDS", 0)
        if explicit_timeout > 0:
            return max(base_timeout, explicit_timeout)

        headless = os.getenv("FACEBOOK_HEADLESS", "false").strip().lower() == "true"
        login_wait = max(0, self._env_int("FACEBOOK_LOGIN_WAIT_SECONDS", 600))
        keep_open = max(0, self._env_int("FACEBOOK_KEEP_OPEN_SECONDS", 0))

        interactive_wait = 0 if headless else min(login_wait, 1200)
        computed_timeout = 90 + keep_open + interactive_wait
        return max(base_timeout, computed_timeout)

    def _instagram_timeout_seconds(self) -> int:
        """
        Return timeout budget for Instagram posting.

        Graph API mode is usually quick. Playwright mode may involve human login
        and should use a larger timeout window.
        """
        base_timeout = max(5, self._env_int("MCP_TIMEOUT_SECONDS", 120))
        explicit_timeout = self._env_int("INSTAGRAM_MCP_TIMEOUT_SECONDS", 0)
        if explicit_timeout > 0:
            return max(base_timeout, explicit_timeout)

        method = os.getenv("INSTAGRAM_POST_METHOD", "playwright").strip().lower()
        if method != "playwright":
            return max(base_timeout, 120)

        headless = os.getenv("INSTAGRAM_HEADLESS", "false").strip().lower() == "true"
        login_wait = max(0, self._env_int("INSTAGRAM_LOGIN_WAIT_SECONDS", 600))
        keep_open = max(0, self._env_int("INSTAGRAM_KEEP_OPEN_SECONDS", 0))

        interactive_wait = 0 if headless else min(login_wait, 1200)
        computed_timeout = 120 + keep_open + interactive_wait
        return max(base_timeout, computed_timeout)

    def _whatsapp_timeout_seconds(self) -> int:
        """
        Return timeout budget for WhatsApp Cloud API sends.
        """
        base_timeout = max(5, self._env_int("MCP_TIMEOUT_SECONDS", 60))
        explicit_timeout = self._env_int("WHATSAPP_MCP_TIMEOUT_SECONDS", 0)
        if explicit_timeout > 0:
            return max(base_timeout, explicit_timeout)
        return max(base_timeout, 120)

    def _env_for_actions(self) -> Dict[str, str]:
        env = {**os.environ}
        if self.dev_mode:
            env["DRY_RUN"] = "true"
        return env

    def _check_rate_limit(self, key: str) -> bool:
        limit = int(self.rate_limits.get(key, 0) or 0)
        if limit <= 0:
            return True
        decision = self.rate_limiter.check_and_increment(key, limit=limit)
        if decision.allowed:
            return True

        # Log and alert. Keep the approval item for retry once the window resets.
        try:
            vault.ensure_structure()
            alert_path = vault.dirs["alerts"] / f"{int(time.time())}_rate_limit_{key}.md"
            alert_path.write_text(
                f"# Rate Limit Blocked\n\n"
                f"- Action: {key}\n"
                f"- Count: {decision.count}\n"
                f"- Limit: {decision.limit} per hour\n"
                f"- Window start: {decision.window_start_iso}\n",
                encoding="utf-8",
            )
        except Exception:
            pass

        self.logger.log_action(
            action_type="rate_limit_block",
            result="failure",
            target=key,
            details={
                "count": decision.count,
                "limit": decision.limit,
                "window_start": decision.window_start_iso,
            },
        )
        return False

    def _mark_plan_completed(self, action_id: str, domain: Optional[str] = None) -> None:
        """Update the plan status to completed and add TASK_COMPLETE promise for orchestrator detection."""
        if not action_id:
            return
        plan_name = f"PLAN_{action_id}.md"

        candidates = []
        try:
            if domain:
                p = vault.get_domain_dir("plans", domain) / plan_name
                if p.exists():
                    candidates.append(p)
            if not candidates:
                candidates = vault.list_files_recursive("plans", plan_name)
        except Exception:
            candidates = []

        for plan_path in candidates:
            try:
                raw = vault.read_file(plan_path)
                parts = raw.split("---", 2)
                if len(parts) < 3:
                    continue
                meta = yaml.safe_load(parts[1]) or {}
                body = parts[2]

                meta["status"] = "completed"
                meta.setdefault("completed", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

                if "<promise>TASK_COMPLETE</promise>" not in body:
                    body = body.rstrip() + "\n\n<promise>TASK_COMPLETE</promise>\n"

                content = "---\n" + yaml.safe_dump(meta, sort_keys=False).strip() + "\n---\n" + body.lstrip()
                vault.write_file(plan_path, content)
                return
            except Exception:
                continue

    def _complete_action_files(self, action_id: str) -> None:
        """Move any in-progress action files matching action_id into Done/."""
        if not action_id:
            return
        try:
            for p in vault.list_files_recursive("in_progress", f"*{action_id}*.md"):
                try:
                    vault.move_file_safe(p, "done")
                except Exception:
                    continue
        except Exception:
            return

    def create_approval_request(self,
                              action_type: str,
                              context: Dict[str, Any],
                              details: str) -> str:
        """
        Create a file in Pending_Approval/
        """
        timestamp = int(time.time())
        unique_str = f"approval-{timestamp}-{str(context)}"
        appr_id = f"appr_{hashlib.md5(unique_str.encode()).hexdigest()[:8]}"

        filename = f"{timestamp}_{action_type}_approval.md"

        yaml_content = f"""---
id: "{appr_id}"
type: "approval"
action_type: "{action_type}"
created: "{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
status: "pending"
context:
"""
        for k, v in context.items():
            yaml_content += f"  {k}: \"{v}\"\n"

        yaml_content += "---\n\n"
        yaml_content += details

        # Write manually to Pending_Approval
        path = vault.dirs["pending_approval"] / filename
        with open(path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        self.logger.log_action(
            action_type="create_approval",
            result="success",
            target=str(path),
            details={"appr_id": appr_id}
        )

        return filename

    def _extract_social_content(self, body: str) -> str:
        """Extract post content from markdown body."""
        lines = body.split("\n")
        content_lines = []
        in_content = False

        for line in lines:
            if line.startswith("## Content"):
                in_content = True
                continue
            if line.startswith("##") and in_content:
                break
            if in_content and line.strip() == "---":
                break
            if in_content and line.strip().lower().startswith("*this post requires approval"):
                break
            if in_content:
                content_lines.append(line)

        content = "\n".join(content_lines).strip()
        if content:
            return content

        # Fallback: first non-empty non-note line
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.lower().startswith("*this post requires approval"):
                return stripped
        return ""

    def _sanitize_social_post_text(self, text: str, max_chars: int = 2200) -> str:
        """
        Remove LLM self-talk/metrics and keep a single clean post body.
        """
        if not text:
            return ""

        def is_meta_line(line: str) -> bool:
            s = line.strip()
            if not s:
                return False
            low = s.lower()
            if low.startswith("```"):
                return True
            if low in {"facebook post:", "post:", "caption:"}:
                return True
            if low.startswith(("here is", "here's", "wait", "actually", "let me", "i need to", "the output should")):
                return True
            if low.startswith("cta:"):
                return True
            if "word count" in low or "character count" in low:
                return True
            return False

        cleaned_lines = [ln.rstrip() for ln in text.splitlines() if not is_meta_line(ln)]
        cleaned = "\n".join(cleaned_lines).strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        if not cleaned:
            return ""

        blocks = [b.strip() for b in re.split(r"\n\s*\n", cleaned) if b.strip()]
        if not blocks:
            return ""

        def is_hashtag_only(block: str) -> bool:
            return bool(re.fullmatch(r"(#\w+(\s+|$))+", block))

        def score(block: str) -> int:
            low = block.lower()
            pts = 0
            if "word count" in low or "character count" in low:
                pts -= 8
            if low.startswith(("wait", "actually", "let me", "cta:")):
                pts -= 6
            if is_hashtag_only(block):
                pts -= 4
            if len(block) >= 60:
                pts += 4
            elif len(block) >= 30:
                pts += 2
            if re.search(r"[.!?]", block):
                pts += 1
            if len(block.split()) >= 10:
                pts += 1
            if re.search(r"#\w+", block):
                pts += 1
            return pts

        best_idx = max(range(len(blocks)), key=lambda idx: (score(blocks[idx]), idx))
        best = blocks[best_idx]
        if best_idx + 1 < len(blocks) and is_hashtag_only(blocks[best_idx + 1]):
            best = f"{best}\n\n{blocks[best_idx + 1]}"

        if len(best) > max_chars:
            best = best[: max_chars - 3].rstrip() + "..."
        return best.strip()

    @staticmethod
    def _extract_markdown_section(body: str, heading: str) -> str:
        if not body:
            return ""
        pattern = re.compile(
            rf"##\s*{re.escape(heading)}\s*[\r\n]+([\s\S]*?)(?:[\r\n]+##\s+|[\r\n]+\*|$)",
            re.IGNORECASE,
        )
        match = pattern.search(body)
        if not match:
            return ""
        return match.group(1).strip()

    @staticmethod
    def _normalize_hashtags_csv(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            tokens = [str(v).strip() for v in value if str(v).strip()]
        else:
            raw = str(value).strip()
            if not raw:
                return ""
            tokens = re.split(r"[,\s]+", raw)

        out = []
        seen = set()
        for token in tokens:
            if not token:
                continue
            cleaned = token if token.startswith("#") else f"#{token}"
            cleaned = re.sub(r"[^\w#]", "", cleaned)
            if cleaned in {"", "#"}:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cleaned)
        return ",".join(out[:12])

    def process_approved(self, filepath) -> bool:
        """Handle logic when a file appears in Approved/"""
        try:
            # Read file to get context
            content = vault.read_file(filepath)
            
            # Parse YAML frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                self.logger.error(f"Invalid approval file format: {filepath.name}")
                return False

            metadata = yaml.safe_load(parts[1])
            body = parts[2].strip()

            # Log the approval decision
            self.logger.log_approval_decision(
                decision="approved",
                action_file=str(filepath),
                reason="Human approved via file move to Approved/"
            )

            # Execution logic
            action = metadata.get("action") or metadata.get("action_type")
            platform = str(metadata.get("platform", "")).strip().lower()
            domain = str(metadata.get("domain") or (metadata.get("context") or {}).get("domain") or "").strip().lower() or None
            source_action_id = str(metadata.get("source_action_id") or metadata.get("action_id") or "").strip()

            # Hackathon/PBR pattern: approval_request files include action: send_email/social_post/etc.
            if action in ("send_email", "email_send"):
                if not self._check_rate_limit("send_email"):
                    return False
                to = str(metadata.get("to") or (metadata.get("context") or {}).get("to") or "").strip()
                subject = str(metadata.get("subject") or (metadata.get("context") or {}).get("subject") or "").strip()
                email_body = self._extract_social_content(body) or body
                attachment = metadata.get("attachment") or (metadata.get("context") or {}).get("attachment")
                attachments = metadata.get("attachments") or (metadata.get("context") or {}).get("attachments")

                if not to or not subject or not email_body:
                    self.logger.error(f"Missing to/subject/body for approved email: {filepath.name}")
                    return False

                mcp_path = Path("mcp-servers/email-mcp/index.js")
                if not mcp_path.exists():
                    self.logger.error(f"email-mcp server not found: {mcp_path}")
                    return False

                try:
                    att_payload = None
                    if isinstance(attachments, list) and attachments:
                        att_payload = [{"path": str(p)} for p in attachments if p]
                    elif isinstance(attachment, str) and attachment.strip():
                        att_payload = [{"path": attachment.strip()}]

                    res = call_node_mcp_tool(
                        entrypoint=mcp_path,
                        tool_name="send_email",
                        arguments={
                            "to": to,
                            "subject": subject,
                            "text": email_body,
                            **({"attachments": att_payload} if att_payload else {}),
                        },
                        timeout_seconds=int(os.getenv("MCP_TIMEOUT_SECONDS", "60")),
                        env=self._env_for_actions(),
                    )
                except Exception as e:
                    self.logger.error(f"Email MCP invocation failed: {e}")
                    return False

                if not res.ok:
                    self.logger.error(
                        "Email MCP error. "
                        f"is_tool_error={res.is_tool_error} "
                        f"content={res.content_text[:300]} "
                        f"stderr={res.stderr[:300]} stdout={res.stdout[:300]}"
                    )
                    return False

                self.logger.log_action(
                    action_type="send_email",
                    result="success",
                    target=to,
                    details={"subject": subject, "mcp": "email-mcp"},
                    approval_status="approved",
                    approved_by="human",
                )
                # Mark originating plan/action as completed (file-movement completion strategy).
                if source_action_id:
                    self._mark_plan_completed(source_action_id, domain=domain)
                    self._complete_action_files(source_action_id)
                return True

            if action in ("social_post", "post") and platform == "facebook":
                if not self._check_rate_limit("facebook_post"):
                    return False
                post_text = self._extract_social_content(body) or body.split("\n")[0]
                post_text = self._sanitize_social_post_text(post_text, max_chars=2200)
                if not post_text:
                    self.logger.error(f"Facebook post content empty after sanitization: {filepath.name}")
                    return False
                mcp_path = Path("mcp-servers/social-mcp/index.js")
                if not mcp_path.exists():
                    self.logger.error("social-mcp server not found")
                    return False
                try:
                    timeout_seconds = self._facebook_timeout_seconds()
                    res = call_node_mcp_tool(
                        entrypoint=mcp_path,
                        tool_name="post_to_facebook",
                        arguments={"content": post_text},
                        timeout_seconds=timeout_seconds,
                        env=self._env_for_actions(),
                    )
                    if not res.ok:
                        self.logger.error(
                            "Facebook post failed: "
                            f"is_tool_error={res.is_tool_error} "
                            f"content={res.content_text or (res.stderr or res.stdout)}"
                        )
                        return False
                    self.logger.log_action(
                        action_type="facebook_post",
                        result="success",
                        target=str(filepath),
                        details={
                            "mcp": "social-mcp",
                            "result": res.content_text[:200],
                            "timeout_seconds": timeout_seconds,
                        },
                        approval_status="approved",
                        approved_by="human",
                    )
                    if source_action_id:
                        self._mark_plan_completed(source_action_id, domain=domain)
                        self._complete_action_files(source_action_id)
                    return True
                except Exception as e:
                    self.logger.error(f"Facebook post exception: {e}")
                    return False

            elif action in ("social_post", "post") and platform == "twitter":
                if not self._check_rate_limit("twitter_post"):
                    return False
                # Extract content from body
                # The body has headers like ## Content
                tweet_text = self._extract_social_content(body)
                if not tweet_text:
                    tweet_text = body.split("\n")[0] # Fallback to first line
                tweet_text = self._sanitize_social_post_text(tweet_text, max_chars=280)
                if not tweet_text:
                    self.logger.error(f"Twitter post content empty after sanitization: {filepath.name}")
                    return False

                self.logger.info(f"Executing tweet: {tweet_text[:50]}...")
                
                # Call social-mcp
                mcp_path = Path("mcp-servers/social-mcp/index.js")
                if mcp_path.exists():
                    try:
                        res = call_node_mcp_tool(
                            entrypoint=mcp_path,
                            tool_name="post_to_twitter",
                            arguments={"content": tweet_text},
                            timeout_seconds=int(os.getenv("MCP_TIMEOUT_SECONDS", "60")),
                            env=self._env_for_actions(),
                        )
                        if not res.ok:
                            self.logger.error(
                                "Tweet execution failed: "
                                f"is_tool_error={res.is_tool_error} "
                                f"content={res.content_text or (res.stderr or res.stdout)}"
                            )
                            return False
                        self.logger.log_action(
                            action_type="twitter_post",
                            result="success",
                            target=str(filepath),
                            details={"mcp": "social-mcp", "result": res.content_text[:200]},
                            approval_status="approved",
                            approved_by="human",
                        )
                        if source_action_id:
                            self._mark_plan_completed(source_action_id, domain=domain)
                            self._complete_action_files(source_action_id)
                        return True
                    except Exception as e:
                        self.logger.error(f"Tweet execution exception: {e}")
                        return False
                else:
                    self.logger.error("social-mcp server not found")
                    return False

            elif action in ("social_post", "post") and platform == "linkedin":
                if not self._check_rate_limit("linkedin_post"):
                    return False
                post_text = self._extract_social_content(body) or body.split("\n")[0]
                post_text = self._sanitize_social_post_text(post_text, max_chars=3000)
                if not post_text:
                    self.logger.error(f"LinkedIn post content empty after sanitization: {filepath.name}")
                    return False
                mcp_path = Path("mcp-servers/social-mcp/index.js")
                if not mcp_path.exists():
                    self.logger.error("social-mcp server not found")
                    return False
                try:
                    res = call_node_mcp_tool(
                        entrypoint=mcp_path,
                        tool_name="post_to_linkedin",
                        arguments={"content": post_text, "visibility": metadata.get("visibility", "PUBLIC")},
                        timeout_seconds=int(os.getenv("MCP_TIMEOUT_SECONDS", "60")),
                        env=self._env_for_actions(),
                    )
                    if not res.ok:
                        self.logger.error(
                            "LinkedIn post failed: "
                            f"is_tool_error={res.is_tool_error} "
                            f"content={res.content_text or (res.stderr or res.stdout)}"
                        )
                        return False
                    self.logger.log_action(
                        action_type="linkedin_post",
                        result="success",
                        target=str(filepath),
                        details={"mcp": "social-mcp", "result": res.content_text[:200]},
                        approval_status="approved",
                        approved_by="human",
                    )
                    if source_action_id:
                        self._mark_plan_completed(source_action_id, domain=domain)
                        self._complete_action_files(source_action_id)
                    return True
                except Exception as e:
                    self.logger.error(f"LinkedIn post exception: {e}")
                    return False

            elif action in ("social_post", "post") and platform == "instagram":
                if not self._check_rate_limit("instagram_post"):
                    return False
                image_url = str(
                    metadata.get("image_url")
                    or (metadata.get("context") or {}).get("image_url")
                    or self._extract_markdown_section(body, "Image URL")
                    or ""
                ).strip()
                caption = str(
                    metadata.get("caption")
                    or (metadata.get("context") or {}).get("caption")
                    or self._extract_social_content(body)
                    or ""
                ).strip()
                caption = self._sanitize_social_post_text(caption, max_chars=2200)
                hashtags_raw = (
                    metadata.get("hashtags")
                    or (metadata.get("context") or {}).get("hashtags")
                    or self._extract_markdown_section(body, "Hashtags")
                )
                hashtags = self._normalize_hashtags_csv(hashtags_raw)
                if not image_url or not caption:
                    self.logger.error(f"Missing image_url/caption for Instagram post: {filepath.name}")
                    return False
                mcp_path = Path("mcp-servers/social-mcp/index.js")
                if not mcp_path.exists():
                    self.logger.error("social-mcp server not found")
                    return False
                try:
                    timeout_seconds = self._instagram_timeout_seconds()
                    res = call_node_mcp_tool(
                        entrypoint=mcp_path,
                        tool_name="post_to_instagram",
                        arguments={
                            "image_url": image_url,
                            "caption": caption,
                            **({"hashtags": hashtags} if hashtags else {}),
                        },
                        timeout_seconds=timeout_seconds,
                        env=self._env_for_actions(),
                    )
                    if not res.ok:
                        self.logger.error(
                            "Instagram post failed: "
                            f"is_tool_error={res.is_tool_error} "
                            f"content={res.content_text or (res.stderr or res.stdout)}"
                        )
                        return False
                    self.logger.log_action(
                        action_type="instagram_post",
                        result="success",
                        target=str(filepath),
                        details={
                            "mcp": "social-mcp",
                            "result": res.content_text[:200],
                            "timeout_seconds": timeout_seconds,
                            "method": os.getenv("INSTAGRAM_POST_METHOD", "playwright"),
                        },
                        approval_status="approved",
                        approved_by="human",
                    )
                    if source_action_id:
                        self._mark_plan_completed(source_action_id, domain=domain)
                        self._complete_action_files(source_action_id)
                    return True
                except Exception as e:
                    self.logger.error(f"Instagram post exception: {e}")
                    return False

            elif action in ("social_post", "post") and platform == "whatsapp":
                if not self._check_rate_limit("whatsapp_post"):
                    return False
                recipient = str(
                    metadata.get("to")
                    or metadata.get("whatsapp_to")
                    or (metadata.get("context") or {}).get("to")
                    or (metadata.get("context") or {}).get("whatsapp_to")
                    or self._extract_markdown_section(body, "Recipient")
                    or ""
                ).strip()
                message_text = self._extract_social_content(body) or body.split("\n")[0]
                message_text = self._sanitize_social_post_text(message_text, max_chars=4096)
                if not recipient or not message_text:
                    self.logger.error(f"Missing recipient/content for WhatsApp post: {filepath.name}")
                    return False
                if not re.fullmatch(r"\+?[1-9]\d{6,14}", recipient):
                    self.logger.error(f"Invalid WhatsApp recipient format (E.164 expected): {recipient}")
                    return False
                mcp_path = Path("mcp-servers/social-mcp/index.js")
                if not mcp_path.exists():
                    self.logger.error("social-mcp server not found")
                    return False
                try:
                    timeout_seconds = self._whatsapp_timeout_seconds()
                    res = call_node_mcp_tool(
                        entrypoint=mcp_path,
                        tool_name="post_to_whatsapp",
                        arguments={
                            "to": recipient,
                            "content": message_text,
                        },
                        timeout_seconds=timeout_seconds,
                        env=self._env_for_actions(),
                    )
                    if not res.ok:
                        self.logger.error(
                            "WhatsApp post failed: "
                            f"is_tool_error={res.is_tool_error} "
                            f"content={res.content_text or (res.stderr or res.stdout)}"
                        )
                        return False
                    self.logger.log_action(
                        action_type="whatsapp_post",
                        result="success",
                        target=str(filepath),
                        details={
                            "mcp": "social-mcp",
                            "recipient": recipient,
                            "result": res.content_text[:200],
                            "timeout_seconds": timeout_seconds,
                        },
                        approval_status="approved",
                        approved_by="human",
                    )
                    if source_action_id:
                        self._mark_plan_completed(source_action_id, domain=domain)
                        self._complete_action_files(source_action_id)
                    return True
                except Exception as e:
                    self.logger.error(f"WhatsApp post exception: {e}")
                    return False

            elif metadata.get('type') == 'invoice_posting' and action == 'post':
                invoice_id = metadata.get('invoice_id')
                if invoice_id:
                    if not self._check_rate_limit("odoo_post_invoice"):
                        return False
                    self.logger.info(f"Executing Odoo invoice post: {invoice_id}")
                    try:
                        # Use Odoo MCP server (gold/platinum requirement)
                        mcp_path = Path("deployment/cloud/odoo-mcp.js")
                        if not mcp_path.exists():
                            self.logger.error(f"Odoo MCP server not found: {mcp_path}")
                            return False

                        res = call_node_mcp_tool(
                            entrypoint=mcp_path,
                            tool_name="post_invoice",
                            arguments={"invoice_id": int(invoice_id), "mode": "live", "require_approval": False},
                            timeout_seconds=int(os.getenv("MCP_TIMEOUT_SECONDS", "120")),
                            env=self._env_for_actions(),
                        )
                        if not res.ok:
                            self.logger.error(
                                "Invoice post failed: "
                                f"is_tool_error={res.is_tool_error} "
                                f"content={res.content_text or (res.stderr or res.stdout)}"
                            )
                            return False
                        self.logger.log_action(
                            action_type="odoo_post_invoice",
                            result="success",
                            target=str(filepath),
                            details={"mcp": "odoo-mcp", "result": res.content_text[:200]},
                            approval_status="approved",
                            approved_by="human",
                        )
                        if source_action_id:
                            self._mark_plan_completed(source_action_id, domain=domain)
                            self._complete_action_files(source_action_id)
                        return True
                    except Exception as e:
                        self.logger.error(f"Invoice post failed: {e}")
                        return False
                else:
                    self.logger.error("Missing invoice_id in approval metadata")
                    return False

            else:
                self.logger.info(f"Approved action ready for execution (No automatic handler): {filepath.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error processing approved file {filepath}: {e}")
            return False

    def process_rejected(self, filepath) -> bool:
        """Handle logic when a file appears in Rejected/"""
        try:
            # Read file to get context
            content = vault.read_file(filepath)

            # Log the rejection decision
            self.logger.log_approval_decision(
                decision="rejected",
                action_file=str(filepath),
                reason="Human rejected via manage-approval skill"
            )

            # Cancel the plan
            self.logger.info(f"Rejected action cancelled: {filepath.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing rejected file {filepath}: {e}")
            return False
