#!/usr/bin/env python3
"""
Send email via Email MCP Server.
This is a wrapper that calls the MCP server for actual sending.
"""

import argparse
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

VAULT_ROOT = Path("AI_Employee_Vault")
LOGS_DIR = VAULT_ROOT / "Logs"
DRY_RUN_LOG = LOGS_DIR / "Email_Dry_Run.log"
SENT_LOG = LOGS_DIR / "Email_Sent.log"

def send_email_mcp(to, subject, body):
    """
    Send email via MCP server using stdio communication.
    """

    # Check if we're in dry run mode
    import os
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    if dry_run:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [DRY RUN] To: {to} | Subject: {subject}\n"
        with open(DRY_RUN_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        print(f"[OK] Email logged (DRY RUN) to {to}")
        return True

    # Real send via MCP (stdio JSON-RPC)
    try:
        # Construct MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "send_email",
                "arguments": {
                    "to": to,
                    "subject": subject,
                    "text": body
                }
            }
        }

        # Call MCP server via Node.js
        mcp_path = Path(__file__).parent.parent.parent.parent / "mcp-servers" / "email-mcp" / "index.js"

        result = subprocess.run(
            ["node", str(mcp_path)],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # MCP servers may emit multiple JSON-RPC messages; parse the last JSON object.
            response = None
            for line in reversed((result.stdout or "").splitlines()):
                candidate = line.strip()
                if candidate.startswith("{") and candidate.endswith("}"):
                    try:
                        response = json.loads(candidate)
                        break
                    except json.JSONDecodeError:
                        continue

            if response and "error" not in response:
                # Log successful send
                LOGS_DIR.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().isoformat()
                log_entry = f"[{timestamp}] [SENT] To: {to} | Subject: {subject}\n"
                with open(SENT_LOG, 'a', encoding='utf-8') as f:
                    f.write(log_entry)

                print(f"[OK] Email sent to {to}")
                return True
            else:
                err = (response or {}).get("error", "Unknown error")
                print(f"[ERROR] MCP returned error: {err}")
                return False
        else:
            print(f"[ERROR] MCP call failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to send via MCP: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send email via MCP")
    parser.add_argument("--to", required=True, help="Recipient email")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body")

    args = parser.parse_args()

    if not send_email_mcp(args.to, args.subject, args.body):
        sys.exit(1)
