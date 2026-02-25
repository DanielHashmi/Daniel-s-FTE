#!/usr/bin/env python3
"""error-recovery skill (Gold Tier)

Provides operational tooling for error recovery and graceful degradation:
- quarantine malformed/corrupted files
- inspect recovery queue
- archive logs older than retention
- create alerts for human review

The always-on orchestrator already implements runtime retry/backoff; this skill is for
manual ops and incident response.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger
from src.lib.vault import vault

logger = get_logger("error_recovery_skill")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_recovery(limit: int = 50) -> int:
    vault.ensure_structure()
    files = sorted([p for p in vault.dirs["recovery_queue"].rglob("*") if p.is_file()], key=lambda p: p.name)
    if not files:
        print("Recovery_Queue is empty.")
        return 0

    print("Recovery_Queue:")
    for p in files[:limit]:
        rel = p.relative_to(vault.root)
        print(f"- {rel}")

    logger.log_action(
        action_type="recovery_list",
        result="success",
        target="Recovery_Queue",
        parameters={"count": len(files)},
        approval_status="not_required",
    )
    return 0


def quarantine(path: str, reason: str) -> int:
    vault.ensure_structure()
    p = Path(path)
    if not p.is_absolute():
        p = vault.root / path

    if not p.exists():
        print(f"Not found: {p}")
        return 1

    q = vault.quarantine_file(p, reason=reason)
    print(f"Quarantined: {q.relative_to(vault.root)}")

    logger.log_action(
        action_type="quarantine_file",
        result="success",
        target=str(q),
        details={"reason": reason},
        approval_status="not_required",
    )
    return 0


def archive_logs(days_old: int = 90) -> int:
    vault.ensure_structure()
    archived = vault.archive_old_logs(days_old=days_old)
    print(f"Archived {len(archived)} log file(s).")
    logger.log_action(
        action_type="archive_old_logs",
        result="success",
        target=str(vault.dirs["logs"]),
        parameters={"days_old": days_old, "archived": len(archived)},
        approval_status="not_required",
    )
    return 0


def create_alert(message: str) -> int:
    vault.ensure_structure()
    ts = int(time.time() * 1000)
    path = vault.dirs["alerts"] / f"{ts}_manual_alert.md"
    path.write_text(
        f"# Alert\n\nTimestamp: {_utc_now_iso()}\n\n{message.strip()}\n",
        encoding="utf-8",
    )
    print(str(path.relative_to(vault.root)))
    logger.log_action(
        action_type="create_alert",
        result="success",
        target=str(path),
        approval_status="not_required",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Error recovery operations")
    parser.add_argument("--action", required=True, choices=["list-recovery", "quarantine", "archive-logs", "alert"])
    parser.add_argument("--path", help="Path of file to quarantine")
    parser.add_argument("--reason", help="Reason for quarantine")
    parser.add_argument("--days-old", type=int, default=90)
    parser.add_argument("--message", help="Alert message")
    parser.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()

    if args.action == "list-recovery":
        return list_recovery(limit=int(args.limit))

    if args.action == "quarantine":
        if not args.path or not args.reason:
            print("--path and --reason are required")
            return 1
        return quarantine(args.path, args.reason)

    if args.action == "archive-logs":
        return archive_logs(days_old=int(args.days_old))

    if args.action == "alert":
        if not args.message:
            print("--message is required")
            return 1
        return create_alert(args.message)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
