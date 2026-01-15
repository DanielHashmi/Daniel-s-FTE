"""Integration tests for FileSystemWatcher."""

import pytest
from pathlib import Path
import time


def test_filesystem_watcher_detects_file(temp_vault):
    """Test that FileSystemWatcher detects new files in Inbox."""
    from src.watchers.filesystem_watcher import FileSystemWatcher

    watcher = FileSystemWatcher(temp_vault, check_interval=1)

    # Create a test file in Inbox
    inbox = temp_vault / "Inbox"
    test_file = inbox / "test_urgent.txt"
    test_file.write_text("Urgent: Test content")

    # Trigger file detection
    time.sleep(0.2)  # Wait for file to be fully written

    # Check for updates
    items = watcher.check_for_updates()

    assert len(items) > 0
    assert items[0]["type"] == "file"
    assert items[0]["source"] == "inbox"
    assert items[0]["priority"] == "high"  # Should detect "urgent" keyword


def test_filesystem_watcher_creates_action_file(temp_vault, sample_file_item):
    """Test that FileSystemWatcher creates action files correctly."""
    from src.watchers.filesystem_watcher import FileSystemWatcher

    watcher = FileSystemWatcher(temp_vault, check_interval=1)

    # Create action file
    action_file = watcher.create_action_file(sample_file_item)

    assert action_file.exists()
    assert action_file.parent == temp_vault / "Needs_Action"

    # Verify content
    content = action_file.read_text()
    assert "---" in content  # Has frontmatter
    assert "type: file" in content
    assert "source: inbox" in content


def test_filesystem_watcher_ignores_unsupported_files(temp_vault):
    """Test that FileSystemWatcher ignores unsupported file types."""
    from src.watchers.filesystem_watcher import FileSystemWatcher

    watcher = FileSystemWatcher(temp_vault, check_interval=1)

    # Create unsupported file
    inbox = temp_vault / "Inbox"
    test_file = inbox / "test.exe"
    test_file.write_text("Binary content")

    time.sleep(0.2)

    # Should not detect .exe files
    items = watcher.check_for_updates()
    assert len(items) == 0
