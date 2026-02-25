#!/usr/bin/env python3
"""cross-domain-orchestrator skill

Coordinate workflows across Personal and Business domains using existing skills.
This implementation executes real skill scripts (or prints commands in dry-run mode).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger

logger = get_logger("cross_domain_orchestrator_skill")
VAULT_ROOT = PROJECT_ROOT / "AI_Employee_Vault"

SCRIPT_PATHS = {
    "process_inbox": PROJECT_ROOT / ".claude" / "skills" / "process-inbox" / "scripts" / "main_operation.py",
    "odoo_accounting": PROJECT_ROOT / ".claude" / "skills" / "odoo-accounting" / "scripts" / "main_operation.py",
    "ceo_briefing": PROJECT_ROOT / ".claude" / "skills" / "ceo-briefing" / "scripts" / "main_operation.py",
    "social_media_suite": PROJECT_ROOT / ".claude" / "skills" / "social-media-suite" / "scripts" / "main_operation.py",
    "watcher_manager": PROJECT_ROOT / ".claude" / "skills" / "watcher-manager" / "scripts" / "main_operation.py",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_python(
    script_path: Path,
    args: List[str],
    *,
    dry_run: bool,
    env_overrides: Optional[Dict[str, str]] = None,
) -> Tuple[int, str, str]:
    cmd = [sys.executable, str(script_path), *args]
    if dry_run:
        print(f"[DRY RUN] {' '.join(cmd)}")
        return 0, "", ""

    env = dict(os.environ)
    if env_overrides:
        env.update({k: str(v) for k, v in env_overrides.items()})

    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode, result.stdout, result.stderr


def _check_paths() -> List[str]:
    missing = []
    for name, p in SCRIPT_PATHS.items():
        if not p.exists():
            missing.append(f"{name}: {p}")
    return missing


def _health_checks() -> Dict[str, Any]:
    env = os.environ
    checks: Dict[str, Any] = {
        "vault_exists": VAULT_ROOT.exists(),
        "odoo_env": bool(env.get("ODOO_URL") and env.get("ODOO_DB") and env.get("ODOO_USERNAME") and env.get("ODOO_PASSWORD")),
        "twitter_env": bool(env.get("TWITTER_API_KEY") and env.get("TWITTER_ACCESS_TOKEN")),
        "linkedin_env": bool(env.get("LINKEDIN_ACCESS_TOKEN") and env.get("LINKEDIN_AUTHOR_URN")),
        "facebook_env": bool(env.get("FACEBOOK_PAGE_TOKEN") and env.get("FACEBOOK_PAGE_ID")),
        "instagram_env": bool(env.get("INSTAGRAM_ACCESS_TOKEN") and env.get("INSTAGRAM_BUSINESS_ID")),
    }
    checks["missing_skill_scripts"] = _check_paths()
    return checks


def sync_domain(domain: str, dry_run: bool) -> bool:
    if domain not in {"personal", "business"}:
        print(f"Unknown domain: {domain}", file=sys.stderr)
        return False

    print(f"Syncing domain: {domain}")

    # Process inbox/plans for this domain role.
    agent_role = "local" if domain == "personal" else "cloud"
    agent_id = "local-agent-001" if domain == "personal" else "cloud-agent-001"

    code, _, _ = _run_python(
        SCRIPT_PATHS["process_inbox"],
        ["--agent-role", agent_role, "--agent-id", agent_id, "--max-files", "10", "--update-dashboard"],
        dry_run=dry_run,
    )
    if code != 0:
        return False

    # Domain-specific syncs.
    if domain == "business":
        # Odoo summary in draft mode (safe for cloud side).
        code, _, _ = _run_python(
            SCRIPT_PATHS["odoo_accounting"],
            ["--mode", "draft", "summary", "--limit", "50"],
            dry_run=dry_run,
        )
        if code != 0:
            return False

    logger.log_action(
        action_type="cross_domain_sync",
        result="success",
        target=domain,
        details={"agent_role": agent_role, "timestamp": _utc_now_iso()},
        approval_status="not_required",
    )
    return True


def sync_all(dry_run: bool) -> bool:
    ok_personal = sync_domain("personal", dry_run=dry_run)
    ok_business = sync_domain("business", dry_run=dry_run)
    return ok_personal and ok_business


def run_schedule(schedule: str, dry_run: bool) -> bool:
    if schedule not in {"daily", "weekly", "monthly"}:
        print(f"Unknown schedule: {schedule}", file=sys.stderr)
        return False

    print(f"Running schedule: {schedule}")
    if not sync_all(dry_run=dry_run):
        return False

    if schedule in {"weekly", "monthly"}:
        code, _, _ = _run_python(
            SCRIPT_PATHS["ceo_briefing"],
            ["--action", "generate"],
            dry_run=dry_run,
        )
        if code != 0:
            return False

    logger.log_action(
        action_type="cross_domain_schedule",
        result="success",
        target=schedule,
        details={"dry_run": dry_run},
        approval_status="not_required",
    )
    return True


def _write_pending_email_approval(params: Dict[str, Any]) -> Path:
    pending = VAULT_ROOT / "Pending_Approval" / "business"
    pending.mkdir(parents=True, exist_ok=True)
    ts = int(datetime.now(timezone.utc).timestamp())
    to = str(params.get("to") or params.get("client_email") or "")
    subject = str(params.get("subject") or "Invoice Update")
    body = str(params.get("body") or "Please find your invoice details attached.")

    filename = f"{ts}_EMAIL_cross_domain_invoice.md"
    path = pending / filename
    content = (
        "---\n"
        "type: approval_request\n"
        "action: send_email\n"
        "domain: business\n"
        f"created: {_utc_now_iso()}\n"
        "status: pending\n"
        f"to: {to}\n"
        f"subject: {subject}\n"
        "---\n\n"
        "# Email Draft\n\n"
        "## Content\n"
        f"{body}\n\n"
        "Move to `Approved/` to execute, or `Rejected/` to cancel.\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def run_workflow(workflow_name: str, params: Optional[Dict[str, Any]], dry_run: bool) -> bool:
    params = params or {}
    name = workflow_name.strip().lower()

    if name == "client-invoice-flow":
        # 1) Pull Odoo draft summary
        code, _, _ = _run_python(
            SCRIPT_PATHS["odoo_accounting"],
            ["--mode", "draft", "summary", "--limit", "25"],
            dry_run=dry_run,
        )
        if code != 0:
            return False

        # 2) Create HITL email approval draft for client communication.
        if dry_run:
            print("[DRY RUN] Would create Pending_Approval/business email draft")
        else:
            approval = _write_pending_email_approval(params)
            print(f"Created approval draft: {approval}")

    elif name == "weekly-business-audit":
        return run_schedule("weekly", dry_run=dry_run)

    elif name == "social-media-campaign":
        message = str(params.get("message") or "Weekly business update")
        code, _, _ = _run_python(
            SCRIPT_PATHS["social_media_suite"],
            ["--action", "post", "--platform", "all", "--message", message, "--domain", "business"],
            dry_run=dry_run,
        )
        if code != 0:
            return False

    else:
        print(f"Unknown workflow: {workflow_name}", file=sys.stderr)
        return False

    logger.log_action(
        action_type="cross_domain_workflow",
        result="success",
        target=name,
        details={"params": params, "dry_run": dry_run},
        approval_status="not_required",
    )
    return True


def show_map() -> bool:
    print("Cross-domain Integration Map")
    print("-" * 60)
    print("Personal domain: Gmail, WhatsApp, local approvals, final execution")
    print("Business domain: Odoo, social drafts, CEO briefing")
    print("Shared queues:")
    print("  Needs_Action/<domain> -> In_Progress/<agent> -> Plans/<domain>")
    print("  Pending_Approval/<domain> -> Approved|Rejected -> Done")
    print("Signals: Cloud writes to Signals/, Local merges into Dashboard")
    return True


def check_health() -> bool:
    checks = _health_checks()

    print("System Health")
    print("-" * 60)
    for key, value in checks.items():
        if key == "missing_skill_scripts":
            status = "ok" if not value else f"missing({len(value)})"
            print(f"{key}: {status}")
            if value:
                for item in value:
                    print(f"  - {item}")
        else:
            print(f"{key}: {'ok' if value else 'not_configured'}")

    healthy = bool(checks.get("vault_exists")) and not checks.get("missing_skill_scripts")
    logger.log_action(
        action_type="cross_domain_health",
        result="success" if healthy else "warning",
        target="system",
        details=checks,
        approval_status="not_required",
    )
    return healthy


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-domain orchestration skill")
    parser.add_argument("--action", required=True, choices=["sync-all", "sync", "run-schedule", "health", "workflow", "map"])
    parser.add_argument("--domain", choices=["personal", "business"], help="Domain for --action sync")
    parser.add_argument("--schedule", choices=["daily", "weekly", "monthly"], help="Schedule for --action run-schedule")
    parser.add_argument("--workflow", help="Workflow name for --action workflow")
    parser.add_argument("--params", help="JSON params for workflow")
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")
    args = parser.parse_args()

    dry_run = args.dry_run or (os.getenv("DRY_RUN", "true").lower() == "true")

    if args.action == "sync-all":
        return 0 if sync_all(dry_run=dry_run) else 1

    if args.action == "sync":
        if not args.domain:
            print("--domain is required for --action sync", file=sys.stderr)
            return 1
        return 0 if sync_domain(args.domain, dry_run=dry_run) else 1

    if args.action == "run-schedule":
        if not args.schedule:
            print("--schedule is required for --action run-schedule", file=sys.stderr)
            return 1
        return 0 if run_schedule(args.schedule, dry_run=dry_run) else 1

    if args.action == "health":
        return 0 if check_health() else 1

    if args.action == "workflow":
        if not args.workflow:
            print("--workflow is required for --action workflow", file=sys.stderr)
            return 1
        params: Optional[Dict[str, Any]] = None
        if args.params:
            try:
                params = json.loads(args.params)
                if not isinstance(params, dict):
                    raise ValueError("--params must decode to a JSON object")
            except Exception as exc:
                print(f"Invalid --params JSON: {exc}", file=sys.stderr)
                return 1
        return 0 if run_workflow(args.workflow, params=params, dry_run=dry_run) else 1

    if args.action == "map":
        return 0 if show_map() else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
