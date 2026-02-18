#!/usr/bin/env python3
"""Verify Odoo Accounting skill operation and connectivity (JSON-RPC)."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Tuple

VAULT_ROOT = Path("AI_Employee_Vault")
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"


def check_odoo_credentials() -> bool:
    required = ["ODOO_URL", "ODOO_DB", "ODOO_USERNAME", "ODOO_PASSWORD"]
    return all(os.getenv(var) for var in required)


def _jsonrpc(url: str, service: str, method: str, args: list):
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"service": service, "method": method, "args": args},
        "id": int(time.time() * 1000),
    }
    req = urllib.request.Request(
        f"{url.rstrip('/')}/jsonrpc",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw) if raw else {}
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(str(data["error"]))
    return data.get("result") if isinstance(data, dict) else None


def test_odoo_connection() -> Tuple[bool, str]:
    if not check_odoo_credentials():
        return False, "Credentials not configured"

    url = str(os.getenv("ODOO_URL") or "").strip()
    db = str(os.getenv("ODOO_DB") or "").strip()
    username = str(os.getenv("ODOO_USERNAME") or "").strip()
    password = str(os.getenv("ODOO_PASSWORD") or "").strip()

    try:
        uid = _jsonrpc(url, "common", "login", [db, username, password])
        if uid:
            return True, f"Authenticated via JSON-RPC as uid={uid}"
        return False, "Authentication failed (uid empty)"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP error: {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"Network error: {exc.reason}"
    except Exception as exc:
        return False, f"Connection error: {exc}"


def verify() -> int:
    checks = []

    checks.append(("Accounting directory", ACCOUNTING_DIR.exists(), ""))

    tx_files = list((ACCOUNTING_DIR / "transactions").glob("*/*transactions.json"))
    checks.append(("Transaction files exist", len(tx_files) > 0, f"found={len(tx_files)}"))

    summary_files = list(ACCOUNTING_DIR.glob("summary_*.md"))
    checks.append(("Summary files exist", len(summary_files) > 0, f"found={len(summary_files)}"))

    has_creds = check_odoo_credentials()
    checks.append(("Odoo credentials configured", has_creds, ""))

    if has_creds:
      ok, msg = test_odoo_connection()
      checks.append(("Odoo JSON-RPC connection", ok, msg))
    else:
      checks.append(("Odoo credentials", False, "Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD"))

    all_passed = True
    for name, passed, message in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")
        if message:
            print(f"  {message}")
        if not passed:
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(verify())
