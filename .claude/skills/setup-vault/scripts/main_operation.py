#!/usr/bin/env python3
"""setup-vault skill

Initialize AI_Employee_Vault for Bronze->Platinum requirements.
Creates required folders, domain subfolders, and core template files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger

logger = get_logger("setup_vault_skill")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


BASE_DIRS: List[str] = [
    "Inbox",
    "Needs_Action",
    "In_Progress",
    "Plans",
    "Done",
    "Logs",
    "Pending_Approval",
    "Approved",
    "Rejected",
    "Signals",
    "Accounting",
    "Briefings",
    "Recovery_Queue",
    "Quarantine",
    "Alerts",
    "Ralph_State",
    "Ralph_History",
    "Config",
    "Banking",
]

DOMAIN_DIRS: List[str] = [
    "Needs_Action/personal",
    "Needs_Action/business",
    "Plans/personal",
    "Plans/business",
    "Pending_Approval/personal",
    "Pending_Approval/business",
    "Approved/personal",
    "Approved/business",
    "Rejected/personal",
    "Rejected/business",
]

AGENT_OWNERSHIP_DIRS: List[str] = [
    "In_Progress/local-agent-001",
    "In_Progress/cloud-agent-001",
]


def _default_dashboard() -> str:
    return (
        "# AI Employee Dashboard\n\n"
        f"**Last Updated**: {_utc_now_iso()}\n\n"
        "## System Status\n"
        "- local orchestrator: unknown\n"
        "- cloud orchestrator: unknown\n\n"
        "## Pending Actions\n"
        "Count: 0\n\n"
        "## Recent Activity\n"
        "- No activity yet\n\n"
        "## Signals\n"
        "- No signals yet\n\n"
        "## Errors\n"
        "- None\n"
    )


def _default_handbook() -> str:
    return (
        "# Company Handbook\n\n"
        f"last_updated: {_utc_now_iso()}\n\n"
        "## Communication Rules\n"
        "- Be concise and polite\n"
        "- Ask for human approval for sensitive actions\n\n"
        "## HITL Rules\n"
        "- Payments always require approval\n"
        "- Bulk social/email requires approval\n"
        "- New contacts require approval\n\n"
        "## Safety\n"
        "- Use DRY_RUN during development\n"
        "- Log every action to Logs/YYYY-MM-DD.json\n"
    )


def _default_business_goals() -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    return (
        "---\n"
        f"last_updated: {today}\n"
        "review_frequency: weekly\n"
        "schema: business_goals_v1\n"
        "---\n\n"
        "# Business_Goals\n\n"
        "## Q1 2026 Objectives\n\n"
        "### Revenue Target\n"
        "- Monthly goal: $10,000\n"
        "- Current MTD: $0\n\n"
        "### Key Metrics to Track\n"
        "| Metric | Target | Alert Threshold |\n"
        "|--------|--------|-----------------|\n"
        "| Client response time | < 24 hours | > 48 hours |\n"
        "| Invoice payment rate | > 90% | < 80% |\n"
        "| Software costs | < $500/month | > $600/month |\n\n"
        "### Active Projects\n"
        "1. AI Employee Hackathon - Due 2026-02-28 - Budget $0\n"
        "2. Client Onboarding - Due 2026-03-15 - Budget $0\n\n"
        "### Subscription Audit Rules\n"
        "Flag for review if:\n"
        "- No login in 30 days\n"
        "- Cost increased > 20%\n"
        "- Duplicate functionality with another tool\n"
    )


def _default_readme() -> str:
    return (
        "# AI Employee Vault\n\n"
        "Local-first state machine folders for autonomous FTE operation.\n\n"
        "## Core Queues\n"
        "- Inbox\n"
        "- Needs_Action/<domain>\n"
        "- In_Progress/<agent>\n"
        "- Plans/<domain>\n"
        "- Pending_Approval/<domain>\n"
        "- Approved/<domain>\n"
        "- Rejected/<domain>\n"
        "- Done\n\n"
        "## Runtime\n"
        "- Logs\n"
        "- Signals\n"
        "- Alerts\n"
        "- Recovery_Queue\n"
    )


def _default_vault_gitignore() -> str:
    return (
        "# Vault-local runtime files\n"
        "Logs/*.json\n"
        "Logs/*.log\n"
        "Signals/*\n"
        "Ralph_State/*\n"
        "Recovery_Queue/*\n"
        "Quarantine/*\n"
        "Alerts/*\n"
        "Inbox/*\n"
        "Needs_Action/*\n"
        "Plans/*\n"
        "Pending_Approval/*\n"
        "Approved/*\n"
        "Rejected/*\n"
        "Done/*\n"
        "!**/.gitkeep\n"
    )


def _write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.write_text(content, encoding="utf-8")


def create_vault(vault_path: Path, force: bool = False, dry_run: bool = False) -> int:
    all_dirs = BASE_DIRS + DOMAIN_DIRS + AGENT_OWNERSHIP_DIRS

    if dry_run:
        print(f"[DRY RUN] Would create/update vault at: {vault_path}")
        for rel in all_dirs:
            print(f"  - dir: {rel}")
        print("  - files: Dashboard.md, Company_Handbook.md, Business_Goals.md, README.md, .gitignore")
        return 0

    vault_path.mkdir(parents=True, exist_ok=True)
    for rel in all_dirs:
        (vault_path / rel).mkdir(parents=True, exist_ok=True)

    # Keep empty folders in git.
    for rel in all_dirs:
        gitkeep = vault_path / rel / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")

    _write_file(vault_path / "Dashboard.md", _default_dashboard(), force)
    _write_file(vault_path / "Company_Handbook.md", _default_handbook(), force)
    _write_file(vault_path / "Business_Goals.md", _default_business_goals(), force)
    _write_file(vault_path / "README.md", _default_readme(), force)
    _write_file(vault_path / ".gitignore", _default_vault_gitignore(), force)

    schedules_path = vault_path / "Config" / "schedules.json"
    if force or not schedules_path.exists():
        schedules_payload = {
            "schedules": [
                {
                    "id": "weekly-ceo-briefing",
                    "cmd": "RUN_CEO_BRIEFING.bat",
                    "schedule": "weekly@sun@23:00",
                    "enabled": True,
                },
                {
                    "id": "daily-linkedin-autopost-action",
                    "cmd": "RUN_LINKEDIN_AUTOPOST_ACTION.bat",
                    "schedule": "daily@09:00",
                    "enabled": True,
                },
            ]
        }
        schedules_path.write_text(json.dumps(schedules_payload, indent=2), encoding="utf-8")

    limits_path = vault_path / "Config" / "rate_limits.json"
    if force or not limits_path.exists():
        rate_limits = {
            "send_email": {"window_start": "", "count": 0},
            "twitter_post": {"window_start": "", "count": 0},
            "linkedin_post": {"window_start": "", "count": 0},
            "facebook_post": {"window_start": "", "count": 0},
            "instagram_post": {"window_start": "", "count": 0},
            "odoo_post_invoice": {"window_start": "", "count": 0},
        }
        limits_path.write_text(json.dumps(rate_limits, indent=2), encoding="utf-8")

    logger.log_action(
        action_type="setup_vault",
        result="success",
        target=str(vault_path),
        details={"force": force},
        approval_status="not_required",
    )
    print(f"Vault ready: {vault_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize AI Employee Vault")
    parser.add_argument("--vault-path", default="AI_Employee_Vault")
    parser.add_argument("--force", action="store_true", help="Overwrite managed template files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    args = parser.parse_args()

    return create_vault(Path(args.vault_path), force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
