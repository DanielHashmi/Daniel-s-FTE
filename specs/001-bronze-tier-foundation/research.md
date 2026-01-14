# Research: Bronze Tier - Personal AI Employee Foundation

**Date**: 2026-01-14
**Feature**: 001-bronze-tier-foundation
**Phase**: Phase 0 - Research & Technology Selection

## Overview

This document captures research findings and technology decisions for implementing the Bronze Tier foundation of the Personal AI Employee system.

## Research Areas

### 1. File System Monitoring (Python Watchdog)

**Decision**: Use `watchdog` library version 6.0+ for file system monitoring

**Rationale**:
- Industry-standard Python library for cross-platform file system event monitoring
- Supports Windows, macOS, and Linux with native OS APIs (inotify, FSEvents, ReadDirectoryChangesW)
- Event-driven architecture reduces CPU usage compared to polling
- Well-maintained with active development (v6.0.0 released recently)

**Implementation Pattern**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DropFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Handle new file detection
        pass
```

**Alternatives Considered**:
- **Polling with os.listdir()**: Rejected due to high CPU usage and 1-second minimum delay
- **inotify (Linux-only)**: Rejected due to lack of cross-platform support
- **pyinotify**: Rejected as watchdog provides better abstraction

**Best Practices**:
- Use Observer pattern with separate handler classes
- Implement debouncing for rapid file changes (wait 100ms after last event)
- Filter events by file extension to avoid processing temporary files
- Use absolute paths to avoid working directory issues

### 2. Gmail API Integration

**Decision**: Use `google-auth` 2.27+ and `google-api-python-client` 2.187+ with OAuth2 flow

**Rationale**:
- Official Google client libraries with comprehensive documentation
- OAuth2 provides secure, token-based authentication without storing passwords
- Supports incremental authorization (request only Gmail read scope)
- Token refresh handled automatically by library
- Rate limiting built into client (250 quota units per user per second limit)

**Implementation Pattern**:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load credentials from token file
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('gmail', 'v1', credentials=creds)

# Query unread emails with keywords
results = service.users().messages().list(
    userId='me',
    q='is:unread (urgent OR invoice OR payment)'
).execute()
```

**Alternatives Considered**:
- **IMAP with imaplib**: Rejected due to less secure app passwords requirement and manual OAuth complexity
- **Third-party libraries (gmail-python)**: Rejected due to lack of maintenance and limited features

**Best Practices**:
- Store credentials in OS-native secure storage (not plain text files)
- Use minimal OAuth scopes (gmail.readonly for Bronze Tier)
- Implement exponential backoff for rate limit errors (429 responses)
- Label processed emails to track state ("AI_Processed" label)
- Cache message IDs in local file to prevent duplicate processing

**Security Considerations**:
- Never commit token.json or credentials.json to version control
- Rotate OAuth tokens every 7 days (Google's refresh token expiry)
- Use service account for production deployments (not user OAuth)

### 3. YAML Frontmatter Parsing

**Decision**: Use `pyyaml` 6.0+ with custom frontmatter parser

**Rationale**:
- PyYAML is the de facto standard for YAML in Python
- Safe loading prevents code execution vulnerabilities
- Supports complex data structures (nested objects, lists)
- Fast C-based parser available (LibYAML)

**Implementation Pattern**:
```python
import yaml
import re

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from Markdown."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return frontmatter, body
```

**Alternatives Considered**:
- **python-frontmatter**: Rejected as it adds unnecessary dependency for simple parsing
- **Manual parsing**: Rejected due to edge case handling complexity

**Best Practices**:
- Always use `yaml.safe_load()` never `yaml.load()` (security)
- Validate required fields after parsing (type, source, timestamp)
- Handle malformed YAML gracefully (log warning, use defaults)
- Preserve original file if parsing fails

### 4. Claude Agent Skills Framework

**Decision**: Implement Agent Skills as Python modules with standardized interface

**Rationale**:
- Constitutional requirement (Principle III)
- Skills provide reusable, testable, documented capabilities
- Clear separation of concerns (each skill = one capability)
- Easy to invoke via command-line or programmatically

**Implementation Pattern**:
```python
# src/skills/setup_vault.py
class SetupVaultSkill:
    """Initialize AI Employee Vault structure."""

    name = "setup-vault"
    description = "Create Obsidian vault with required folders and files"

    def execute(self, vault_path: str) -> dict:
        """Execute vault setup."""
        # Create folders
        # Create Dashboard.md and Company_Handbook.md
        # Return success/failure
        return {"status": "success", "message": "Vault created"}
```

**Best Practices**:
- Each skill has: name, description, execute() method
- Return structured dict with status and message
- Raise specific exceptions for different failure modes
- Include dry-run mode for testing
- Document required inputs and expected outputs

**Skill Catalog for Bronze Tier**:
1. **setup-vault**: Initialize vault structure
2. **start-watcher**: Launch watcher process
3. **stop-watcher**: Terminate watcher process
4. **process-inbox**: Run Claude on pending actions
5. **view-dashboard**: Display current system status

### 5. Process Management for Background Watchers

**Decision**: Use PM2 (Node.js process manager) for production, manual process for development

**Rationale**:
- PM2 provides auto-restart, logging, and monitoring out of the box
- Cross-platform support (Windows, macOS, Linux)
- Simple CLI interface (`pm2 start`, `pm2 stop`, `pm2 logs`)
- Startup script generation for system boot
- Alternative: systemd (Linux-only) or launchd (macOS-only)

**Implementation Pattern**:
```bash
# Start watcher with PM2
pm2 start src/watchers/filesystem_watcher.py --interpreter python3 --name ai-watcher

# Save process list for auto-start on boot
pm2 save
pm2 startup
```

**Alternatives Considered**:
- **supervisord**: Rejected due to Python 2 legacy and complex configuration
- **systemd**: Rejected due to Linux-only limitation
- **Custom watchdog script**: Rejected as PM2 provides better features

**Best Practices**:
- Use PM2 ecosystem file for configuration (ecosystem.config.js)
- Set max memory limit (50MB) to prevent runaway processes
- Configure log rotation (max 10MB per log file)
- Use PM2 monitoring dashboard for production

### 6. Retry Patterns and Error Handling

**Decision**: Implement exponential backoff with jitter for transient errors

**Rationale**:
- Exponential backoff prevents thundering herd problem
- Jitter (random delay) prevents synchronized retries
- Industry standard pattern (AWS SDK, Google Cloud SDK)
- Balances quick recovery with API rate limit respect

**Implementation Pattern**:
```python
import time
import random
from functools import wraps

def with_retry(max_attempts=3, base_delay=1, max_delay=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    time.sleep(delay + jitter)
        return wrapper
    return decorator
```

**Error Categories**:
- **Transient**: Network timeout, API rate limit (retry with backoff)
- **Authentication**: Expired token, invalid credentials (alert human, pause)
- **Logic**: Invalid input, malformed data (log, skip, continue)
- **System**: Disk full, permission denied (alert human, attempt recovery)

**Best Practices**:
- Log each retry attempt with attempt number and delay
- Set maximum retry attempts (3 for most operations)
- Use different strategies for different error types
- Never retry destructive operations (payments, deletions)

### 7. Logging Strategy

**Decision**: Use Python `logging` module with structured JSON logs

**Rationale**:
- Built-in Python module, no external dependencies
- Supports multiple handlers (file, console, syslog)
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Thread-safe for concurrent operations

**Implementation Pattern**:
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName
        }
        return json.dumps(log_data)

# Configure logger
logger = logging.getLogger("ai_employee")
handler = logging.FileHandler("AI_Employee_Vault/Logs/watcher-2026-01-14.log")
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

**Best Practices**:
- Use structured JSON for machine-readable logs
- Include timestamp (ISO 8601), level, logger name, message
- Rotate logs daily (new file per day)
- Set log retention policy (90 days per constitution)
- Never log sensitive data (passwords, API keys, email content)

### 8. Configuration Management

**Decision**: Use `python-dotenv` 1.0+ for environment variables with .env file

**Rationale**:
- Simple, widely-used pattern for configuration
- Keeps secrets out of code
- Easy to override for different environments (dev, prod)
- Compatible with Docker and cloud deployments

**Implementation Pattern**:
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file

GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH")
VAULT_PATH = os.getenv("VAULT_PATH", "AI_Employee_Vault")
WATCHER_CHECK_INTERVAL = int(os.getenv("WATCHER_CHECK_INTERVAL", "60"))
```

**.env.example Template**:
```bash
# Gmail Watcher Configuration (if using Gmail)
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json

# Vault Configuration
VAULT_PATH=AI_Employee_Vault

# Watcher Configuration
WATCHER_TYPE=filesystem  # or gmail
WATCHER_CHECK_INTERVAL=60  # seconds

# Logging Configuration
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=90

# Development Mode
DRY_RUN=false
```

**Best Practices**:
- Provide .env.example with all variables (no values)
- Add .env to .gitignore immediately
- Validate required variables on startup
- Use sensible defaults for optional variables

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.13+ | Core implementation |
| File Monitoring | watchdog | 6.0+ | Detect new files |
| Gmail API | google-api-python-client | 2.187+ | Email monitoring |
| Auth | google-auth | 2.27+ | OAuth2 flow |
| YAML Parsing | pyyaml | 6.0+ | Frontmatter parsing |
| Config | python-dotenv | 1.0+ | Environment variables |
| Testing | pytest | 8.0+ | Unit/integration tests |
| Process Manager | PM2 | 5.3+ | Background processes |
| Logging | logging (stdlib) | - | Structured logging |

## Implementation Risks and Mitigations

### Risk 1: Gmail API Rate Limits
**Impact**: Watcher fails when exceeding 250 requests/user/second
**Mitigation**: Implement exponential backoff, cache message IDs, use batch requests

### Risk 2: File System Race Conditions
**Impact**: Multiple processes accessing same file simultaneously
**Mitigation**: Use file locking (fcntl on Unix, msvcrt on Windows), atomic file operations

### Risk 3: Watcher Process Crashes
**Impact**: No new inputs detected until manual restart
**Mitigation**: Use PM2 auto-restart, implement health check endpoint, alert on failures

### Risk 4: Malformed YAML Frontmatter
**Impact**: Action files cannot be parsed, processing fails
**Mitigation**: Graceful error handling, log warnings, attempt partial parsing, create clarification request

### Risk 5: Disk Space Exhaustion
**Impact**: Cannot create new action files or logs
**Mitigation**: Implement log rotation, set max log size, monitor disk usage, alert at 90% full

## Next Steps

Phase 1 will use these research findings to:
1. Define data models for Action Files, Plan Files, Dashboard, Company Handbook
2. Create contracts for BaseWatcher interface and YAML schemas
3. Generate quickstart.md with setup instructions
4. Update agent context with technology stack
