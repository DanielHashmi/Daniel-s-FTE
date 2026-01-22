#!/usr/bin/env python3
"""Verify Cross-Domain Orchestrator skill operation."""
import sys
from pathlib import Path

VAULT_ROOT = Path("AI_Employee_Vault")
CONFIG_DIR = VAULT_ROOT / "Config"

def verify():
    checks = []

    # Check directory exists
    checks.append(("Config directory", CONFIG_DIR.exists()))

    # Check skill directories
    skill_dir = Path(".claude/skills")
    required_skills = ["odoo-accounting", "social-media-suite", "ceo-briefing"]

    for skill in required_skills:
        skill_path = skill_dir / skill / "SKILL.md"
        checks.append((f"Skill: {skill}", skill_path.exists()))

    # Report results
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    verify()
