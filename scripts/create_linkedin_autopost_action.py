#!/usr/bin/env python3
"""
Create a LinkedIn auto-post Action File in the vault.

This is used with Task Scheduler / cron to satisfy the hackathon requirement:
\"Automatically Post on LinkedIn about business to generate sales\".

Pipeline:
scheduled script -> Needs_Action/business/ SOCIAL action -> cloud drafts Pending_Approval -> local auto-approves (optional) -> local posts via social-mcp
"""

from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)

    # Ensure imports work even when called from Task Scheduler
    import sys

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.lib.vault import vault

    vault.ensure_structure()

    ts = int(time.time())
    action_basis = f"linkedin_autopost|{ts}"
    action_id = f"act_{hashlib.md5(action_basis.encode('utf-8')).hexdigest()[:10]}"

    frontmatter: Dict[str, Any] = {
        "id": action_id,
        "type": "social",
        "source": "scheduler",
        "domain": "business",
        "priority": "low",
        "timestamp": _utc_now_iso(),
        "status": "pending",
        "metadata": {
            "platform": "linkedin",
            # When true, local agent may auto-approve scheduled posts (policy-controlled).
            "auto_approve": os.getenv("LINKEDIN_AUTO_APPROVE", "false").lower() == "true",
        },
    }

    body = (
        "# LinkedIn Auto-Post Request\n\n"
        "## Content\n"
        "Draft a LinkedIn post that helps generate sales.\n"
        "Use Business_Goals.md and recent activity (Plans/Done/Logs) as context.\n"
        "Constraints:\n"
        "- Keep it concise and professional\n"
        "- Include a clear call-to-action\n"
        "- Do not invent numbers or claims; if unsure, stay generic\n"
    )

    content = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False).strip() + "\n---\n\n" + body + "\n"
    filename = f"SOCIAL_{action_id}.md"
    path = vault.write_action(filename, content, domain="business")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

