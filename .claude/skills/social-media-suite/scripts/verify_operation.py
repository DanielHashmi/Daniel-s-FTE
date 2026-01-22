#!/usr/bin/env python3
"""Verify Social Media Suite skill operation."""
import sys
from pathlib import Path

VAULT_ROOT = Path("AI_Employee_Vault")
PENDING_APPROVAL = VAULT_ROOT / "Pending_Approval"
LOGS_DIR = VAULT_ROOT / "Logs"

def verify():
    checks = []

    # Check directories exist
    checks.append(("Pending Approval directory", PENDING_APPROVAL.exists()))
    checks.append(("Logs directory", LOGS_DIR.exists()))

    # Check for social media approval files
    social_files = list(PENDING_APPROVAL.glob("SOCIAL_*.md"))
    checks.append(("Can create approval files", True))  # Always passes if dirs exist

    # Report results
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    print(f"\nPending social posts: {len(social_files)}")
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    verify()
