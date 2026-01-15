"""Gmail watcher for monitoring email inbox."""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import os
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.watchers.base_watcher import BaseWatcher
from src.utils.retry import with_retry


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """Watcher for monitoring Gmail inbox."""

    def __init__(
        self,
        vault_path: Path,
        check_interval: int = 120,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        query: str = "is:unread (urgent OR invoice OR payment)"
    ):
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            check_interval: Seconds between checks
            credentials_path: Path to OAuth2 credentials.json
            token_path: Path to token.json (will be created on first auth)
            query: Gmail search query
        """
        super().__init__(vault_path, check_interval)

        self.credentials_path = credentials_path or os.getenv("GMAIL_CREDENTIALS_PATH")
        self.token_path = token_path or os.getenv("GMAIL_TOKEN_PATH", "token.json")
        self.query = query

        if not self.credentials_path:
            raise ValueError("Gmail credentials path not provided")

        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired Gmail token")
                creds.refresh(Request())
            else:
                self.logger.info("Starting OAuth2 flow for Gmail authentication")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            self.logger.info("Gmail authentication successful")

        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=creds)

    @with_retry(max_attempts=3, base_delay=2, exceptions=(HttpError,))
    def check_for_updates(self) -> List[Dict]:
        """
        Check Gmail inbox for new messages matching query.

        Returns:
            List of email items to process
        """
        items = []

        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=self.query,
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            for msg_ref in messages:
                msg_id = msg_ref['id']

                # Skip if already processed
                if msg_id in self.processed_ids:
                    continue

                # Get full message
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()

                # Extract message details
                item = self._parse_message(message)
                if item:
                    items.append(item)

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}", exc_info=True)
            raise

        return items

    def _parse_message(self, message: Dict) -> Optional[Dict]:
        """
        Parse Gmail message into item format.

        Args:
            message: Gmail message object

        Returns:
            Item dict or None if parsing fails
        """
        try:
            msg_id = message['id']
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            subject = headers.get('Subject', '(No Subject)')
            sender = headers.get('From', '(Unknown Sender)')
            date_str = headers.get('Date', '')

            # Get message snippet
            snippet = message.get('snippet', '')

            # Determine priority based on subject and snippet
            priority = self._determine_priority(subject, snippet)

            # Create timestamp
            timestamp = datetime.utcnow().isoformat() + "Z"

            # Build content
            content = f"From: {sender}\nSubject: {subject}\nDate: {date_str}\n\n{snippet}"

            item = {
                "id": msg_id,
                "type": "email",
                "source": "gmail",
                "priority": priority,
                "content": content,
                "timestamp": timestamp,
                "suggested_actions": [
                    "Read full email",
                    "Draft response",
                    "Mark as processed"
                ],
                "notes": f"Gmail message ID: {msg_id}"
            }

            return item

        except Exception as e:
            self.logger.error(f"Failed to parse message: {e}", exc_info=True)
            return None

    def _determine_priority(self, subject: str, snippet: str) -> str:
        """
        Determine priority based on email content.

        Args:
            subject: Email subject
            snippet: Email snippet

        Returns:
            Priority level (high, medium, low)
        """
        high_keywords = ['urgent', 'asap', 'critical', 'emergency', 'invoice', 'payment']
        medium_keywords = ['important', 'soon', 'review', 'feedback']

        text = (subject + " " + snippet).lower()

        for keyword in high_keywords:
            if keyword in text:
                return "high"

        for keyword in medium_keywords:
            if keyword in text:
                return "medium"

        return "low"

    def create_action_file(self, item: Dict) -> Path:
        """
        Create action file from email item.

        Args:
            item: Email item metadata

        Returns:
            Path to created action file
        """
        filename = self._generate_action_filename(
            item["type"],
            item["source"],
            item["timestamp"]
        )

        content = self._create_action_file_content(
            item["type"],
            item["source"],
            item["timestamp"],
            item["priority"],
            item["content"],
            item.get("suggested_actions"),
            item.get("notes")
        )

        action_file = self.needs_action / filename
        action_file.write_text(content)

        return action_file


def main():
    """Main entry point for Gmail watcher."""
    from src.config import get_config

    config = get_config()

    if config.watcher_type != "gmail":
        print("Error: WATCHER_TYPE must be 'gmail' to run Gmail watcher")
        return

    watcher = GmailWatcher(
        config.vault_path,
        config.watcher_check_interval,
        config.gmail_credentials_path,
        config.gmail_token_path,
        config.gmail_query
    )

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    main()
