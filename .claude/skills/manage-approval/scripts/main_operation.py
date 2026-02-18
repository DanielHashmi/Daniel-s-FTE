#!/usr/bin/env python3
"""manage-approval skill

Lists, approves, and rejects HITL approval request files.

Supports Platinum domain routing:
- Pending_Approval/<domain>/
- Approved/<domain>/
- Rejected/<domain>/
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger
from src.lib.vault import vault

logger = get_logger("manage_approval_skill")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_frontmatter(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


def _list_pending() -> List[Path]:
    base = vault.dirs["pending_approval"]
    if not base.exists():
        return []
    return sorted([p for p in base.rglob("*.md") if p.is_file()], key=lambda p: p.name)


def list_approvals() -> int:
    files = _list_pending()
    if not files:
        print("No pending approvals.")
        return 0

    print(f"{'FILE':<45} | {'ACTION':<14} | {'PLATFORM':<10} | {'DOMAIN':<10} | {'CREATED'}")
    print("-" * 110)

    for f in files:
        meta = _read_frontmatter(f)
        action = str(meta.get("action") or meta.get("action_type") or "").strip()
        platform = str(meta.get("platform") or "").strip()
        domain = str(meta.get("domain") or "").strip()
        created = str(meta.get("created") or meta.get("timestamp") or "").strip()
        rel = f.relative_to(vault.root)
        print(f"{str(rel):<45} | {action:<14} | {platform:<10} | {domain:<10} | {created}")

    return 0


def _resolve_pending_file(file_id: str) -> Optional[Path]:
    if not file_id:
        return None

    base = vault.dirs["pending_approval"]
    exact = base / file_id
    if exact.exists():
        return exact

    if not file_id.endswith(".md"):
        exact = base / f"{file_id}.md"
        if exact.exists():
            return exact

    matches = [p for p in base.rglob(f"*{file_id}*") if p.is_file()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Ambiguous ID '{file_id}'. Matches:")
        for m in matches:
            print(f"- {m.relative_to(vault.root)}")
        return None

    print(f"Not found in Pending_Approval: {file_id}")
    return None


def approve(file_id: str) -> int:
    f = _resolve_pending_file(file_id)
    if not f:
        return 1

    meta = _read_frontmatter(f)
    domain = str(meta.get("domain") or "").strip().lower() or None

    dest_dir = vault.get_domain_dir("approved", domain)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f.name

    try:
        shutil.move(str(f), str(dest))
        print(f"Approved: {dest.relative_to(vault.root)}")
        logger.log_action(
            action_type="approval_workflow",
            result="success",
            target=str(dest),
            details={"decision": "approved", "source": str(f)},
            approval_status="approved",
            approved_by="human",
        )
        return 0
    except Exception as e:
        print(f"Failed to approve: {e}")
        logger.log_action(
            action_type="approval_workflow",
            result="error",
            target=str(f),
            details={"decision": "approved", "error": str(e)},
            approval_status="approved",
            approved_by="human",
        )
        return 1


def reject(file_id: str, reason: str) -> int:
    f = _resolve_pending_file(file_id)
    if not f:
        return 1

    meta = _read_frontmatter(f)
    domain = str(meta.get("domain") or "").strip().lower() or None

    dest_dir = vault.get_domain_dir("rejected", domain)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f.name

    try:
        raw = f.read_text(encoding="utf-8", errors="replace")
        note = (
            "\n\n## Rejection Info\n"
            f"- Rejected At: {_utc_now_iso()}\n"
            f"- Reason: {reason}\n"
        )
        dest.write_text(raw + note, encoding="utf-8")
        f.unlink()

        print(f"Rejected: {dest.relative_to(vault.root)}")
        logger.log_action(
            action_type="approval_workflow",
            result="success",
            target=str(dest),
            details={"decision": "rejected", "reason": reason},
            approval_status="rejected",
            approved_by="human",
        )
        return 0
    except Exception as e:
        print(f"Failed to reject: {e}")
        logger.log_action(
            action_type="approval_workflow",
            result="error",
            target=str(f),
            details={"decision": "rejected", "error": str(e)},
            approval_status="rejected",
            approved_by="human",
        )
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage approval queue")
    parser.add_argument("--action", required=True, choices=["list", "approve", "reject"])
    parser.add_argument("--id", help="File ID or name for approve/reject")
    parser.add_argument("--reason", help="Reason for rejection")

    args = parser.parse_args()
    vault.ensure_structure()

    if args.action == "list":
        return list_approvals()

    if args.action == "approve":
        if not args.id:
            print("--id is required")
            return 1
        return approve(args.id)

    if args.action == "reject":
        if not args.id or not args.reason:
            print("--id and --reason are required")
            return 1
        return reject(args.id, args.reason)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
