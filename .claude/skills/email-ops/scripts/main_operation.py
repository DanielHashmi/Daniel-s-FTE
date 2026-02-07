#!/usr/bin/env python3
import argparse
import sys
import json
import os
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
LOGS_DIR = VAULT_ROOT / "Logs"
DRY_RUN_LOG = LOGS_DIR / "Email_Dry_Run.log"
SENT_LOG = LOGS_DIR / "Email_Sent.log"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"

def setup_dirs():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def audit_log(action, target, status, details=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "message": f"Email {action} to {target}: {status}",
        "logger": "email_ops_skill",
        "action_type": "email_op",
        "sub_action": action,
        "target": target,
        "result": status,
        "details": details or {}
    }

    try:
        # Append to JSON log file (one entry per line)
        with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception as e:
        # Silently fail on audit log errors
        pass

def send_email(to, subject, body, attachment=None):
    # Check if we have credentials or force dry run
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [DRY RUN] To: {to} | Subject: {subject} | Attachment: {attachment}\n"
        with open(DRY_RUN_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print(f"[OK] Email logged (DRY RUN) to {to}")
        audit_log("send", to, "success (dry_run)", {"subject": subject, "attachment": str(attachment)})
        return True

    # Real sending via official Gmail API
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        token_path = 'gmail_token.json'

        if not os.path.exists(token_path):
            print("[ERROR] gmail_token.json not found")
            print("[INFO] Run gmail watcher first to authenticate")
            return False

        # Load credentials
        creds = Credentials.from_authorized_user_file(token_path, [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send'
        ])

        # Check if we have send scope
        if 'https://www.googleapis.com/auth/gmail.send' not in (creds.scopes or []):
            print("[ERROR] Missing gmail.send scope")
            print("[INFO] Run: python src/utils/gmail_auth_setup.py")
            print("[INFO] This adds send permission (safe, uses official Google OAuth)")
            return False

        # Refresh token if needed
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)

        # Create message following Gmail API official format
        message = MIMEMultipart()
        message['To'] = to
        message['Subject'] = subject
        msg_body = MIMEText(body, 'plain')
        message.attach(msg_body)

        # Encode as required by Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send via official Gmail API method
        print(f"[INFO] Sending via Gmail API to {to}...")
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        # Success!
        msg_id = result['id']
        print(f"[OK] Email sent to {to} (ID: {msg_id})")

        # Log successful send
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [SENT] To: {to} | Subject: {subject} | ID: {msg_id}\n"
        with open(SENT_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        audit_log("send", to, "success", {"subject": subject, "method": "gmail_api", "message_id": msg_id})
        return True

    except HttpError as error:
        if error.resp.status == 403:
            print(f"[ERROR] Permission denied: {error}")
            print("[INFO] You need to add gmail.send scope")
            print("[INFO] Run: python src/utils/gmail_auth_setup.py")
        else:
            print(f"[ERROR] Gmail API error: {error}")
        return False

    except Exception as e:
        print(f"[ERROR] Failed to send: {e}")
        return False

def list_sent(limit):
    if not DRY_RUN_LOG.exists():
        print("No sent emails found.")
        return

    print(f"Recent sent emails (from {DRY_RUN_LOG}):")
    print("-" * 60)

    with open(DRY_RUN_LOG, 'r') as f:
        lines = f.readlines()

    for line in lines[-limit:]:
        print(line.strip())

def main():
    parser = argparse.ArgumentParser(description="Email operations")
    parser.add_argument("--action", required=True, choices=["send", "list-sent", "status"])
    parser.add_argument("--to", help="Recipient email")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body", help="Email body")
    parser.add_argument("--attachment", help="Path to attachment")
    parser.add_argument("--limit", type=int, default=5, help="Limit for list-sent")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "send":
        if not all([args.to, args.subject, args.body]):
            print("Error: --to, --subject, and --body required for send")
            sys.exit(1)
        if not send_email(args.to, args.subject, args.body, args.attachment):
            sys.exit(1)

    elif args.action == "list-sent":
        list_sent(args.limit)

    elif args.action == "status":
        print("✓ Email Ops ready (DRY RUN mode active)")

if __name__ == "__main__":
    main()
