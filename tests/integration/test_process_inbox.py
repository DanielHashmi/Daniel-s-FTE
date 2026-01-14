"""Integration test for process_inbox skill."""

import pytest
from pathlib import Path
import sys
import subprocess


def test_process_inbox_no_vault(tmp_path):
    """Test process_inbox with non-existent vault."""
    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(tmp_path / "nonexistent"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Vault not found" in result.stdout


def test_process_inbox_empty_needs_action(tmp_path):
    """Test process_inbox with empty Needs_Action folder."""
    vault = tmp_path / "test_vault"
    needs_action = vault / "Needs_Action"
    needs_action.mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(vault),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No pending actions" in result.stdout


def test_process_inbox_with_action_files(tmp_path):
    """Test process_inbox with action files present."""
    vault = tmp_path / "test_vault"
    needs_action = vault / "Needs_Action"
    needs_action.mkdir(parents=True)

    # Create test action files
    (needs_action / "EMAIL_gmail_2026-01-14T10-30-00.md").write_text(
        """---
type: email
source: gmail
timestamp: 2026-01-14T10:30:00Z
priority: high
status: pending
created_by: watcher
---

## Content

Test email content
"""
    )

    (needs_action / "FILE_inbox_2026-01-14T09-15-00.md").write_text(
        """---
type: file
source: inbox
timestamp: 2026-01-14T09:15:00Z
priority: medium
status: pending
created_by: watcher
---

## Content

Test file content
"""
    )

    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(vault),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Found 2 action files" in result.stdout


def test_process_inbox_priority_filter(tmp_path):
    """Test process_inbox with priority filter."""
    vault = tmp_path / "test_vault"
    needs_action = vault / "Needs_Action"
    needs_action.mkdir(parents=True)

    # Create action files with different priorities
    (needs_action / "high_priority_task.md").write_text("---\npriority: high\n---\n")
    (needs_action / "low_priority_task.md").write_text("---\npriority: low\n---\n")

    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(vault),
            "--priority",
            "high",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Priority filter: high" in result.stdout


def test_process_inbox_max_files_limit(tmp_path):
    """Test process_inbox with max files limit."""
    vault = tmp_path / "test_vault"
    needs_action = vault / "Needs_Action"
    needs_action.mkdir(parents=True)

    # Create multiple action files
    for i in range(5):
        (needs_action / f"task_{i}.md").write_text(f"---\npriority: medium\n---\nTask {i}")

    result = subprocess.run(
        [
            sys.executable,
            ".claude/skills/process-inbox/scripts/main_operation.py",
            "--vault-path",
            str(vault),
            "--max-files",
            "2",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Should only process 2 files, with 3 remaining
    assert "Remaining: 3" in result.stdout
