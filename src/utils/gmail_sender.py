"""
Gmail Sender - Official Gmail API Implementation.

Uses the official Gmail API with OAuth2 to send emails.
Follows Google's best practices to avoid any issues.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path

# Gmail API Scopes - need both readonly and send
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

class GmailSender:
    """Official Gmail API sender."""

    def __init__(self):
        self.service = None
        self.creds = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using existing token."""
        token_path = 'gmail_token.json'

        if not os.path.exists(token_path):
            print("[ERROR] gmail_token.json not found")
            return

        try:
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # Refresh if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())

                # Save refreshed token
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())

            if self.creds and self.creds.valid:
                self.service = build('gmail', 'v1', credentials=self.creds)
                print("[OK] Gmail API authenticated")
            else:
                print("[ERROR] Invalid credentials")

        except Exception as e:
            print(f"[ERROR] Authentication failed: {e}")
            print("[INFO] You need to re-authenticate with send scope")
            print("[INFO] Run: python src/utils/gmail_auth_setup.py")

    def send_email(self, to: str, subject: str, body: str, reply_to: str = None) -> bool:
        """
        Send email via Gmail API (official method).

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)
            reply_to: Optional message ID to reply to

        Returns:
            bool: True if sent successfully
        """

        if not self.service:
            print("[ERROR] Gmail service not initialized")
            return False

        try:
            # Create message
            message = MIMEMultipart()
            message['To'] = to
            message['Subject'] = subject

            # Add body
            msg_body = MIMEText(body, 'plain')
            message.attach(msg_body)

            # If this is a reply, add headers
            if reply_to:
                message['In-Reply-To'] = reply_to
                message['References'] = reply_to

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send via Gmail API
            send_message = {'raw': raw_message}
            if reply_to:
                send_message['threadId'] = reply_to

            result = self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()

            print(f"[OK] Email sent to {to} (Message ID: {result['id']})")

            # Log to file
            log_dir = Path("AI_Employee_Vault/Logs")
            log_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            log_file = log_dir / "Email_Sent.log"
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] To: {to} | Subject: {subject} | ID: {result['id']}\n"

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)

            return True

        except HttpError as error:
            print(f"[ERROR] Gmail API error: {error}")
            if error.resp.status == 403:
                print("[INFO] Permission denied - you need gmail.send scope")
                print("[INFO] Re-authenticate with: python src/utils/gmail_auth_setup.py")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to send: {e}")
            return False

    def is_available(self) -> bool:
        """Check if Gmail sending is available."""
        return self.service is not None

# Singleton
_sender_instance = None

def get_sender():
    global _sender_instance
    if _sender_instance is None:
        _sender_instance = GmailSender()
    return _sender_instance
