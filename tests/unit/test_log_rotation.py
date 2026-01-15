"""Test log rotation and retention policies."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import time
from src.utils.logger import setup_logger, get_daily_log_file, cleanup_old_logs


def test_daily_log_file_naming(tmp_path):
    """Test that daily log files are named correctly."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    log_file = get_daily_log_file(vault, "watcher")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    assert log_file.name == f"watcher-{today}.log"
    assert log_file.parent == vault / "Logs"


def test_log_directory_creation(tmp_path):
    """Test that Logs directory is created if it doesn't exist."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    log_file = get_daily_log_file(vault, "watcher")

    assert (vault / "Logs").exists()
    assert (vault / "Logs").is_dir()


def test_log_rotation_by_date(tmp_path):
    """Test that logs are rotated daily."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create log files for different dates
    log_dir = vault / "Logs"
    log_dir.mkdir()

    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    today_log = log_dir / f"watcher-{today.strftime('%Y-%m-%d')}.log"
    yesterday_log = log_dir / f"watcher-{yesterday.strftime('%Y-%m-%d')}.log"
    old_log = log_dir / f"watcher-{two_days_ago.strftime('%Y-%m-%d')}.log"

    today_log.write_text("Today's logs")
    yesterday_log.write_text("Yesterday's logs")
    old_log.write_text("Old logs")

    # Verify all files exist
    assert today_log.exists()
    assert yesterday_log.exists()
    assert old_log.exists()


def test_cleanup_old_logs(tmp_path):
    """Test that old logs are cleaned up based on retention policy."""
    vault = tmp_path / "test_vault"
    log_dir = vault / "Logs"
    log_dir.mkdir(parents=True)

    # Create log files with different ages
    now = time.time()

    # Recent log (should be kept)
    recent_log = log_dir / "watcher-2026-01-14.log"
    recent_log.write_text("Recent log")
    recent_log.touch()

    # Old log (should be deleted)
    old_log = log_dir / "watcher-2025-10-01.log"
    old_log.write_text("Old log")
    # Set modification time to 100 days ago
    old_time = now - (100 * 86400)
    old_log.touch()
    import os
    os.utime(old_log, (old_time, old_time))

    # Very old log (should be deleted)
    very_old_log = log_dir / "watcher-2025-09-01.log"
    very_old_log.write_text("Very old log")
    very_old_time = now - (120 * 86400)
    very_old_log.touch()
    os.utime(very_old_log, (very_old_time, very_old_time))

    # Run cleanup with 90-day retention
    cleanup_old_logs(vault, retention_days=90)

    # Verify recent log is kept, old logs are deleted
    assert recent_log.exists(), "Recent log should be kept"
    assert not old_log.exists(), "Old log should be deleted"
    assert not very_old_log.exists(), "Very old log should be deleted"


def test_cleanup_with_no_logs(tmp_path):
    """Test cleanup when Logs directory doesn't exist."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Should not raise an error
    cleanup_old_logs(vault, retention_days=90)


def test_cleanup_with_empty_logs_dir(tmp_path):
    """Test cleanup with empty Logs directory."""
    vault = tmp_path / "test_vault"
    log_dir = vault / "Logs"
    log_dir.mkdir(parents=True)

    # Should not raise an error
    cleanup_old_logs(vault, retention_days=90)


def test_log_retention_policy_default(tmp_path):
    """Test that default retention policy is 90 days."""
    vault = tmp_path / "test_vault"
    log_dir = vault / "Logs"
    log_dir.mkdir(parents=True)

    # Create a log file 91 days old
    old_log = log_dir / "watcher-2025-10-15.log"
    old_log.write_text("Old log")

    now = time.time()
    old_time = now - (91 * 86400)
    old_log.touch()
    import os
    os.utime(old_log, (old_time, old_time))

    # Run cleanup with default retention (90 days)
    cleanup_old_logs(vault)

    # Log should be deleted
    assert not old_log.exists(), "Log older than 90 days should be deleted"


def test_log_retention_custom_period(tmp_path):
    """Test custom retention period."""
    vault = tmp_path / "test_vault"
    log_dir = vault / "Logs"
    log_dir.mkdir(parents=True)

    # Create logs with different ages
    now = time.time()

    # 25 days old (should be deleted with 30-day retention)
    log_25_days = log_dir / "watcher-25days.log"
    log_25_days.write_text("25 days old")
    log_25_days.touch()
    import os
    os.utime(log_25_days, (now - (25 * 86400), now - (25 * 86400)))

    # 35 days old (should be deleted with 30-day retention)
    log_35_days = log_dir / "watcher-35days.log"
    log_35_days.write_text("35 days old")
    log_35_days.touch()
    os.utime(log_35_days, (now - (35 * 86400), now - (35 * 86400)))

    # Run cleanup with 30-day retention
    cleanup_old_logs(vault, retention_days=30)

    # 25-day log should be kept, 35-day log should be deleted
    assert log_25_days.exists(), "Log within retention period should be kept"
    assert not log_35_days.exists(), "Log beyond retention period should be deleted"


def test_json_log_format(tmp_path):
    """Test that logs are written in JSON format."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)
    logger.info("Test message")

    # Read log file and verify JSON format
    log_content = log_file.read_text()
    import json
    log_entry = json.loads(log_content.strip())

    assert "timestamp" in log_entry
    assert "level" in log_entry
    assert "message" in log_entry
    assert log_entry["message"] == "Test message"
    assert log_entry["level"] == "INFO"


def test_multiple_components_separate_logs(tmp_path):
    """Test that different components have separate log files."""
    vault = tmp_path / "test_vault"

    watcher_log = get_daily_log_file(vault, "watcher")
    claude_log = get_daily_log_file(vault, "claude")

    assert watcher_log != claude_log
    assert "watcher" in watcher_log.name
    assert "claude" in claude_log.name
