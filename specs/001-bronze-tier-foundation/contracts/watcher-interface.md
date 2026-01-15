# Watcher Interface Contract

**Version**: 1.0.0
**Date**: 2026-01-14
**Feature**: 001-bronze-tier-foundation

## Overview

This document defines the interface contract for all Watcher implementations in the Bronze Tier Personal AI Employee system. All watchers MUST implement the `BaseWatcher` abstract class.

## Abstract Base Class

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional
import logging
import time

class BaseWatcher(ABC):
    """
    Abstract base class for all input source watchers.

    Watchers monitor external input sources (Gmail, file system, etc.)
    and create Action Files when new inputs are detected.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.

        Args:
            vault_path: Absolute path to AI_Employee_Vault
            check_interval: Seconds between checks (default: 60)

        Raises:
            ValueError: If vault_path doesn't exist
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs_dir = self.vault_path / 'Logs'
        self.check_interval = check_interval
        self.processed_ids = set()
        self.logger = self._setup_logger()

        # Validate vault structure
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
        if not self.needs_action.exists():
            raise ValueError(f"Needs_Action folder missing: {self.needs_action}")

    @abstractmethod
    def check_for_updates(self) -> List[Dict]:
        """
        Check the input source for new items.

        This method MUST:
        - Query the input source (Gmail API, file system, etc.)
        - Filter out already-processed items using self.processed_ids
        - Return list of new items with metadata

        Returns:
            List of dicts, each containing:
                - id: Unique identifier for the item
                - type: "email" | "file" | "manual"
                - source: Source identifier (e.g., "gmail", "inbox")
                - priority: "high" | "medium" | "low"
                - content: Item content or reference
                - metadata: Additional source-specific data

        Raises:
            ConnectionError: If cannot connect to input source
            AuthenticationError: If credentials are invalid
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict) -> Path:
        """
        Create an Action File in Needs_Action folder.

        This method MUST:
        - Generate unique filename: {TYPE}_{SOURCE}_{TIMESTAMP}.md
        - Create YAML frontmatter with required fields
        - Write Markdown body with content and suggested actions
        - Add item ID to self.processed_ids
        - Log the creation

        Args:
            item: Item dict from check_for_updates()

        Returns:
            Path to created action file

        Raises:
            IOError: If cannot write file
            ValueError: If item is missing required fields
        """
        pass

    def run(self):
        """
        Main loop: continuously check for updates and create action files.

        This method:
        - Runs indefinitely until interrupted
        - Calls check_for_updates() every check_interval seconds
        - Creates action files for new items
        - Handles errors gracefully without crashing
        - Logs all activities
        """
        self.logger.info(f"Starting {self.__class__.__name__}")

        while True:
            try:
                items = self.check_for_updates()

                for item in items:
                    try:
                        filepath = self.create_action_file(item)
                        self.logger.info(f"Created action file: {filepath.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to create action file: {e}")

            except Exception as e:
                self.logger.error(f"Error in check_for_updates: {e}")

            time.sleep(self.check_interval)

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for this watcher."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        # Create log file with current date
        from datetime import datetime
        log_file = self.logs_dir / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.log"

        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger
```

## Implementation Requirements

### Required Methods

1. **`check_for_updates()`**
   - MUST return list of dicts with required fields
   - MUST filter out already-processed items
   - MUST handle connection errors gracefully
   - SHOULD implement rate limiting for API calls

2. **`create_action_file(item)`**
   - MUST generate unique filename
   - MUST include valid YAML frontmatter
   - MUST write human-readable Markdown body
   - MUST add item ID to processed_ids set
   - MUST be atomic (no partial writes)

### Error Handling

Watchers MUST handle these error types:

- **ConnectionError**: Network timeout, API unavailable
  - Action: Log error, retry with exponential backoff

- **AuthenticationError**: Invalid credentials, expired token
  - Action: Log error, alert human, pause operations

- **IOError**: Cannot write file, disk full
  - Action: Log error, retry once, alert human if fails

- **ValueError**: Malformed item data
  - Action: Log warning, skip item, continue

### Logging Requirements

Watchers MUST log:
- Startup and shutdown events
- Each check_for_updates() call
- Each action file created
- All errors with stack traces
- Performance metrics (check duration, items processed)

### Performance Requirements

- Check duration MUST be < 10 seconds
- Memory usage MUST be < 50MB
- MUST detect new items within 2 minutes
- MUST handle 100+ items per check

## Example Implementations

### File System Watcher

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
from datetime import datetime

class FileSystemWatcher(BaseWatcher):
    """Watches AI_Employee_Vault/Inbox for new files."""

    def __init__(self, vault_path: str, check_interval: int = 10):
        super().__init__(vault_path, check_interval)
        self.inbox = self.vault_path / 'Inbox'

    def check_for_updates(self) -> List[Dict]:
        """Check Inbox folder for new files."""
        items = []

        for filepath in self.inbox.iterdir():
            if filepath.is_file() and filepath.suffix in ['.txt', '.md', '.pdf']:
                file_id = str(filepath)

                if file_id not in self.processed_ids:
                    items.append({
                        'id': file_id,
                        'type': 'file',
                        'source': 'inbox',
                        'priority': 'medium',
                        'content': filepath.read_text() if filepath.suffix in ['.txt', '.md'] else f"File: {filepath.name}",
                        'metadata': {
                            'filename': filepath.name,
                            'size': filepath.stat().st_size,
                            'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                        }
                    })

        return items

    def create_action_file(self, item: Dict) -> Path:
        """Create action file and move original to Needs_Action."""
        timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        filename = f"FILE_{item['source']}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Create YAML frontmatter
        frontmatter = f"""---
type: {item['type']}
source: {item['source']}
timestamp: {datetime.now().isoformat()}Z
priority: {item['priority']}
status: pending
created_by: watcher
---

## Content

{item['content']}

## File Metadata

- Original filename: {item['metadata']['filename']}
- Size: {item['metadata']['size']} bytes
- Modified: {item['metadata']['modified']}

## Suggested Actions

- [ ] Review file content
- [ ] Determine required action
- [ ] Process or archive

## Notes

File detected in Inbox folder.
"""

        filepath.write_text(frontmatter)
        self.processed_ids.add(item['id'])

        return filepath
```

### Gmail Watcher

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime

class GmailWatcher(BaseWatcher):
    """Watches Gmail for emails with priority keywords."""

    KEYWORDS = ['urgent', 'asap', 'invoice', 'payment', 'help']

    def __init__(self, vault_path: str, credentials_path: str, check_interval: int = 120):
        super().__init__(vault_path, check_interval)
        self.creds = Credentials.from_authorized_user_file(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.creds)

    def check_for_updates(self) -> List[Dict]:
        """Check Gmail for unread emails with keywords."""
        items = []

        # Build query for unread emails with keywords
        query = 'is:unread (' + ' OR '.join(self.KEYWORDS) + ')'

        results = self.service.users().messages().list(
            userId='me',
            q=query
        ).execute()

        messages = results.get('messages', [])

        for msg in messages:
            msg_id = msg['id']

            if msg_id not in self.processed_ids:
                # Get full message details
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_id
                ).execute()

                headers = {h['name']: h['value'] for h in message['payload']['headers']}

                items.append({
                    'id': msg_id,
                    'type': 'email',
                    'source': 'gmail',
                    'priority': self._determine_priority(headers.get('Subject', '')),
                    'content': message.get('snippet', ''),
                    'metadata': {
                        'from': headers.get('From', 'Unknown'),
                        'subject': headers.get('Subject', 'No Subject'),
                        'date': headers.get('Date', '')
                    }
                })

        return items

    def create_action_file(self, item: Dict) -> Path:
        """Create action file for email."""
        timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        filename = f"EMAIL_{item['source']}_{timestamp}.md"
        filepath = self.needs_action / filename

        frontmatter = f"""---
type: {item['type']}
source: {item['source']}
timestamp: {datetime.now().isoformat()}Z
priority: {item['priority']}
status: pending
created_by: watcher
---

## Email Content

**From**: {item['metadata']['from']}
**Subject**: {item['metadata']['subject']}
**Date**: {item['metadata']['date']}

{item['content']}

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing

## Notes

Email detected with priority keyword.
"""

        filepath.write_text(frontmatter)
        self.processed_ids.add(item['id'])

        # Label email as processed
        self.service.users().messages().modify(
            userId='me',
            id=item['id'],
            body={'addLabelIds': ['AI_Processed']}
        ).execute()

        return filepath

    def _determine_priority(self, subject: str) -> str:
        """Determine priority based on subject keywords."""
        subject_lower = subject.lower()

        if any(kw in subject_lower for kw in ['urgent', 'asap', 'critical']):
            return 'high'
        elif any(kw in subject_lower for kw in ['important', 'soon']):
            return 'medium'
        else:
            return 'low'
```

## Testing Contract Compliance

Watcher implementations MUST pass these tests:

```python
def test_watcher_initialization():
    """Test watcher initializes correctly."""
    watcher = ConcreteWatcher(vault_path="/path/to/vault")
    assert watcher.vault_path.exists()
    assert watcher.needs_action.exists()
    assert watcher.check_interval > 0

def test_check_for_updates_returns_list():
    """Test check_for_updates returns list of dicts."""
    watcher = ConcreteWatcher(vault_path="/path/to/vault")
    items = watcher.check_for_updates()
    assert isinstance(items, list)
    for item in items:
        assert 'id' in item
        assert 'type' in item
        assert 'source' in item

def test_create_action_file_creates_valid_file():
    """Test action file is created with valid structure."""
    watcher = ConcreteWatcher(vault_path="/path/to/vault")
    item = {
        'id': 'test-123',
        'type': 'email',
        'source': 'gmail',
        'priority': 'high',
        'content': 'Test content'
    }
    filepath = watcher.create_action_file(item)

    assert filepath.exists()
    assert filepath.suffix == '.md'
    content = filepath.read_text()
    assert '---' in content  # Has YAML frontmatter
    assert 'type: email' in content

def test_watcher_handles_errors_gracefully():
    """Test watcher continues after errors."""
    watcher = ConcreteWatcher(vault_path="/path/to/vault")
    # Simulate error condition
    # Verify watcher logs error and continues
```

## Version History

- **1.0.0** (2026-01-14): Initial interface definition
