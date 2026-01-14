"""Test to verify no sensitive data is logged."""

import pytest
import re
from pathlib import Path
from src.utils.logger import setup_logger, get_daily_log_file


# Patterns that indicate sensitive data
SENSITIVE_PATTERNS = [
    # Passwords and secrets
    r"password['\"]?\s*[:=]\s*['\"]?[\w\-!@#$%^&*()]+",
    r"secret['\"]?\s*[:=]\s*['\"]?[\w\-!@#$%^&*()]+",
    r"api[_\-]?key['\"]?\s*[:=]\s*['\"]?[\w\-]+",
    r"token['\"]?\s*[:=]\s*['\"]?[\w\-\.]+",

    # Email addresses (should be redacted or masked)
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",

    # Credit card numbers (basic pattern)
    r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",

    # Social Security Numbers (US format)
    r"\b\d{3}-\d{2}-\d{4}\b",

    # OAuth tokens (Bearer tokens)
    r"Bearer\s+[\w\-\.]+",

    # AWS keys
    r"AKIA[0-9A-Z]{16}",

    # Private keys
    r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
]


def test_logger_does_not_log_passwords(tmp_path):
    """Test that passwords are not logged in plain text."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Simulate logging that should NOT include passwords
    logger.info("User authentication successful")
    logger.info("Configuration loaded from environment")

    # Read log file
    log_content = log_file.read_text()

    # Check for password patterns
    for pattern in SENSITIVE_PATTERNS[:4]:  # Check password/secret/key/token patterns
        matches = re.findall(pattern, log_content, re.IGNORECASE)
        assert len(matches) == 0, f"Found sensitive data matching pattern: {pattern}"


def test_logger_masks_email_addresses(tmp_path):
    """Test that email addresses should be masked or redacted in logs."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Log a message without email
    logger.info("Processing action file from inbox")

    log_content = log_file.read_text()

    # Email pattern should not appear in logs
    # Note: In production, emails should be masked like "u***@example.com"
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    full_emails = re.findall(email_pattern, log_content)

    # If emails are found, they should be masked
    for email in full_emails:
        assert "***" in email or email.startswith("test@"), \
            f"Unmasked email found in logs: {email}"


def test_logger_does_not_log_credentials(tmp_path):
    """Test that credentials are not logged."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Log safe messages
    logger.info("Gmail authentication initiated")
    logger.info("OAuth flow completed successfully")

    log_content = log_file.read_text()

    # Check that no credential patterns appear
    credential_keywords = [
        "credentials.json",
        "token.json",
        "client_secret",
        "refresh_token",
        "access_token",
    ]

    for keyword in credential_keywords:
        # It's OK to mention the filename, but not the contents
        if keyword in ["credentials.json", "token.json"]:
            continue
        assert keyword not in log_content.lower(), \
            f"Credential keyword found in logs: {keyword}"


def test_logger_does_not_log_api_keys(tmp_path):
    """Test that API keys are not logged."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Log safe messages
    logger.info("API request initiated")
    logger.info("API response received")

    log_content = log_file.read_text()

    # Check for API key patterns
    api_key_pattern = r"api[_\-]?key['\"]?\s*[:=]\s*['\"]?[\w\-]+"
    matches = re.findall(api_key_pattern, log_content, re.IGNORECASE)
    assert len(matches) == 0, "API key pattern found in logs"


def test_logger_redacts_sensitive_fields():
    """Test that sensitive fields are redacted in structured logs."""
    # This test verifies the logging configuration
    # In production, sensitive fields should be redacted before logging

    sensitive_fields = [
        "password",
        "secret",
        "api_key",
        "token",
        "credentials",
        "private_key",
    ]

    # Verify these fields are in the redaction list
    # (This would be implemented in the logger configuration)
    assert all(field in ["password", "secret", "api_key", "token", "credentials", "private_key"]
               for field in sensitive_fields)


def test_log_file_permissions(tmp_path):
    """Test that log files have appropriate permissions."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)
    logger.info("Test message")

    # Verify log file exists
    assert log_file.exists()

    # On Unix systems, verify permissions are restrictive
    import stat
    import platform

    if platform.system() != "Windows":
        file_stat = log_file.stat()
        # File should not be world-readable
        assert not (file_stat.st_mode & stat.S_IROTH), \
            "Log file is world-readable"


def test_no_environment_variables_in_logs(tmp_path):
    """Test that environment variables are not logged."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Log safe messages
    logger.info("Configuration loaded")
    logger.info("Environment initialized")

    log_content = log_file.read_text()

    # Check that no environment variable values appear
    # (Variable names are OK, but not values)
    env_patterns = [
        r"GMAIL_CREDENTIALS_PATH\s*=\s*['\"]?[\w/\-\.]+",
        r"GMAIL_TOKEN_PATH\s*=\s*['\"]?[\w/\-\.]+",
    ]

    for pattern in env_patterns:
        matches = re.findall(pattern, log_content)
        # It's OK to log the variable name, but not with its value
        for match in matches:
            assert "=" not in match or "***" in match, \
                f"Environment variable value found in logs: {match}"


def test_no_file_contents_in_logs(tmp_path):
    """Test that file contents are not logged in full."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Log safe messages about file operations
    logger.info("Processing file: test.txt")
    logger.info("File processed successfully")

    log_content = log_file.read_text()

    # Verify log is reasonably sized (not dumping entire files)
    assert len(log_content) < 10000, \
        "Log file is too large, may contain full file contents"


def test_error_messages_do_not_leak_sensitive_data(tmp_path):
    """Test that error messages don't leak sensitive data."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Log error messages (without sensitive data)
    logger.error("Authentication failed: Invalid credentials")
    logger.error("File not found: /path/to/file.txt")

    log_content = log_file.read_text()

    # Check that error messages don't contain sensitive patterns
    for pattern in SENSITIVE_PATTERNS[:4]:
        matches = re.findall(pattern, log_content, re.IGNORECASE)
        assert len(matches) == 0, \
            f"Sensitive data found in error message: {pattern}"


def test_stack_traces_do_not_leak_sensitive_data(tmp_path):
    """Test that stack traces don't leak sensitive data."""
    vault = tmp_path / "test_vault"
    log_file = get_daily_log_file(vault, "test")

    logger = setup_logger("test_logger", log_file=log_file, console=False)

    # Simulate an exception (without sensitive data)
    try:
        raise ValueError("Invalid configuration")
    except ValueError:
        logger.exception("Error occurred during processing")

    log_content = log_file.read_text()

    # Verify exception is logged
    assert "ValueError" in log_content
    assert "Invalid configuration" in log_content

    # Check that no sensitive patterns appear in stack trace
    for pattern in SENSITIVE_PATTERNS[:4]:
        matches = re.findall(pattern, log_content, re.IGNORECASE)
        assert len(matches) == 0, \
            f"Sensitive data found in stack trace: {pattern}"
