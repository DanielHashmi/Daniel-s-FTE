#!/usr/bin/env python3
"""Verify Audit Logger skill operation."""
import sys
from pathlib import Path

VAULT_ROOT = Path("AI_Employee_Vault")
LOGS_DIR = VAULT_ROOT / "Logs"
ARCHIVE_DIR = LOGS_DIR / "Archive"

def verify():
    checks = []

    # Check directories exist
    checks.append(("Logs directory", LOGS_DIR.exists()))
    checks.append(("Archive directory", ARCHIVE_DIR.exists()))

    # Check for log files
    log_files = list(LOGS_DIR.glob("*.json"))
    checks.append(("Log files exist", len(log_files) > 0))

    # Report results
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    # Count logs
    archived = list(ARCHIVE_DIR.glob("*.gz")) if ARCHIVE_DIR.exists() else []
    print(f"\nActive log files: {len(log_files)}")
    print(f"Archived files: {len(archived)}")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    verify()
