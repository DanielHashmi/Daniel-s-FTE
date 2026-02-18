#!/usr/bin/env python3
"""Static Hackathon 0 requirements checker.

Checks presence of key implementation artifacts for Bronze->Platinum tiers.
This is a structural check (file/path/capability markers), not a runtime e2e test.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Requirement:
    tier: str
    text: str
    check: Callable[[], Tuple[bool, str]]


def exists(rel: str) -> Tuple[bool, str]:
    p = ROOT / rel
    return p.exists(), rel


def contains(rel: str, marker: str) -> Tuple[bool, str]:
    p = ROOT / rel
    if not p.exists():
        return False, f"{rel} (missing)"
    txt = p.read_text(encoding="utf-8", errors="replace")
    return marker in txt, f"{rel} contains '{marker}'"


REQS: List[Requirement] = [
    # Bronze
    Requirement("bronze", "Vault has Dashboard.md", lambda: exists("AI_Employee_Vault/Dashboard.md")),
    Requirement("bronze", "Vault has Company_Handbook.md", lambda: exists("AI_Employee_Vault/Company_Handbook.md")),
    Requirement("bronze", "At least one watcher exists", lambda: exists("src/watchers/filesystem.py")),
    Requirement("bronze", "Basic folders are managed by vault library", lambda: contains("src/lib/vault.py", "needs_action")),
    Requirement("bronze", "Skills directory exists", lambda: exists(".claude/skills")),
    # Silver
    Requirement("silver", "Gmail watcher exists", lambda: exists("src/watchers/gmail.py")),
    Requirement("silver", "WhatsApp watcher exists", lambda: exists("src/watchers/whatsapp.py")),
    Requirement("silver", "LinkedIn watcher exists", lambda: exists("src/watchers/linkedin.py")),
    Requirement("silver", "LinkedIn autopost action creator exists", lambda: exists("scripts/create_linkedin_autopost_action.py")),
    Requirement("silver", "Plan manager exists", lambda: exists("src/orchestration/plan_manager.py")),
    Requirement("silver", "Email MCP server exists", lambda: exists("mcp-servers/email-mcp/index.js")),
    Requirement("silver", "Approval manager exists", lambda: exists("src/orchestration/approval_manager.py")),
    Requirement("silver", "Scheduler skill exists", lambda: exists(".claude/skills/scheduler/scripts/main_operation.py")),
    # Gold
    Requirement("gold", "Cross-domain orchestrator skill exists", lambda: exists(".claude/skills/cross-domain-orchestrator/scripts/main_operation.py")),
    Requirement("gold", "Odoo accounting skill exists", lambda: exists(".claude/skills/odoo-accounting/scripts/main_operation.py")),
    Requirement("gold", "Social MCP server exists", lambda: exists("mcp-servers/social-mcp/index.js")),
    Requirement("gold", "CEO briefing skill exists", lambda: exists(".claude/skills/ceo-briefing/scripts/main_operation.py")),
    Requirement("gold", "Error recovery skill exists", lambda: exists(".claude/skills/error-recovery/scripts/main_operation.py")),
    Requirement("gold", "Ralph loop skill exists", lambda: exists(".claude/skills/ralph-wiggum-loop/scripts/main_operation.py")),
    Requirement("gold", "Architecture doc exists", lambda: exists("docs/architecture.md")),
    Requirement("gold", "Lessons learned doc exists", lambda: exists("docs/lessons-learned.md")),
    # Platinum
    Requirement("platinum", "Role specialization exists", lambda: contains("src/orchestration/orchestrator.py", "AGENT_ROLE")),
    Requirement("platinum", "Claim-by-move exists", lambda: contains("src/orchestration/orchestrator.py", "In_Progress")),
    Requirement("platinum", "Signals merge exists", lambda: contains("src/orchestration/orchestrator.py", "signals")),
    Requirement("platinum", "Cloud PM2 config exists", lambda: exists("deployment/cloud/ecosystem.config.js")),
    Requirement("platinum", "Cloud Odoo compose exists", lambda: exists("deployment/cloud/docker-compose.odoo.yml")),
    Requirement("platinum", "Cloud Odoo TLS config exists", lambda: exists("deployment/cloud/config/Caddyfile")),
    Requirement("platinum", "Cloud health check exists", lambda: exists("deployment/cloud/healthcheck_odoo.sh")),
    Requirement("platinum", "Platinum gate script exists", lambda: exists("scripts/platinum_demo_gate.py")),
]


def main() -> int:
    grouped = {"bronze": [], "silver": [], "gold": [], "platinum": []}
    for req in REQS:
        ok, detail = req.check()
        grouped[req.tier].append((ok, req.text, detail))

    overall_ok = True
    for tier in ("bronze", "silver", "gold", "platinum"):
        rows = grouped[tier]
        passed = sum(1 for ok, _, _ in rows if ok)
        total = len(rows)
        print(f"\n[{tier.upper()}] {passed}/{total}")
        for ok, text, detail in rows:
            mark = "PASS" if ok else "FAIL"
            print(f"- {mark}: {text} ({detail})")
            if not ok:
                overall_ok = False

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
