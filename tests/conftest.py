"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime


@pytest.fixture
def temp_vault():
    """Create a temporary vault structure for testing."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "AI_Employee_Vault"
    vault_path.mkdir()

    # Create folder structure
    folders = [
        "Inbox",
        "Needs_Action",
        "Done",
        "Plans",
        "Logs",
        "Pending_Approval",
        "Approved",
        "Rejected"
    ]
    for folder in folders:
        (vault_path / folder).mkdir()

    # Create core files
    (vault_path / "Dashboard.md").write_text("# Dashboard\n\nTest dashboard")
    (vault_path / "Company_Handbook.md").write_text("# Handbook\n\nTest handbook")

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_action_file_content():
    """Sample action file content with valid frontmatter."""
    return """---
type: email
source: gmail
timestamp: 2026-01-14T10:30:00Z
priority: high
status: pending
created_by: watcher
---

## Content

From: client@example.com
Subject: Urgent: Invoice Request

Please send the invoice for January.

## Suggested Actions

- [ ] Generate invoice
- [ ] Send to client

## Notes

High priority client.
"""


@pytest.fixture
def sample_plan_file_content():
    """Sample plan file content with valid frontmatter."""
    return """---
plan_id: PLAN_001
action_file: EMAIL_gmail_2026-01-14T10-30-00.md
created: 2026-01-14T10:35:00Z
status: draft
priority: high
estimated_time: 15 minutes
requires_approval: false
---

## Objective

Generate and send invoice to client.

## Steps

1. [ ] Read client information
2. [ ] Calculate invoice amount
3. [ ] Generate PDF
4. [ ] Send email

## Required Approvals

None (Bronze Tier does not send emails automatically)

## Estimated Completion Time

15 minutes

## Notes

Client is high priority.
"""


@pytest.fixture
def mock_config(temp_vault):
    """Mock configuration for testing."""
    from src.config import Config

    class MockConfig(Config):
        def __init__(self, vault_path):
            self.vault_path = vault_path
            self.watcher_type = "filesystem"
            self.watcher_check_interval = 1  # Fast for testing
            self.gmail_credentials_path = None
            self.gmail_token_path = None
            self.gmail_query = "is:unread"
            self.log_level = "DEBUG"
            self.log_retention_days = 90
            self.dry_run = True
            self.max_memory_mb = 50

    return MockConfig(temp_vault)


@pytest.fixture
def sample_email_item():
    """Sample email item from Gmail watcher."""
    return {
        "id": "msg_12345",
        "type": "email",
        "source": "gmail",
        "priority": "high",
        "content": "From: test@example.com\nSubject: Test\n\nTest email content",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "suggested_actions": ["Reply to email", "Archive message"],
        "notes": "Test email"
    }


@pytest.fixture
def sample_file_item():
    """Sample file item from filesystem watcher."""
    return {
        "id": "file_test.txt",
        "type": "file",
        "source": "inbox",
        "priority": "medium",
        "content": "Test file content",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "suggested_actions": ["Process file", "Archive file"],
        "notes": "Test file from inbox"
    }
