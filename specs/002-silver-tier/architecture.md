# AI Employee System - Technical Architecture

> **📚 Note**: For current documentation, see the [README](README.md#documentation) documentation section.
>
> This file provides detailed technical reference for component implementation. For production deployment, testing, and architecture decisions, refer to the consolidated documentation in specs/002-silver-tier/.

## Overview

The AI Employee system is a production-ready autonomous assistant that monitors multiple channels, processes tasks, and executes actions with human-in-the-loop approval.

---

## System Components

### 1. Orchestrator (`src/orchestration/orchestrator.py`)

**Purpose:** Main coordinator that manages all system components.

**Responsibilities:**
- Starts and manages watcher threads
- Polls for new action files every 5 seconds
- Coordinates plan generation
- Manages approval workflow
- Updates dashboard
- Performs health checks

**Key Features:**
- Multi-threaded watcher management
- Graceful shutdown handling
- Error recovery and logging
- Dashboard updates every 30 seconds

**Configuration:**
- `ORCHESTRATOR_POLL_INTERVAL`: How often to check for new actions (default: 5s)
- `HEALTH_CHECK_INTERVAL`: Health check frequency (default: 60s)
- `DASHBOARD_UPDATE_INTERVAL`: Dashboard update frequency (default: 30s)

---

### 2. Watchers (`src/watchers/`)

**Base Class:** `BaseWatcher` (abstract)

All watchers inherit from `BaseWatcher` and implement:
- `check_for_updates()`: Poll for new items
- `create_action_file()`: Create structured action files

#### Gmail Watcher (`gmail.py`)

**Purpose:** Monitor Gmail for urgent/important emails.

**Features:**
- OAuth2 authentication
- Queries for unread + (important OR starred) emails
- Creates action files for urgent messages
- Graceful handling of missing credentials

**Configuration:**
- `GMAIL_INTERVAL`: Check frequency (default: 60s)
- Requires: `credentials.json` and `gmail_token.json`

**Action File Format:**
```markdown
---
id: "gmail_[timestamp]"
type: "email"
source: "gmail"
priority: "high"
timestamp: "2026-01-15T12:00:00Z"
status: "pending"
metadata:
  from: "sender@example.com"
  subject: "Email subject"
  message_id: "gmail_message_id"
---

# Email from sender@example.com

Subject: Email subject

[Email body preview]
```

#### WhatsApp Watcher (`whatsapp.py`)

**Purpose:** Monitor WhatsApp Web for new messages.

**Features:**
- Playwright-based browser automation
- Session persistence (no repeated QR scanning)
- Headless mode for production
- Unread message detection

**Configuration:**
- `WHATSAPP_INTERVAL`: Check frequency (default: 60s)
- Requires: Playwright browsers installed
- Session stored in: `whatsapp_session/`

**System Requirements:**
- Linux/WSL2: `libnspr4` library
- Chromium browser (installed via Playwright)

#### LinkedIn Watcher (`linkedin.py`)

**Purpose:** Monitor LinkedIn for messages/notifications.

**Features:**
- Placeholder implementation (to be extended)
- Follows same BaseWatcher pattern

**Configuration:**
- `LINKEDIN_INTERVAL`: Check frequency (default: 300s)

---

### 3. Plan Manager (`src/orchestration/plan_manager.py`)

**Purpose:** Generate execution plans for action files.

**Process:**
1. Reads action file from `Needs_Action/`
2. Analyzes content and metadata
3. Generates structured plan
4. Writes plan to `Plans/` directory
5. Logs plan creation

**Plan File Format:**
```markdown
---
id: "plan_[timestamp]"
action_file: "original_action_file.md"
created_at: "2026-01-15T12:00:00Z"
status: "pending"
---

# Execution Plan

## Action Summary
[Summary of what needs to be done]

## Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Required Approvals
- [Approval type]

## Risks
- [Potential risks]
```

---

### 4. Approval Manager (`src/orchestration/approval_manager.py`)

**Purpose:** Manage human-in-the-loop approval workflow.

**Process:**
1. Detects action files requiring approval
2. Creates approval request in `Pending_Approval/`
3. Monitors for human decision (move to `Approved/` or `Rejected/`)
4. Processes approved actions
5. Logs all approval decisions

**Approval Request Format:**
```markdown
---
id: "AR-[date]-[sequence]-[description]"
type: "approval_request"
action_file: "original_action.md"
created_at: "2026-01-15T12:00:00Z"
status: "pending"
requires_approval: true
---

# Approval Request

## Action Summary
[What the AI wants to do]

## Details
[Detailed information]

## Approve or Reject
Move this file to:
- `Approved/` to approve
- `Rejected/` to reject
```

**Sensitive Actions (Always Require Approval):**
- Email sending
- Social media posting
- Financial transactions
- Bulk operations
- Irreversible actions

---

### 5. MCP Servers (`src/mcp/`)

**Purpose:** Provide external capabilities via Model Context Protocol.

#### Email Server (`email_server.py`)

**Capabilities:**
- `send_email(to, subject, body, attachments)`: Send email
- `read_sent_emails()`: Check sent items

**Features:**
- FastMCP-based implementation
- Dry-run mode support
- Audit logging
- Error handling

**Configuration:**
- `REQUIRE_EMAIL_APPROVAL`: Force approval (default: true)
- `DRY_RUN`: Test mode (default: false)

#### Social Server (`social_server.py`)

**Capabilities:**
- `post_to_linkedin(content, schedule)`: Post to LinkedIn
- `check_post_status(post_id)`: Check post status

**Features:**
- Duplicate content detection
- Scheduled posting support
- Dry-run mode
- Audit logging

**Configuration:**
- `REQUIRE_SOCIAL_APPROVAL`: Force approval (default: true)
- `DRY_RUN`: Test mode (default: false)

---

### 6. Dashboard Manager (`src/orchestration/dashboard_manager.py`)

**Purpose:** Update system status dashboard.

**Updates:**
- Watcher status (running/stopped)
- Pending action count
- Recent activity
- Error messages
- Last update timestamp

**Dashboard Location:** `AI_Employee_Vault/Dashboard.md`

**Update Frequency:** Every 30 seconds (configurable)

---

### 7. Watchdog (`src/orchestration/watchdog.py`)

**Purpose:** Monitor system health and restart failed components.

**Features:**
- PM2 status checking
- Watcher health monitoring
- Automatic restart on failure
- Health metrics logging

**Configuration:**
- `HEALTH_CHECK_INTERVAL`: Check frequency (default: 60s)

---

## Data Flow

### 1. Action Creation Flow

```
User/Watcher → Needs_Action/ → Orchestrator detects → Plan Manager
                                                    ↓
                                              Plans/ created
                                                    ↓
                                         Approval Manager checks
                                                    ↓
                                    Pending_Approval/ created
```

### 2. Approval Flow

```
Pending_Approval/ → Human reviews → Moves to Approved/
                                                    ↓
                                    Orchestrator detects
                                                    ↓
                                    Approval Manager processes
                                                    ↓
                                    MCP Server executes
                                                    ↓
                                    Done/ + Audit log
```

### 3. Monitoring Flow

```
Watcher (thread) → check_for_updates() → New item detected
                                                    ↓
                                    create_action_file()
                                                    ↓
                                    Needs_Action/ file created
                                                    ↓
                                    Orchestrator picks up
```

---

## File Structure

### Vault Directory Structure

```
AI_Employee_Vault/
├── Dashboard.md              # System status (auto-updated)
├── Company_Handbook.md       # AI behavior rules (user-editable)
├── README.md                 # Vault documentation
├── .gitignore                # Excludes sensitive data
├── Inbox/                    # Raw inputs (future use)
├── Needs_Action/             # Action files awaiting processing
│   └── [action_files].md
├── Plans/                    # Generated execution plans
│   └── [plan_files].md
├── Pending_Approval/         # Awaiting human approval
│   └── [approval_requests].md
├── Approved/                 # Human-approved actions
│   └── [approved_files].md
├── Rejected/                 # Human-rejected actions
│   └── [rejected_files].md
├── Done/                     # Completed actions
│   └── [completed_files].md
└── Logs/                     # Audit trail
    └── YYYY-MM-DD.json       # Daily log files
```

### Source Code Structure

```
src/
├── lib/                      # Core libraries
│   ├── vault.py              # Vault access layer
│   ├── logging.py            # Audit logging
│   └── config.py             # Configuration management
├── watchers/                 # Input monitors
│   ├── base.py               # BaseWatcher abstract class
│   ├── gmail.py              # Gmail watcher
│   ├── whatsapp.py           # WhatsApp watcher
│   └── linkedin.py           # LinkedIn watcher
├── orchestration/            # Core orchestration
│   ├── orchestrator.py       # Main coordinator
│   ├── plan_manager.py       # Plan generation
│   ├── approval_manager.py   # HITL workflow
│   ├── dashboard_manager.py  # Dashboard updates
│   └── watchdog.py           # Health monitoring
└── mcp/                      # MCP servers
    ├── email_server.py       # Email capabilities
    └── social_server.py      # Social media capabilities
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# System Mode
DRY_RUN=false                          # Set to true for testing

# Watcher Intervals (seconds)
GMAIL_INTERVAL=60                      # Gmail check frequency
WHATSAPP_INTERVAL=60                   # WhatsApp check frequency
LINKEDIN_INTERVAL=300                  # LinkedIn check frequency

# Orchestrator Settings
ORCHESTRATOR_POLL_INTERVAL=5           # Action file polling
HEALTH_CHECK_INTERVAL=60               # Health check frequency
DASHBOARD_UPDATE_INTERVAL=30           # Dashboard update frequency

# Approval Requirements
REQUIRE_EMAIL_APPROVAL=true            # Force email approval
REQUIRE_SOCIAL_APPROVAL=true           # Force social approval

# Logging
LOG_LEVEL=INFO                         # Logging verbosity
```

### PM2 Configuration (`ecosystem.config.js`)

```javascript
module.exports = {
  apps: [
    {
      name: "ai-orchestrator",
      script: "./run-orchestrator.sh",    // Wrapper script
      interpreter: "bash",                 // Use bash interpreter
      instances: 1,
      autorestart: true,
      max_memory_restart: "200M",
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: "false"
      }
    },
    // ... mcp-email and mcp-social configs
  ]
};
```

---

## Deployment Architecture

### Production Setup

```
PM2 Process Manager
├── ai-orchestrator (bash → venv → Python)
│   ├── Orchestrator
│   ├── GmailWatcher (thread)
│   ├── WhatsAppWatcher (thread)
│   ├── LinkedInWatcher (thread)
│   ├── PlanManager
│   ├── ApprovalManager
│   ├── DashboardManager
│   └── Watchdog
├── mcp-email (bash → venv → Python)
│   └── FastMCP Email Server
└── mcp-social (bash → venv → Python)
    └── FastMCP Social Server
```

### Wrapper Scripts

**Purpose:** Activate virtual environment before running Python.

**Why Needed:** PM2 uses system Python by default, which doesn't have project dependencies.

**Example (`run-orchestrator.sh`):**
```bash
#!/bin/bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
export PYTHONPATH="/mnt/c/Users/kk/Desktop/Daniel's FTE"
exec python3 src/orchestration/orchestrator.py
```

---

## Security Architecture

### Credentials Management

**Gmail:**
- `credentials.json`: OAuth client credentials (from Google Cloud Console)
- `gmail_token.json`: User access token (generated during auth)
- Both excluded from git via `.gitignore`

**WhatsApp:**
- Session data stored in `whatsapp_session/`
- Excluded from git via `.gitignore`

**Environment Variables:**
- Sensitive config in `.env` file
- `.env` excluded from git
- `.env.example` provides template

### Audit Logging

**Format:** Structured JSON logs

**Location:** `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

**Log Entry Structure:**
```json
{
  "timestamp": "2026-01-15T12:00:00.000000+00:00",
  "level": "INFO",
  "message": "",
  "logger": "orchestrator",
  "action_type": "plan_created",
  "actor": "orchestrator",
  "target": "action_file.md",
  "result": "success",
  "parameters": {},
  "details": {}
}
```

**Logged Events:**
- Action file creation
- Plan generation
- Approval decisions
- Action execution
- Errors and failures

### Human-in-the-Loop (HITL)

**Principle:** Sensitive actions require explicit human approval.

**Implementation:**
1. Action detected → Approval request created
2. Human reviews in `Pending_Approval/`
3. Human moves to `Approved/` or `Rejected/`
4. System detects decision and acts accordingly

**Sensitive Actions:**
- Email sending
- Social media posting
- Financial transactions
- Bulk operations
- Irreversible actions

---

## Performance Characteristics

### Resource Usage

**Typical:**
- ai-orchestrator: 40-50 MB RAM
- mcp-email: 50-60 MB RAM
- mcp-social: 50-60 MB RAM
- Total: ~150 MB RAM

**CPU:**
- Idle: <1% CPU
- Active processing: 5-10% CPU
- Watcher checks: Brief spikes

### Latency

**Action Processing:**
- Detection: 0-5 seconds (poll interval)
- Plan generation: 1-2 seconds
- Approval creation: <1 second
- Execution: 1-5 seconds (depends on MCP server)

**Watcher Checks:**
- Gmail: 2-5 seconds per check
- WhatsApp: 5-10 seconds per check (browser automation)
- LinkedIn: 2-5 seconds per check

---

## Scalability Considerations

### Current Limitations

- Single-threaded orchestrator (one action at a time)
- File-based state (not suitable for high volume)
- Local-only deployment

### Future Enhancements

- Database backend for state management
- Distributed orchestration
- Queue-based action processing
- Multi-instance deployment
- Cloud deployment support

---

## Monitoring and Observability

### Health Checks

**Watchdog monitors:**
- PM2 process status
- Watcher thread health
- File system accessibility
- Log file rotation

**Health Check Frequency:** Every 60 seconds

### Metrics

**Available via logs:**
- Actions processed per day
- Approval response time
- Watcher check frequency
- Error rates
- Execution success rate

### Dashboard

**Real-time status:**
- Watcher status (running/stopped)
- Pending action count
- Recent activity (last 10 items)
- Error messages
- Last update timestamp

**Location:** `AI_Employee_Vault/Dashboard.md`

---

## Error Handling

### Watcher Errors

**Strategy:** Log and continue

**Behavior:**
- Error logged to audit trail
- Watcher continues on next interval
- No system crash

### Orchestrator Errors

**Strategy:** Log and skip

**Behavior:**
- Error logged
- Current action skipped
- Next action processed
- System remains running

### MCP Server Errors

**Strategy:** Return error to orchestrator

**Behavior:**
- Error logged
- Action marked as failed
- Moved to `Done/` with error status
- Human notified via dashboard

---

## Testing Strategy

### Unit Tests

**Location:** `tests/unit/`

**Coverage:**
- Vault operations
- Logging functionality
- Configuration management
- Watcher base class

### Integration Tests

**Location:** `tests/integration/`

**Coverage:**
- Orchestrator workflow
- Watcher integration
- MCP server communication
- Approval workflow

### Manual Testing

**Scripts:**
- `quick-test.sh`: Fast integration test
- `demo-workflow.sh`: Interactive demo
- `test-system.sh`: System readiness check

---

## Maintenance

### Daily

- Check PM2 status: `pm2 status`
- Review pending approvals: `ls AI_Employee_Vault/Pending_Approval/`
- Check dashboard: `cat AI_Employee_Vault/Dashboard.md`

### Weekly

- Review audit logs: `cat AI_Employee_Vault/Logs/*.json`
- Check error logs: `pm2 logs --err --lines 100`
- Restart services: `pm2 restart all`

### Monthly

- Clean old logs: `find AI_Employee_Vault/Logs/ -name "*.json" -mtime +30 -delete`
- Clean done files: `find AI_Employee_Vault/Done/ -name "*.md" -mtime +30 -delete`
- Update dependencies: `pip install --upgrade [packages]`

---

## Troubleshooting

See `SETUP_TROUBLESHOOTING.md` for detailed troubleshooting guide.

**Quick Checks:**

1. **Services not starting:**
   ```bash
   pm2 logs --err --lines 50
   ```

2. **Actions not processing:**
   ```bash
   pm2 logs ai-orchestrator --lines 50
   ```

3. **Dependency issues:**
   ```bash
   source venv/bin/activate
   pip list
   ```

4. **Restart fresh:**
   ```bash
   pm2 delete all
   pm2 start ecosystem.config.js
   ```

---

## References

- **Production Guide:** `PRODUCTION_GUIDE.md`
- **Quick Start:** `QUICK_START_UPDATED.md`
- **Troubleshooting:** `SETUP_TROUBLESHOOTING.md`
- **Testing:** `TESTING_GUIDE.md`
- **Constitution:** `.specify/memory/constitution.md`
