# AI Employee - Platinum Tier Production Assistant

**Version**: 0.4.0
**Status**: ✅ Production Ready (Platinum Tier)
**Branch**: `004-platinum-tier`

## Overview

The Personal AI Employee system is a local-first, autonomous assistant that operates 24/7 across Cloud and Local environments. It proactively manages personal and business affairs using Claude Code as the reasoning engine and Obsidian as the management dashboard.

This Platinum Tier implementation features domain-specific specialization (Cloud owns triage/drafting, Local owns approvals/execution), full Odoo accounting integration, and autonomous multi-step task completion via the Ralph Wiggum loop.

### Key Features

- **Domain Specialization**: Cloud agent handles 24/7 triage and draft generation; Local agent handles sensitive execution and approvals.
- **Ralph Wiggum Loop**: Persistent autonomous iteration until complex multi-step tasks are completed.
- **Odoo Accounting Sync**: Automated sync with Odoo Community for financial auditing and invoice management.
- **Multi-Channel Monitoring**: Monitors Gmail, WhatsApp, and LinkedIn for new work.
- **HITL Approval Workflow**: Security-first design where sensitive actions require explicit human approval.
- **Synced Vault (Local-First)**: Synchronized markdown knowledge base using Git/Syncthing with strict secret isolation.
- **Monday Morning CEO Briefing**: Automated weekly audits of revenue, bottlenecks, and costs.
- **Audit Logging**: Comprehensive JSON logs for every system action and human decision.
- **Production Infrastructure**: Robust process management with PM2 and automatic recovery.

## Quick Start (Platinum)

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **Docker** (for Odoo Community deployment)
- **PM2** (`npm install -g pm2`)

### Deployment

1. **Local Setup**:
   ```bash
   # Clone and setup vault
   ./setup-vault.sh
   pm2 start ecosystem.config.js
   ```

2. **Cloud Setup**:
   ```bash
   # On your Cloud VM (Oracle/AWS)
   cd deployment/cloud
   ./setup.sh --test
   docker-compose up -d  # Start Odoo
   pm2 start ecosystem.config.js
   ```

3. **Sync Configuration**:
   Configure Syncthing or Git between your Local and Cloud `AI_Employee_Vault` directories. Ensure `.env` files are excluded.

## System Architecture

```
[ CLOUD DOMAIN ]                    [ LOCAL DOMAIN ]
Cloud Agent (Always-On) <---------> Local Agent (Executive)
- Email Triage                      - HITL Approvals
- Draft Generation                  - WhatsApp Session
- Odoo Draft Accounting             - Payments & Posting
- Social Scheduling                 - Final Audit & Dashboard
```

## Documentation

### Tiered Deliverables
- **[Platinum Tier Spec](specs/004-platinum-tier/spec.md)** - Full production requirements
- **[Odoo Integration](docs/guides/odoo-integration-guide.md)** - ERP setup and MCP usage
- **[Handover Logic](specs/004-platinum-tier/plan.md)** - Cloud-to-Local workflow details

### Core Documentation
- **[Quickstart Guide](specs/001-bronze-tier-foundation/quickstart.md)**
- **[Testing Scenarios](specs/004-platinum-tier/tasks.md)**
- **[Architecture ADRs](history/prompts/004-platinum-tier/)**


## Quick Start

### Prerequisites

- **Python 3.12+** ([download](https://www.python.org/downloads/))
- **Node.js 18+** (for PM2 process manager)
- **Git** (for version control)
- **Linux/WSL2** (recommended for production)

### 5-Minute Setup

```bash
# 1. Navigate to project
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# 2. Install PM2
npm install -g pm2

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install watchdog google-auth google-auth-oauthlib google-api-python-client pyyaml python-dotenv playwright fastmcp mcp

# 5. Install Playwright browsers
playwright install chromium

# 6. Create environment file
cp .env.example .env

# 7. Start the system
pm2 start ecosystem.config.js

# 8. Verify it's running
pm2 status
```

**Expected:** All three services (ai-orchestrator, mcp-email, mcp-social) should show "online".

### First Task

Create your first task to verify the system works:

```bash
cat > AI_Employee_Vault/Needs_Action/test_task.md << 'EOF'
---
id: "test_001"
type: "email"
source: "manual"
priority: "high"
timestamp: "2026-01-15T12:00:00Z"
status: "pending"
---

# Test Task

Send a test email to test@example.com with subject "System Test".
EOF

# Wait 10 seconds
sleep 10

# Check if plan was created
ls AI_Employee_Vault/Plans/

# Check if approval request was created
ls AI_Employee_Vault/Pending_Approval/
```

**Expected:** You should see new files in both directories.

## Documentation

### Getting Started

- **[Quickstart Guide](specs/002-silver-tier/quickstart.md)** - Production deployment guide with installation, configuration, and troubleshooting
- **[Testing Guide](specs/002-silver-tier/testing.md)** - Comprehensive testing scenarios from basic to production

### Technical Documentation

- **[Feature Specifications](specs/002-silver-tier/spec.md)** - User stories and acceptance criteria
- **[Architecture & Decisions](specs/002-silver-tier/research.md)** - Design rationale and production lessons learned
- **[Implementation Plan](specs/002-silver-tier/plan.md)** - Architecture overview and component design
- **[Data Models](specs/002-silver-tier/data-model.md)** - File formats and structures
- **[API Contracts](specs/002-silver-tier/contracts/interfaces.md)** - Interface definitions

### Additional Reference

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed component implementation reference

## System Architecture

### Components

```
PM2 Process Manager
├── ai-orchestrator          # Main coordinator
│   ├── GmailWatcher         # Monitors Gmail
│   ├── WhatsAppWatcher      # Monitors WhatsApp
│   ├── LinkedInWatcher      # Monitors LinkedIn
│   ├── PlanManager          # Generates plans
│   ├── ApprovalManager      # HITL workflow
│   └── DashboardManager     # Updates status
├── mcp-email                # Email sending via MCP
└── mcp-social               # LinkedIn posting via MCP
```

### Workflow

1. **Input Detection**: Watchers monitor channels (Gmail, WhatsApp, LinkedIn)
2. **Action Creation**: New items create action files in `Needs_Action/`
3. **Plan Generation**: Orchestrator creates execution plan in `Plans/`
4. **Approval Request**: Sensitive actions create approval request in `Pending_Approval/`
5. **Human Decision**: You move file to `Approved/` or `Rejected/`
6. **Execution**: Orchestrator executes via MCP server
7. **Completion**: File moved to `Done/`, logged to audit trail

## Daily Usage

### Give AI a Task

```bash
cat > AI_Employee_Vault/Needs_Action/my_task.md << 'EOF'
---
id: "task_$(date +%s)"
type: "email"
source: "manual"
priority: "high"
timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status: "pending"
---

# Your Task Here

Describe what you want the AI to do.
EOF
```

### Approve Actions

```bash
# Check pending approvals
ls AI_Employee_Vault/Pending_Approval/

# Read the request
cat AI_Employee_Vault/Pending_Approval/[filename].md

# Approve
mv AI_Employee_Vault/Pending_Approval/[filename].md AI_Employee_Vault/Approved/

# Or reject
mv AI_Employee_Vault/Pending_Approval/[filename].md AI_Employee_Vault/Rejected/
```

### Monitor System

```bash
# Check status
pm2 status

# View logs
pm2 logs

# View dashboard
cat AI_Employee_Vault/Dashboard.md

# View today's audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool
```

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
```

### Optional: Gmail Monitoring

To enable Gmail monitoring:

1. Create project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth2 credentials (Desktop app)
4. Download `credentials.json` to project root
5. Run authentication:

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
python3 -c "
from src.watchers.gmail import GmailWatcher
w = GmailWatcher()
w._authenticate()
"
```

6. Restart orchestrator: `pm2 restart ai-orchestrator`

### Optional: WhatsApp Monitoring

To enable WhatsApp monitoring:

1. Install system dependency: `sudo apt-get install libnspr4`
2. Scan QR code (see [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md))
3. Restart orchestrator: `pm2 restart ai-orchestrator`

## Common Commands

```bash
# Start system
pm2 start ecosystem.config.js

# Stop system
pm2 stop all

# Restart system
pm2 restart all

# View logs
pm2 logs

# Check status
pm2 status

# Save configuration
pm2 save

# Configure auto-start on boot
pm2 startup
```

## Troubleshooting

### Services crash or restart repeatedly

```bash
# Check error logs
pm2 logs --err --lines 50

# Common fixes:
# 1. Reinstall dependencies
source venv/bin/activate
pip install --force-reinstall watchdog google-auth-oauthlib google-api-python-client pyyaml python-dotenv playwright fastmcp mcp

# 2. Restart fresh
pm2 delete all
pm2 start ecosystem.config.js
```

### "ModuleNotFoundError" errors

The wrapper scripts should handle this automatically. If you still see errors, see [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md).

### Services online but not processing

```bash
# Check orchestrator logs
pm2 logs ai-orchestrator --lines 50

# Create test action file (see "First Task" above)
```

For more issues, see [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md).

## Project Structure

```
.
├── AI_Employee_Vault/           # Local knowledge base
│   ├── Dashboard.md             # System status (auto-updated)
│   ├── Company_Handbook.md      # AI behavior rules
│   ├── Needs_Action/            # Tasks awaiting processing
│   ├── Plans/                   # Generated execution plans
│   ├── Pending_Approval/        # Awaiting human approval
│   ├── Approved/                # Human-approved actions
│   ├── Rejected/                # Human-rejected actions
│   ├── Done/                    # Completed actions
│   └── Logs/                    # Audit trail (JSON)
├── src/
│   ├── lib/                     # Core libraries
│   │   ├── vault.py             # Vault access layer
│   │   ├── logging.py           # Audit logging
│   │   └── config.py            # Configuration
│   ├── watchers/                # Input monitors
│   │   ├── base.py              # BaseWatcher abstract class
│   │   ├── gmail.py             # Gmail watcher
│   │   ├── whatsapp.py          # WhatsApp watcher
│   │   └── linkedin.py          # LinkedIn watcher
│   ├── orchestration/           # Core orchestration
│   │   ├── orchestrator.py      # Main coordinator
│   │   ├── plan_manager.py      # Plan generation
│   │   ├── approval_manager.py  # HITL workflow
│   │   ├── dashboard_manager.py # Dashboard updates
│   │   └── watchdog.py          # Health monitoring
│   └── mcp/                     # MCP servers
│       ├── email_server.py      # Email capabilities
│       └── social_server.py     # Social media capabilities
├── .claude/                     # Claude Code configuration
│   └── skills/                  # Agent Skills
├── ecosystem.config.js          # PM2 configuration
├── run-orchestrator.sh          # Wrapper script (activates venv)
├── run-mcp-email.sh             # Wrapper script (activates venv)
├── run-mcp-social.sh            # Wrapper script (activates venv)
└── .env                         # Environment configuration
```

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test
pytest tests/integration/test_watchers.py

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
pylint src/

# Type checking
mypy src/
```

## Security

- **Local-First**: All data stays on your machine
- **Human-in-the-Loop**: Sensitive actions require explicit approval
- **No Secrets in Code**: Credentials use environment variables
- **Audit Logging**: Every action logged with timestamp and details
- **Dry-Run Mode**: Test mode available for development

### Sensitive Actions (Always Require Approval)

- Email sending
- Social media posting
- Financial transactions
- Bulk operations
- Irreversible actions

## Contributing

This is a personal project, but contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]

## Support

- **Documentation**: See docs listed above
- **Issues**: Check [SETUP_TROUBLESHOOTING.md](SETUP_TROUBLESHOOTING.md)
- **Logs**: `pm2 logs --err --lines 100`

## Roadmap

### Silver Tier (Current) ✅
- Multi-channel monitoring (Gmail, WhatsApp, LinkedIn)
- Intelligent plan generation
- HITL approval workflow
- MCP servers for email and social
- Production deployment with PM2

### Gold Tier (Future)
- Accounting integration (Xero)
- Advanced social media features
- Multi-step autonomous workflows
- Cloud deployment support
- Advanced analytics and reporting

## Acknowledgments

Built with:
- [Claude Code](https://claude.com/product/claude-code) - AI development assistant
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [Playwright](https://playwright.dev/) - Browser automation
- [PM2](https://pm2.keymetrics.io/) - Process management

---

**Status**: Production Ready ✅
**Last Updated**: 2026-01-15
**Maintainer**: [Your Name]
