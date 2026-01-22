#!/usr/bin/env python3
"""Verify Error Recovery skill operation."""
import sys
from pathlib import Path

VAULT_ROOT = Path("AI_Employee_Vault")
RECOVERY_QUEUE = VAULT_ROOT / "Recovery_Queue"
QUARANTINE = VAULT_ROOT / "Quarantine"
ALERTS = VAULT_ROOT / "Alerts"

def verify():
    checks = []

    # Check directories exist
    checks.append(("Recovery Queue directory", RECOVERY_QUEUE.exists()))
    checks.append(("Quarantine directory", QUARANTINE.exists()))
    checks.append(("Alerts directory", ALERTS.exists()))

    # Report results
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    # Show queue status
    queue_files = list(RECOVERY_QUEUE.glob("*.json")) if RECOVERY_QUEUE.exists() else []
    quarantine_files = list(QUARANTINE.glob("*")) if QUARANTINE.exists() else []
    alert_files = list(ALERTS.glob("*.md")) if ALERTS.exists() else []

    print(f"\nPending in queue: {len(queue_files)}")
    print(f"Quarantined files: {len(quarantine_files)}")
    print(f"Active alerts: {len(alert_files)}")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    verify()
