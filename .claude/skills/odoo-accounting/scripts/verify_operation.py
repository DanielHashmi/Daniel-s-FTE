#!/usr/bin/env python3
"""Verify Odoo Accounting skill operation and connectivity."""
import sys
import os
from pathlib import Path

try:
    import xmlrpc.client
except ImportError:
    xmlrpc = None

VAULT_ROOT = Path("AI_Employee_Vault")
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"


def check_odoo_credentials() -> bool:
    """Check if Odoo credentials are configured."""
    required = ["ODOO_URL", "ODOO_DB", "ODOO_USER", "ODOO_PASSWORD"]
    return all(os.getenv(var) for var in required)


def test_odoo_connection():
    """Test actual Odoo connection if credentials are available."""
    if not check_odoo_credentials():
        return False, "Credentials not configured"

    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USER")
    password = os.getenv("ODOO_PASSWORD")

    try:
        if xmlrpc is None:
            return False, "xmlrpc.client not available"

        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})

        if uid:
            return True, f"Authenticated as user {uid}"
        else:
            return False, "Authentication failed"

    except Exception as e:
        return False, f"Connection error: {str(e)}"


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

    # Check Odoo credentials
    has_creds = check_odoo_credentials()
    checks.append(("Odoo credentials configured", has_creds))

    # Test Odoo connection if credentials configured
    if has_creds:
        conn_ok, conn_msg = test_odoo_connection()
        checks.append(("Odoo connection", conn_ok, conn_msg))
    else:
        checks.append(("Odoo credentials", False, "Set ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD"))

    # Report results
    all_passed = True
    for item in checks:
        name = item[0]
        passed = item[1]
        message = item[2] if len(item) > 2 else ""

        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if message:
            print(f"     {message}")

        if not passed:
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    verify()
