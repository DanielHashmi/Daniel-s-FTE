#!/usr/bin/env python3
"""setup-vault verification

Validate required Bronze->Platinum vault structure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_DIRS = [
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

REQUIRED_FILES = [
    "Dashboard.md",
    "Company_Handbook.md",
    "Business_Goals.md",
    "README.md",
]


def verify(vault_path: Path) -> bool:
    if not vault_path.exists():
        print(f"Missing vault directory: {vault_path}")
        return False

    missing_dirs = [d for d in REQUIRED_DIRS if not (vault_path / d).exists()]
    missing_files = [f for f in REQUIRED_FILES if not (vault_path / f).exists()]

    if missing_dirs:
        print("Missing directories:")
        for item in missing_dirs:
            print(f"- {item}")
    if missing_files:
        print("Missing files:")
        for item in missing_files:
            print(f"- {item}")

    ok = not missing_dirs and not missing_files
    if ok:
        print("Vault verification passed")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AI Employee Vault structure")
    parser.add_argument("--vault-path", default="AI_Employee_Vault")
    args = parser.parse_args()

    return 0 if verify(Path(args.vault_path)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
