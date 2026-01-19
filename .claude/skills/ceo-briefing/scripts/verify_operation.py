#!/usr/bin/env python3
"""Verify CEO Briefing skill operation."""
import sys
from pathlib import Path

VAULT_ROOT = Path("AI_Employee_Vault")
BRIEFINGS_DIR = VAULT_ROOT / "Briefings"

def verify():
    checks = []

    # Check directory exists
    checks.append(("Briefings directory", BRIEFINGS_DIR.exists()))

    # Check for briefing files
    briefings = list(BRIEFINGS_DIR.glob("*_Briefing.md"))
    checks.append(("Briefing files exist", len(briefings) > 0))

    # Report results
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    if briefings:
        print(f"\nLatest briefing: {briefings[-1].name}")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    verify()
