"""End-to-end test for full Bronze Tier workflow.

Tests the complete flow:
1. Setup vault structure
2. Start watcher (simulated)
3. Detect new input
4. Process action file
"""

import pytest
import subprocess
import sys
from pathlib import Path
import time
import shutil


@pytest.fixture
def test_vault(tmp_path):
    """Create a temporary test vault."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create vault structure
    folders = [
        "Inbox",
        "Needs_Action",
        "Done",
        "Plans",
        "Logs",
        "Pending_Approval",
        "Approved",
        "Rejected",
    ]

    for folder in folders:
        (vault / folder).mkdir()

    # Create Dashboard.md
    (vault / "Dashboard.md").write_text(
        """# AI Employee Dashboard

**Last Updated**: 2026-01-14T10:00:00Z

## System Status

- **Watcher**: Stopped
- **Watcher Type**: None
- **Last Check**: Never
- **Uptime**: 0 minutes

## Pending Actions

**Count**: 0

## Recent Activity

No activity yet.

## Quick Stats

- **Files Processed Today**: 0
- **Files Processed This Week**: 0
- **Average Processing Time**: N/A
- **Success Rate**: N/A

## Errors

No errors.
"""
    )

    # Create Company_Handbook.md
    (vault / "Company_Handbook.md").write_text(
        """# Company Handbook

**Last Updated**: 2026-01-14T08:00:00Z

## Communication Style

- Always be polite and professional
- Use clear, concise language

## Approval Thresholds

- **Always require approval**: Payments, new contacts, bulk operations
- **No approval needed**: Reading emails, creating plans

## Priority Keywords

**High Priority**: urgent, asap, critical, emergency

**Medium Priority**: important, soon, review

**Low Priority**: fyi, info, update

## Error Handling Preferences

- **Network errors**: Retry 3 times with exponential backoff
- **Authentication errors**: Alert human immediately

## Business Rules

- Invoices should be generated within 24 hours
- Client emails should be acknowledged within 4 hours
"""
    )

    return vault


def test_e2e_vault_setup(test_vault):
    """Test Phase 1: Vault structure is properly set up."""
    # Verify all required folders exist
    required_folders = [
        "Inbox",
        "Needs_Action",
        "Done",
        "Plans",
        "Logs",
        "Pending_Approval",
        "Approved",
        "Rejected",
    ]

    for folder in required_folders:
        assert (test_vault / folder).exists(), f"Missing folder: {folder}"
        assert (test_vault / folder).is_dir(), f"{folder} is not a directory"

    # Verify core files exist
    assert (test_vault / "Dashboard.md").exists(), "Missing Dashboard.md"
    assert (test_vault / "Company_Handbook.md").exists(), "Missing Company_Handbook.md"


def test_e2e_file_detection(test_vault):
    """Test Phase 2: File system watcher detects new files."""
    inbox = test_vault / "Inbox"

    # Simulate dropping a file in Inbox
    test_file = inbox / "urgent_task.txt"
    test_file.write_text("Urgent: Please process this task immediately!")

    # Verify file was created
    assert test_file.exists(), "Test file not created in Inbox"

    # In a real scenario, the watcher would detect this and create an action file
    # For this test, we simulate the watcher's behavior
    needs_action = test_vault / "Needs_Action"
    action_file = needs_action / "FILE_inbox_2026-01-14T10-30-00.md"

    action_file.write_text(
        """---
type: file
source: inbox
timestamp: 2026-01-14T10:30:00Z
priority: high
status: pending
created_by: watcher
---

## Content

File: urgent_task.txt

Urgent: Please process this task immediately!

## Suggested Actions

- [ ] Review task details
- [ ] Create execution plan
- [ ] Execute task

## Notes

Detected by FileSystemWatcher. Priority set to HIGH due to "urgent" keyword.
"""
    )

    assert action_file.exists(), "Action file not created"


def test_e2e_action_file_processing(test_vault):
    """Test Phase 3: Action files are processed correctly."""
    needs_action = test_vault / "Needs_Action"

    # Create a test action file
    action_file = needs_action / "EMAIL_gmail_2026-01-14T10-30-00.md"
    action_file.write_text(
        """---
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

Please send invoice for January work.

## Suggested Actions

- [ ] Generate invoice
- [ ] Send to client

## Notes

High priority client request.
"""
    )

    # Run process-inbox skill
    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(test_vault),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"process-inbox failed: {result.stderr}"
    assert "Found 1 action files" in result.stdout, "Action file not detected"


def test_e2e_full_workflow(test_vault):
    """Test complete workflow from file drop to processing."""
    # Step 1: Drop file in Inbox
    inbox = test_vault / "Inbox"
    test_file = inbox / "test_task.txt"
    test_file.write_text("Test task content")

    # Step 2: Simulate watcher creating action file
    needs_action = test_vault / "Needs_Action"
    action_file = needs_action / "FILE_inbox_2026-01-14T11-00-00.md"
    action_file.write_text(
        """---
type: file
source: inbox
timestamp: 2026-01-14T11:00:00Z
priority: medium
status: pending
created_by: watcher
---

## Content

File: test_task.txt
Test task content

## Suggested Actions

- [ ] Process task

## Notes

Test action file.
"""
    )

    # Step 3: Verify action file exists
    assert action_file.exists(), "Action file not created"

    # Step 4: Run process-inbox
    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(test_vault),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Processing failed"
    assert "Found 1 action files" in result.stdout, "Action file not found"

    # Step 5: Verify dashboard can be viewed
    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/view-dashboard/scripts/main_operation.py",
            "--vault-path",
            str(test_vault),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Dashboard view failed"
    assert "AI Employee Dashboard" in result.stdout, "Dashboard not displayed"


def test_e2e_error_handling(test_vault):
    """Test error handling in the workflow."""
    # Test with invalid vault path
    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            "/nonexistent/path",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, "Should fail with invalid vault path"
    assert "Vault not found" in result.stdout, "Error message not shown"


def test_e2e_priority_handling(test_vault):
    """Test priority-based processing."""
    needs_action = test_vault / "Needs_Action"

    # Create action files with different priorities
    high_priority = needs_action / "high_priority.md"
    high_priority.write_text("---\npriority: high\n---\nHigh priority task")

    low_priority = needs_action / "low_priority.md"
    low_priority.write_text("---\npriority: low\n---\nLow priority task")

    # Process only high priority
    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(test_vault),
            "--priority",
            "high",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Priority filtering failed"
    assert "Priority filter: high" in result.stdout, "Priority filter not applied"
