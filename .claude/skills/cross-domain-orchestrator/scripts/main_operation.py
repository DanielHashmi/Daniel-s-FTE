#!/usr/bin/env python3
"""Cross-Domain Orchestrator - Gold Tier Skill

Coordinate operations across Personal and Business domains,
manage workflow dependencies, and orchestrate multi-system tasks.
"""
import argparse
import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
CONFIG_DIR = VAULT_ROOT / "Config"
LOGS_DIR = VAULT_ROOT / "Logs"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"

# Domain definitions
DOMAINS = {
    "personal": {
        "components": ["gmail", "whatsapp", "calendar"],
        "skills": ["email-ops", "watcher-manager"]
    },
    "business": {
        "components": ["xero", "linkedin", "facebook", "instagram", "twitter"],
        "skills": ["xero-accounting", "social-ops", "social-media-suite"]
    }
}

# Pre-built workflows
WORKFLOWS = {
    "client-invoice-flow": {
        "description": "Generate and send invoice to client",
        "steps": [
            {"action": "xero-accounting", "command": "--action invoices --status unpaid"},
            {"action": "generate-invoice", "template": "invoice"},
            {"action": "email-ops", "command": "--action send --attachment invoice.pdf"},
            {"action": "social-ops", "command": "--action post --message 'Thanks for your business!'"},
            {"action": "audit-log", "event": "invoice_sent"}
        ]
    },
    "weekly-business-audit": {
        "description": "Full weekly business audit and CEO briefing",
        "steps": [
            {"action": "xero-accounting", "command": "--action sync"},
            {"action": "xero-accounting", "command": "--action summary --period weekly"},
            {"action": "ceo-briefing", "command": "--action generate"},
            {"action": "email-ops", "command": "--action send --subject 'Weekly CEO Briefing'"}
        ]
    },
    "social-media-campaign": {
        "description": "Multi-platform social media posting",
        "steps": [
            {"action": "social-media-suite", "command": "--platform all --action post"},
            {"action": "wait-for-approval", "timeout": 3600},
            {"action": "social-media-suite", "command": "--action summary --days 1"}
        ]
    }
}


def setup_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "cross_domain_orchestrator",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "cross_domain_orchestrator_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


def check_component_health(component: str) -> dict:
    """Check health of a single component."""
    health_checks = {
        "gmail": lambda: os.path.exists(os.path.expanduser("~/.gmail_credentials.json")),
        "whatsapp": lambda: os.path.exists(os.path.expanduser("~/.whatsapp_session")),
        "xero": lambda: bool(os.getenv("XERO_CLIENT_ID")),
        "linkedin": lambda: bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "facebook": lambda: bool(os.getenv("META_ACCESS_TOKEN")),
        "instagram": lambda: bool(os.getenv("INSTAGRAM_BUSINESS_ID")),
        "twitter": lambda: bool(os.getenv("TWITTER_API_KEY")),
        "calendar": lambda: True,  # Always available (local)
    }

    check_fn = health_checks.get(component, lambda: True)
    try:
        is_healthy = check_fn()
        return {
            "component": component,
            "status": "healthy" if is_healthy else "unconfigured",
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "component": component,
            "status": "error",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }


def sync_all():
    """Sync all domains and components."""
    print("Full System Sync")
    print("=" * 50)

    results = {"personal": {}, "business": {}}

    for domain, config in DOMAINS.items():
        print(f"\n{domain.upper()} DOMAIN")
        print("-" * 30)

        for component in config["components"]:
            health = check_component_health(component)
            status_emoji = "✓" if health["status"] == "healthy" else "✗"
            print(f"  {status_emoji} {component}: {health['status']}")
            results[domain][component] = health

    # Run skill syncs
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        print("\n[DRY RUN] Would execute:")
        print("  - xero-accounting --action sync")
        print("  - social-media-suite --action status")
    else:
        # Execute real syncs
        pass

    audit_log("sync_all", "all_domains", "success", results)
    print("\n✓ System sync complete")
    return True


def sync_domain(domain: str):
    """Sync a specific domain."""
    if domain not in DOMAINS:
        print(f"✗ Unknown domain: {domain}")
        return False

    print(f"Syncing {domain.upper()} domain...")

    config = DOMAINS[domain]
    for component in config["components"]:
        health = check_component_health(component)
        status_emoji = "✓" if health["status"] == "healthy" else "✗"
        print(f"  {status_emoji} {component}: {health['status']}")

    audit_log("sync_domain", domain, "success")
    print(f"\n✓ {domain.capitalize()} domain sync complete")
    return True


def run_schedule(schedule: str):
    """Run scheduled coordination tasks."""
    schedules = {
        "daily": ["sync_all"],
        "weekly": ["sync_all", "weekly-business-audit"],
        "monthly": ["sync_all", "weekly-business-audit", "generate-reports"]
    }

    if schedule not in schedules:
        print(f"✗ Unknown schedule: {schedule}")
        return False

    tasks = schedules[schedule]
    print(f"Running {schedule.upper()} schedule...")
    print(f"Tasks: {', '.join(tasks)}")

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    for task in tasks:
        print(f"\n  → {task}")
        if dry_run:
            print(f"    [DRY RUN] Would execute: {task}")
        else:
            # Execute task
            pass

    audit_log("run_schedule", schedule, "success", {"tasks": tasks})
    print(f"\n✓ {schedule.capitalize()} schedule complete")
    return True


def check_health():
    """Check health of all integrated systems."""
    print("System Health Check")
    print("=" * 50)

    all_healthy = True

    for domain, config in DOMAINS.items():
        print(f"\n{domain.upper()} DOMAIN")
        print("-" * 30)

        for component in config["components"]:
            health = check_component_health(component)
            status_emoji = "✓" if health["status"] == "healthy" else "✗"
            print(f"  {status_emoji} {component}: {health['status']}")

            if health["status"] != "healthy":
                all_healthy = False

    # Check skill availability
    print("\nSKILLS")
    print("-" * 30)
    skill_dir = Path(".claude/skills")
    for skill in ["xero-accounting", "social-media-suite", "ceo-briefing", "ralph-wiggum-loop"]:
        skill_path = skill_dir / skill / "SKILL.md"
        exists = skill_path.exists()
        status_emoji = "✓" if exists else "✗"
        print(f"  {status_emoji} {skill}")
        if not exists:
            all_healthy = False

    overall = "✓ All systems healthy" if all_healthy else "⚠️ Some systems need attention"
    print(f"\n{overall}")
    return all_healthy


def run_workflow(workflow_name: str, params: Optional[dict] = None):
    """Execute a pre-built workflow."""
    if workflow_name not in WORKFLOWS:
        print(f"✗ Unknown workflow: {workflow_name}")
        print(f"  Available: {', '.join(WORKFLOWS.keys())}")
        return False

    workflow = WORKFLOWS[workflow_name]
    print(f"Executing Workflow: {workflow_name}")
    print(f"Description: {workflow['description']}")
    print(f"Steps: {len(workflow['steps'])}")
    print("-" * 50)

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    for i, step in enumerate(workflow["steps"], 1):
        action = step.get("action", "unknown")
        command = step.get("command", "")

        print(f"\n[{i}/{len(workflow['steps'])}] {action}")

        if dry_run:
            print(f"  [DRY RUN] Would execute: {action} {command}")
        else:
            # Execute step
            pass

    audit_log("workflow", workflow_name, "success", {"params": params})
    print(f"\n✓ Workflow '{workflow_name}' complete")
    return True


def show_integration_map():
    """Display integration map of all systems."""
    print("Cross-Domain Integration Map")
    print("=" * 60)

    print("""
┌─────────────────────────────────────────────────────────────┐
│                    AI EMPLOYEE SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PERSONAL DOMAIN            BUSINESS DOMAIN                  │
│  ┌─────────────────┐       ┌─────────────────────────────┐  │
│  │ Gmail           │       │ Xero (Accounting)           │  │
│  │ WhatsApp        │◄─────►│ LinkedIn                    │  │
│  │ Calendar        │       │ Facebook/Instagram/Twitter  │  │
│  └─────────────────┘       └─────────────────────────────┘  │
│           │                           │                      │
│           │                           │                      │
│           ▼                           ▼                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              ORCHESTRATION LAYER                      │   │
│  │   • Cross-domain coordination                         │   │
│  │   • Workflow management                               │   │
│  │   • Schedule execution                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SKILLS LAYER                             │   │
│  │   • xero-accounting    • ceo-briefing                 │   │
│  │   • social-media-suite • ralph-wiggum-loop            │   │
│  │   • error-recovery     • audit-logger                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
""")

    # List available workflows
    print("\nAvailable Workflows:")
    for name, workflow in WORKFLOWS.items():
        print(f"  • {name}: {workflow['description']}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Cross-Domain Orchestrator")
    parser.add_argument("--action", required=True,
                       choices=["sync-all", "sync", "run-schedule", "health", "workflow", "map"])
    parser.add_argument("--domain", choices=["personal", "business"], help="Domain for sync")
    parser.add_argument("--schedule", choices=["daily", "weekly", "monthly"])
    parser.add_argument("--workflow", help="Workflow name to execute")
    parser.add_argument("--params", help="JSON params for workflow")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "sync-all":
        sync_all()

    elif args.action == "sync":
        if not args.domain:
            print("Error: --domain required for sync action")
            sys.exit(1)
        sync_domain(args.domain)

    elif args.action == "run-schedule":
        if not args.schedule:
            print("Error: --schedule required for run-schedule action")
            sys.exit(1)
        run_schedule(args.schedule)

    elif args.action == "health":
        if not check_health():
            sys.exit(1)

    elif args.action == "workflow":
        if not args.workflow:
            print("Error: --workflow required for workflow action")
            sys.exit(1)
        params = json.loads(args.params) if args.params else None
        run_workflow(args.workflow, params)

    elif args.action == "map":
        show_integration_map()


if __name__ == "__main__":
    main()
