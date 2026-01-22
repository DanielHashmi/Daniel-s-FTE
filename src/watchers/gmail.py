"""
Gmail Watcher.

Monitors Gmail for urgent or relevant emails and creates Action Files.
Uses the Gmail API via google-api-python-client.
"""

import os
import time
from typing import List, Dict, Any
from .base import BaseWatcher
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailWatcher(BaseWatcher):
    def __init__(self, interval: int = 60):
        super().__init__("gmail_watcher", interval)
        self.service = None
        self.creds = None

        # Load credentials safely (this logic would be extended in production)
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API."""
        # For this implementation, we'll setup the service if credentials exist.
        # Handling the full OAuth flow autonomously is complex and might require initial human setup.
        # We assume token.json or credentials.json exists in a safe location (e.g., config/ or root)
        # Note: In a real "AI Employee", the initial auth is a one-time human setup step.

        token_path = 'gmail_token.json'
        credentials_path = 'credentials.json'

        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Refresh if expired
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
            except Exception as e:
                self.logger.error(f"Failed to refresh Gmail token: {e}")
                self.creds = None

        # If no valid credentials, run OAuth flow
        if not self.creds and os.path.exists(credentials_path):
            try:
                self.logger.info("Starting OAuth flow for Gmail authentication...")
                self.logger.info("NOTE: If running on WSL/Headless, follow the link in console.")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                # Fix for WSL/Headless hang: don't try to open browser automatically
                self.creds = flow.run_local_server(port=0, open_browser=False)

                # Save the credentials for future runs
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())
                self.logger.info(f"Gmail token saved to {token_path}")
            except Exception as e:
                self.logger.error(f"Failed to complete OAuth flow: {e}")
                self.creds = None

        if self.creds:
            try:
                self.service = build('gmail', 'v1', credentials=self.creds)
                self.logger.info("Gmail service initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to build Gmail service: {e}")
                self.service = None
        else:
             self.logger.info("Gmail credentials not available. Watcher will run but cannot fetch.")

    def check_for_updates(self):
        """Check for new unread messages with specific importance."""
        if not self.service:
            # Try to re-auth? Or just log warning once?
            # self.logger.warning("Gmail service not active.")
            return

        try:
            # Query: unread and (important or starred) - simplest heuristic for "urgent"
            # Adjust query based on needs
            query = 'is:unread is:important'

            results = self.service.users().messages().list(userId='me', q=query, maxResults=5).execute()
            messages = results.get('messages', [])

            if messages:
                self.logger.info(f"Found {len(messages)} new important emails.")

                for msg in messages:
                    self.process_message(msg['id'])

        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")

    def process_message(self, msg_id: str):
        """Fetch full message details and create action file."""
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id).execute()

            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(no subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '(unknown)')
            snippet = message.get('snippet', '')

            # Create Action File
            metadata = {
                "sender": sender,
                "subject": subject,
                "thread_id": message['threadId'],
                "msg_id": msg_id
            }

            content = f"# Incoming Email\n\n**From:** {sender}\n**Subject:** {subject}\n\n## Snippet\n{snippet}\n"

            filename = self.create_action_file(
                type="email",
                content=content,
                metadata=metadata,
                priority="urgent" # Because we queried for 'important'
            )

            # Mark as read so we don't process again?
            # Or store processed IDs in a local DB/file to avoid duplicate processing without modifying server state?
            # For safety, let's NOT modify server state (mark read) in this MVP phase, tracking state locally is safer.
            # However, for simplicity of this code, we'll assume the Orchestrator/Plan will handle the "Mark Read" action later.
            # To prevent loops in this watcher, we should cache processed IDs.
            # TODO: Implement deduping.

        except Exception as e:
            self.logger.error(f"Error processing message {msg_id}: {e}")

if __name__ == "__main__":
    # Test run
    watcher = GmailWatcher(interval=10)
    watcher.start()
