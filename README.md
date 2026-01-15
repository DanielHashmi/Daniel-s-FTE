# AI Employee - Silver Tier Functional Assistant

**Version**: 0.2.0
**Status**: Silver Tier (Functional Assistant)
**Branch**: `002-silver-tier`

## Overview

The Personal AI Employee system Is a local-first, autonomous assistant that monitors multiple input sources (Gmail, WhatsApp, LinkedIn), creates structured plans, and executes approved actions via Agent Skills. This Silver Tier implementation transforms the foundation into a functional assistant capable of real-world interactions under human supervision.

### Key Features

- **Local-First Architecture**: All data stays on your machine in an Obsidian vault
- **Multi-Channel Monitoring**: Monitors Gmail, WhatsApp, and LinkedIn for new work
- **Intelligent Planning**: Claude autonomously creates execution plans for incoming tasks
- **HITL Approval Workflow**: Sensitive actions require explicit human approval via file system
- **MCP Integrations**: Modular servers for Email sending and LinkedIn posting
- **Agent Skills**: Reusable capabilities for all AI operations
- **Audit Logging**: Comprehensive JSON logs for all system activities

## Quick Start

### Prerequisites

- **Python 3.13+** ([download](https://www.python.org/downloads/))
- **Obsidian 1.11.4+** ([download](https://obsidian.md/download))
- **Claude Code** ([setup guide](https://claude.com/product/claude-code))
- **Node.js 24+** (for PM2 process manager)
- **Git** (for version control)

### Installation

1. **Clone or navigate to the project**:
   ```bash
   cd "/path/to/Daniel's FTE"
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv

   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -e .

   # For development (includes testing tools):
   pip install -e ".[dev]"
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize the vault** (if not already done):
   ```bash
   python .claude/skills/setup-vault/scripts/main_operation.py
   ```

6. **Open vault in Obsidian**:
   - Launch Obsidian
   - Click "Open folder as vault"
   - Navigate to `AI_Employee_Vault`
   - Pin `Dashboard.md` for quick access

### Running the Watcher

#### Option A: File System Watcher (Recommended for beginners)

```bash
# Start with PM2 (production)
pm2 start ecosystem.config.js --only ai-watcher-filesystem

# OR run manually (development)
python src/watchers/filesystem_watcher.py
```

Drop files into `AI_Employee_Vault/Inbox/` and the watcher will detect them automatically.

#### Option B: Gmail Watcher (Advanced)

1. **Set up Google Cloud credentials**:
   - Create project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Gmail API
   - Create OAuth2 credentials (Desktop app)
   - Download `credentials.json` to project root

2. **Update `.env`**:
   ```bash
   WATCHER_TYPE=gmail
   GMAIL_CREDENTIALS_PATH=credentials.json
   GMAIL_TOKEN_PATH=token.json
   ```

3. **Authenticate** (first time only):
   ```bash
   python src/watchers/gmail_watcher.py
   # Browser will open for OAuth consent
   ```

4. **Start watcher**:
   ```bash
   pm2 start ecosystem.config.js --only ai-watcher-gmail
   ```

### Processing Action Files

Once action files are created in `Needs_Action/`, use Claude Code to process them:

```bash
cd AI_Employee_Vault
claude

# In Claude, say:
# "Process all files in Needs_Action and create plans"
```

Claude will:
1. Read action files
2. Read `Company_Handbook.md` for behavior rules
3. Create plan files in `Plans/`
4. Move processed files to `Done/`
5. Update `Dashboard.md`

## Project Structure

```
.
├── AI_Employee_Vault/          # Obsidian vault (knowledge base)
│   ├── Inbox/                  # Drop folder for file system watcher
│   ├── Needs_Action/           # Pending action files
│   ├── Done/                   # Completed action files
│   ├── Plans/                  # Generated plan files
│   ├── Logs/                   # System logs
│   ├── Dashboard.md            # Real-time system status
│   └── Company_Handbook.md     # AI behavior rules
│
├── src/                        # Source code
│   ├── config.py               # Configuration management
│   ├── watchers/               # Input detection
│   │   ├── base_watcher.py    # Abstract base class
│   │   ├── filesystem_watcher.py
│   │   └── gmail_watcher.py
│   └── utils/                  # Shared utilities
│       ├── logger.py           # Structured logging
│       ├── yaml_parser.py      # Frontmatter parsing
│       └── retry.py            # Retry decorator
│
├── .claude/skills/             # Agent Skills
│   ├── setup-vault/            # Initialize vault structure
│   ├── watcher-manager/        # Start/stop watchers
│   ├── process-inbox/          # Process action files
│   └── view-dashboard/         # Display system status
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
│
├── specs/                      # Feature specifications
│   └── 001-bronze-tier-foundation/
│       ├── spec.md             # Feature specification
│       ├── plan.md             # Implementation plan
│       ├── tasks.md            # Task breakdown
│       └── contracts/          # API contracts
│
├── pyproject.toml              # Python project configuration
├── ecosystem.config.js         # PM2 process configuration
├── .env.example                # Environment variable template
└── README.md                   # This file
```

## Agent Skills

Agent Skills are reusable capabilities that perform specific functions. They're located in `.claude/skills/` and can be invoked via Claude Code.

### Available Skills

1. **setup-vault**: Initialize vault structure
   ```bash
   python .claude/skills/setup-vault/scripts/main_operation.py
   ```

2. **watcher-manager**: Manage watcher processes
   ```bash
   python .claude/skills/watcher-manager/scripts/main_operation.py --action start --watcher-type filesystem
   python .claude/skills/watcher-manager/scripts/main_operation.py --action status
   ```

3. **process-inbox**: Process pending action files and create plans
   ```bash
   python .claude/skills/process-inbox/scripts/main_operation.py --priority high
   ```

4. **view-dashboard**: Display system status
   ```bash
   python .claude/skills/view-dashboard/scripts/main_operation.py
   ```

5. **manage-approval**: Manage HITL workflows (list, approve, reject)
   ```bash
   python .claude/skills/manage-approval/scripts/main_operation.py --action list
   ```

6. **email-ops**: Send/Check Emails via MCP
   ```bash
   python .claude/skills/email-ops/scripts/main_operation.py --action status
   ```

7. **social-ops**: LinkedIn posting via MCP
   ```bash
   python .claude/skills/social-ops/scripts/main_operation.py --action list-recent
   ```

8. **scheduler**: Manage cron tasks
   ```bash
   python .claude/skills/scheduler/scripts/main_operation.py --action list
   ```

## Configuration

All configuration is managed via environment variables in `.env`:

```bash
# Vault Configuration
VAULT_PATH=AI_Employee_Vault

# Watcher Configuration
WATCHER_TYPE=filesystem  # Options: filesystem, gmail
WATCHER_CHECK_INTERVAL=60  # Seconds between checks

# Gmail Watcher (if using Gmail)
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
GMAIL_QUERY=is:unread (urgent OR invoice OR payment)

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_RETENTION_DAYS=90

# Development
DRY_RUN=false  # Set to true for testing
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_yaml_parser.py

# Run integration tests only
pytest tests/integration/
```

## Monitoring

### Check Watcher Status

```bash
# Using PM2
pm2 status
pm2 logs ai-watcher-filesystem

# Check logs
tail -f AI_Employee_Vault/Logs/watcher-$(date +%Y-%m-%d).log
```

### View Dashboard

Open `AI_Employee_Vault/Dashboard.md` in Obsidian to see:
- Watcher status
- Pending actions count
- Recent activity
- Quick stats
- Errors

## Troubleshooting

### Watcher Not Detecting Files

**Problem**: Files in Inbox aren't being processed

**Solutions**:
- Check watcher is running: `pm2 status`
- Verify supported file extensions (.txt, .md, .pdf, .docx, .csv)
- Check logs: `AI_Employee_Vault/Logs/watcher-YYYY-MM-DD.log`
- Ensure check_interval isn't too long

### Gmail Authentication Errors

**Problem**: "Invalid credentials" or "Token expired"

**Solutions**:
- Delete `token.json` and re-authenticate
- Verify `credentials.json` is valid
- Check Gmail API is enabled in Google Cloud Console
- Ensure OAuth consent screen is configured

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solutions**:
- Ensure virtual environment is activated
- Install package in editable mode: `pip install -e .`
- Check you're running from project root

## Security

- ✅ Never commit `.env` to Git (already in `.gitignore`)
- ✅ Store credentials in environment variables, not code
- ✅ Rotate OAuth tokens monthly
- ✅ Review audit logs weekly
- ✅ Use dry-run mode for testing

## Next Steps

Once Silver Tier is working smoothly:

1. **Gold Tier**: Full automation with accounting, social media, CEO briefings
2. **Customization**: Modify `Company_Handbook.md` to match your workflow
3. **Optimization**: Tune check intervals, add custom priority keywords

## Documentation

- **Specification**: `specs/002-silver-tier/spec.md`
- **Implementation Plan**: `specs/002-silver-tier/plan.md`
- **Tasks**: `specs/002-silver-tier/tasks.md`
- **Quickstart Guide**: `specs/002-silver-tier/quickstart.md`
- **Data Model**: `specs/002-silver-tier/data-model.md`

## Contributing

This is a personal project, but contributions are welcome:

1. Create a feature branch: `git checkout -b 002-feature-name`
2. Follow the Spec-Driven Development workflow
3. Run tests before committing: `pytest`
4. Create a pull request

## License

MIT License - See LICENSE file for details

## Support

- **Issues**: Check logs in `AI_Employee_Vault/Logs/`
- **Documentation**: See `specs/002-silver-tier/`
- **Community**: Join Wednesday research meetings

---

**Congratulations!** You now have a working Silver Tier Personal AI Employee system. The foundation is in place for building more advanced automation in Gold tier.
