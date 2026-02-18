#!/usr/bin/env python3
"""email-ops skill

Email operations through MCP (email-mcp).
- send: calls MCP tool `send_email`
- list-sent: reads audit logs for recent email sends
- status: checks MCP server availability and dry-run mode
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger
from src.mcp.stdio_client import call_node_mcp_tool

logger = get_logger("email_ops_skill")
VAULT_ROOT = PROJECT_ROOT / "AI_Employee_Vault"
LOGS_DIR = VAULT_ROOT / "Logs"
EMAIL_MCP = PROJECT_ROOT / "mcp-servers" / "email-mcp" / "index.js"


def _parse_log_file(path: Path) -> List[Dict[str, Any]]:
    """Support both JSON array files and JSON-lines files."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []

    entries: List[Dict[str, Any]] = []

    # Try JSON array/object first.
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [e for e in data if isinstance(e, dict)]
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # Fallback: JSON lines.
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            entries.append(obj)
    return entries


def _iter_recent_log_entries(days: int = 7) -> Iterable[Dict[str, Any]]:
    if not LOGS_DIR.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    entries: List[Dict[str, Any]] = []

    for log_file in sorted(LOGS_DIR.glob("*.json"), reverse=True):
        # Date-named files are the main audit logs.
        if len(log_file.stem) != 10:
            continue
        for entry in _parse_log_file(log_file):
            ts_raw = entry.get("timestamp")
            if not ts_raw:
                entries.append(entry)
                continue
            try:
                ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    entries.append(entry)
            except Exception:
                entries.append(entry)

    return entries


def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: List[str],
    dry_run: bool,
) -> int:
    if not EMAIL_MCP.exists():
        print(f"email-mcp server not found: {EMAIL_MCP}", file=sys.stderr)
        return 1

    env = dict(os.environ)
    if dry_run:
        env["DRY_RUN"] = "true"

    args: Dict[str, Any] = {
        "to": to,
        "subject": subject,
        "text": body,
    }
    if attachments:
        args["attachments"] = [{"path": p} for p in attachments if p]

    result = call_node_mcp_tool(
        entrypoint=EMAIL_MCP,
        tool_name="send_email",
        arguments=args,
        timeout_seconds=int(os.getenv("EMAIL_MCP_TIMEOUT_SECONDS", "60")),
        env=env,
    )

    if result.ok:
        msg = result.content_text or "email-mcp send_email completed"
        print(msg)
        logger.log_action(
            action_type="email_send",
            result="success",
            target=to,
            parameters={"subject": subject, "attachments": attachments},
            details={"mcp": "email-mcp", "dry_run": dry_run, "response": msg[:300]},
            approval_status="approved",
            approved_by="human",
        )
        return 0

    err = (result.stderr or result.stdout or "Unknown MCP error").strip()
    print(f"Email send failed: {err}", file=sys.stderr)
    logger.log_action(
        action_type="email_send",
        result="failure",
        target=to,
        parameters={"subject": subject, "attachments": attachments},
        details={"mcp": "email-mcp", "dry_run": dry_run, "error": err[:500]},
        approval_status="approved",
        approved_by="human",
    )
    return 1


def list_sent(limit: int, days: int) -> int:
    sent_rows: List[Dict[str, Any]] = []
    for entry in _iter_recent_log_entries(days=days):
        action_type = str(entry.get("action_type") or "").strip().lower()
        if action_type not in {"email_send", "email_op", "send_email"}:
            continue
        result = str(entry.get("result") or "").strip().lower()
        if "success" not in result:
            continue
        sent_rows.append(entry)

    if not sent_rows:
        print("No sent emails found in logs.")
        return 0

    print(f"Recent sent emails (last {days} day(s))")
    print("-" * 80)
    for entry in sent_rows[: max(1, limit)]:
        ts = entry.get("timestamp", "")
        target = entry.get("target", "")
        params = entry.get("parameters") or {}
        subject = ""
        if isinstance(params, dict):
            subject = str(params.get("subject") or "")
        print(f"[{ts}] to={target} subject={subject}")
    return 0


def status() -> int:
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    print("Email Ops status")
    print("-" * 40)
    print(f"email-mcp: {'ready' if EMAIL_MCP.exists() else 'missing'}")
    print(f"DRY_RUN: {str(dry_run).lower()}")
    return 0 if EMAIL_MCP.exists() else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Email operations via MCP")
    parser.add_argument("--action", required=True, choices=["send", "list-sent", "status"])
    parser.add_argument("--to", help="Recipient email")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body", help="Email body")
    parser.add_argument("--attachment", action="append", default=[], help="Attachment path (repeatable)")
    parser.add_argument("--limit", type=int, default=5, help="Max rows for list-sent")
    parser.add_argument("--days", type=int, default=7, help="Lookback window for list-sent")
    parser.add_argument("--dry-run", action="store_true", help="Force DRY_RUN=true for this command")
    args = parser.parse_args()

    if args.action == "send":
        if not args.to or not args.subject or not args.body:
            print("--to, --subject, and --body are required for send", file=sys.stderr)
            return 1
        return send_email(
            to=args.to,
            subject=args.subject,
            body=args.body,
            attachments=list(args.attachment or []),
            dry_run=args.dry_run or (os.getenv("DRY_RUN", "true").lower() == "true"),
        )

    if args.action == "list-sent":
        return list_sent(limit=args.limit, days=args.days)

    return status()


if __name__ == "__main__":
    raise SystemExit(main())
