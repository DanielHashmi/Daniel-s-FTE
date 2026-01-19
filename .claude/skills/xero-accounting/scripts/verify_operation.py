#!/usr/bin/env python3
"""Verify Xero Accounting skill operation."""
import sys
from pathlib import Path

VAULT_ROOT = Path("AI_Employee_Vault")
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"

def verify():
    checks = []

    # Check directory exists
    checks.append(("Accounting directory", ACCOUNTING_DIR.exists()))

    # Check for transaction files
    tx_files = list(ACCOUNTING_DIR.glob("transactions_*.json"))
    checks.append(("Transaction files exist", len(tx_files) > 0))

    # Check for summary files
    summary_files = list(ACCOUNTING_DIR.glob("summary_*.md"))
    checks.append(("Summary files exist", len(summary_files) > 0))

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
