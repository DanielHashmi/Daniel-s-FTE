"""Structured logging utilities for AI Employee system."""

import json
import logging
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string representation of log record
        """
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    console: bool = True,
) -> logging.Logger:
    """
    Set up a logger with JSON formatting.

    Args:
        name: Logger name (typically module name)
        log_file: Path to log file (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Whether to also log to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with JSON formatting
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    # Console handler with simple formatting
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def get_daily_log_file(vault_path: Path, component: str) -> Path:
    """
    Get log file path for today.

    Args:
        vault_path: Path to AI Employee Vault
        component: Component name (e.g., 'watcher', 'claude')

    Returns:
        Path to today's log file
    """
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    log_dir = vault_path / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{component}-{today}.log"


def cleanup_old_logs(vault_path: Path, retention_days: int = 90):
    """
    Remove log files older than retention period.

    Args:
        vault_path: Path to AI Employee Vault
        retention_days: Number of days to keep logs
    """
    log_dir = vault_path / "Logs"
    if not log_dir.exists():
        return

    cutoff_timestamp = datetime.now(UTC).timestamp() - (retention_days * 86400)

    for log_file in log_dir.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_timestamp:
            log_file.unlink()


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter to add extra context to log messages."""

    def process(self, msg, kwargs):
        """Add extra fields to log record."""
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["extra_fields"] = self.extra
        return msg, kwargs
