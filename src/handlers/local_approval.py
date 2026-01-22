#!/usr/bin/env python3
"""
local_approval.py - Local agent approval handler for cloud-drafted emails.

This handler processes draft emails from cloud agent and handles approval.
"""

import os
import sys
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class LocalApprovalHandler:
    """Handle approval and execution of cloud-drafted emails."""

    def __init__(self, vault_path: str):
        """
        Initialize local approval handler.

        Args:
            vault_path: Path to AI_Employee_Vault
        """
        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved = self.vault_path / "Approved"
        self.rejected = self.vault_path / "Rejected"
        self.logs = self.vault_path / "Logs"
        self.sent_emails = self.vault_path / "Sent_Emails"

        # Create directories
        self.approved.mkdir(exist_ok=True)
        self.rejected.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)
        self.sent_emails.mkdir(exist_ok=True)

        self.local_agent_id = os.getenv('LOCAL_AGENT_ID', 'local-agent-001')

        # Email configuration
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
        self.email_user = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_APP_PASSWORD')

    def scan_pending_drafts(self) -> list:
        """
        Scan Pending_Approval folder for cloud drafts.

        Returns:
            List of draft file paths
        """
        if not self.pending_approval.exists():
            return []

        drafts = []
        for f in self.pending_approval.glob("*.yaml"):
            try:
                with open(f, 'r') as file:
                    content = file.read()

                # Check if it's a cloud draft
                if 'cloud_environment: true' in content or 'cloud_draft: true' in content:
                    drafts.append(f)
            except Exception as e:
                print(f"Error reading {f}: {e}")

        return drafts

    def process_draft(self, draft_file: Path, auto_approve: bool = False) -> Dict[str, Any]:
        """
        Process a draft email file.

        Args:
            draft_file: Path to draft file
            auto_approve: If True, automatically approve and send

        Returns:
            Dict with processing result
        """
        result = {
            'draft_file': str(draft_file),
            'draft_id': None,
            'recipient': None,
            'subject': None,
            'action': None,  # approved, rejected, pending
            'sent': False,
            'error': None
        }

        try:
            # Parse draft file
            with open(draft_file, 'r') as f:
                content = f.read()

            # Extract YAML frontmatter
            if '---' not in content:
                result['error'] = "Invalid format: no YAML frontmatter"
                return result

            parts = content.split('---', 2)
            if len(parts) < 3:
                result['error'] = "Invalid format: incomplete frontmatter"
                return result

            # Parse metadata
            metadata = yaml.safe_load(parts[1])
            email_body = parts[2]

            result['draft_id'] = metadata.get('draft_id')
            result['recipient'] = metadata.get('recipient')
            result['subject'] = metadata.get('subject')

            # Check if auto-approval is enabled
            if auto_approve:
                return self.approve_and_send(draft_file, metadata, email_body)

            # Manual approval required
            result['action'] = 'pending'
            print(f"\n=== DRAFT EMAIL REQUIRES APPROVAL ===")
            print(f"Draft ID: {result['draft_id']}")
            print(f"To: {result['recipient']}")
            print(f"Subject: {result['subject']}")
            print(f"\n--- Email Body ---\n{email_body}\n---\n")

            # If we have email credentials, we can send interactively
            if self._has_email_credentials():
                response = input("Approve and send? (yes/no): ").strip().lower()
                if response in ('yes', 'y'):
                    return self.approve_and_send(draft_file, metadata, email_body)
                else:
                    return self.reject_draft(draft_file)
            else:
                print("Email credentials not configured. Please add to .env file.")
                result['error'] = "Email credentials not configured"

        except Exception as e:
            result['error'] = str(e)

        return result

    def approve_and_send(self, draft_file: Path, metadata: Dict, email_body: str) -> Dict[str, Any]:
        """
        Approve and send the drafted email.

        Args:
            draft_file: Path to draft file
            metadata: Parsed metadata from draft
            email_body: Email body content

        Returns:
            Dict with sending result
        """
        result = {
            'draft_file': str(draft_file),
            'draft_id': metadata.get('draft_id'),
            'recipient': metadata.get('recipient'),
            'subject': metadata.get('subject'),
            'action': 'approved',
            'sent': False,
            'error': None
        }

        try:
            # Send email
            if self._send_email(metadata.get('recipient'), metadata.get('subject'), email_body):
                result['sent'] = True

                # Move to approved
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                approved_name = f"{timestamp}_{draft_file.name}"
                shutil.move(str(draft_file), str(self.approved / approved_name))

                # Log approval and sending
                self._log_action('email_sent', {
                    'draft_id': result['draft_id'],
                    'recipient': result['recipient'],
                    'subject': result['subject'],
                    'agent': self.local_agent_id
                })

                print(f"✓ Email sent successfully to {result['recipient']}")
                print(f"✓ Draft moved to Approved folder")

            else:
                result['error'] = "Failed to send email"

        except Exception as e:
            result['error'] = str(e)

        return result

    def reject_draft(self, draft_file: Path) -> Dict[str, Any]:
        """
        Reject a draft email.

        Args:
            draft_file: Path to draft file

        Returns:
            Dict with rejection result
        """
        result = {
            'draft_file': str(draft_file),
            'action': 'rejected',
            'error': None
        }

        try:
            # Move to rejected
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            rejected_name = f"{timestamp}_{draft_file.name}"
            shutil.move(str(draft_file), str(self.rejected / rejected_name))

            # Log rejection
            self._log_action('draft_rejected', {
                'draft_file': str(draft_file),
                'agent': self.local_agent_id
            })

            print(f"✓ Draft rejected and moved to Rejected folder")

        except Exception as e:
            result['error'] = str(e)

        return result

    def _has_email_credentials(self) -> bool:
        """Check if email credentials are configured."""
        return all([
            self.email_user,
            self.email_password,
            self.smtp_server
        ])

    def _send_email(self, recipient: str, subject: str, body: str) -> bool:
        """
        Send email via SMTP.

        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body

        Returns:
            True if successful
        """
        if not self._has_email_credentials():
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send via SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, recipient, text)
            server.quit()

            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def _log_action(self, action_type: str, data: Dict[str, Any]):
        """Log action for audit trail."""
        log_file = self.logs / f"approval_{datetime.utcnow().strftime('%Y-%m-%d')}.json"

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent': self.local_agent_id,
            'action': action_type,
            'data': data
        }

        # Append to log file
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Local approval handler for cloud drafts')
    parser.add_argument('vault_path', help='Path to AI_Employee_Vault')
    parser.add_argument('--draft', help='Process specific draft file')
    parser.add_argument('--auto', action='store_true', help='Auto-approve and send')
    parser.add_argument('--scan', action='store_true', help='Scan and list pending drafts')

    args = parser.parse_args()

    handler = LocalApprovalHandler(args.vault_path)

    if args.scan:
        drafts = handler.scan_pending_drafts()
        if drafts:
            print(f"Found {len(drafts)} pending drafts:")
            for draft in drafts:
                print(f"  - {draft.name}")
        else:
            print("No pending drafts found.")
        return

    if args.draft:
        draft_file = Path(args.draft)
        result = handler.process_draft(draft_file, auto_approve=args.auto)
        print(json.dumps(result, indent=2))
        return

    # Process all pending drafts
    drafts = handler.scan_pending_drafts()
    if not drafts:
        print("No pending drafts to process.")
        return

    print(f"Found {len(drafts)} pending drafts\n")

    for draft_file in drafts:
        print(f"\nProcessing: {draft_file.name}")
        result = handler.process_draft(draft_file, auto_approve=args.auto)

        if result.get('error'):
            print(f"ERROR: {result['error']}")
        elif result.get('sent'):
            print(f"✓ Sent to {result['recipient']}")
        else:
            print(f"Status: {result.get('action', 'unknown')}")


if __name__ == '__main__':
    main()
