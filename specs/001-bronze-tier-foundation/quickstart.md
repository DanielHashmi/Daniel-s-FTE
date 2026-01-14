# Quickstart Guide: Bronze Tier - Personal AI Employee Foundation

**Version**: 1.0.0
**Date**: 2026-01-14
**Estimated Setup Time**: 30 minutes

## Overview

This guide will help you set up the Bronze Tier Personal AI Employee system, which includes:
- Obsidian vault for knowledge management
- One Watcher (Gmail OR File System) for input detection
- Claude Code integration for AI processing
- Agent Skills for system management

## Prerequisites

Before starting, ensure you have:

- [ ] **Obsidian** v1.11.4+ installed ([download](https://obsidian.md/download))
- [ ] **Python** 3.13+ installed ([download](https://www.python.org/downloads/))
- [ ] **Claude Code** installed and configured ([setup guide](https://claude.com/product/claude-code))
- [ ] **Git** installed (for version control)
- [ ] **Node.js** v24+ (for PM2 process manager)
- [ ] Approximately 100MB free disk space
- [ ] Stable internet connection (10+ Mbps)

**Optional** (if using Gmail Watcher):
- [ ] Google account with Gmail access
- [ ] Ability to create OAuth2 credentials in Google Cloud Console

## Step 1: Clone or Navigate to Project

```bash
# If you haven't already, navigate to your project directory
cd "/path/to/Daniel's FTE"

# Verify you're on the Bronze Tier branch
git branch --show-current
# Should show: 001-bronze-tier-foundation
```

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies (includes all required packages)
pip install --upgrade pip
pip install -e .

# For development (includes testing tools):
pip install -e ".[dev]"
```

## Step 3: Initialize Obsidian Vault

The AI_Employee_Vault folder should already exist at the project root. You can use the setup-vault skill to initialize its structure:

```bash
# Run the vault setup skill
python .claude/skills/setup-vault/scripts/main_operation.py

# This will create all required folders and files
```

Alternatively, you can verify the structure manually:

```bash
# Check that all folders exist
ls -la AI_Employee_Vault/

# Should show:
# - Inbox/
# - Needs_Action/
# - Done/
# - Plans/
# - Logs/
# - Pending_Approval/
# - Approved/
# - Rejected/
# - Dashboard.md
# - Company_Handbook.md
```

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cat > .env << 'EOF'
# Vault Configuration
VAULT_PATH=AI_Employee_Vault

# Watcher Configuration
WATCHER_TYPE=filesystem  # or gmail
WATCHER_CHECK_INTERVAL=60  # seconds

# Gmail Watcher Configuration (if using Gmail)
# GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
# GMAIL_TOKEN_PATH=/path/to/token.json

# Logging Configuration
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=90

# Development Mode
DRY_RUN=false
EOF

echo "✅ .env file created"
```

**Important**: Add `.env` to `.gitignore` immediately:

```bash
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
```

## Step 5: Choose and Configure Your Watcher

### Option A: File System Watcher (Recommended for beginners)

The File System Watcher monitors the `AI_Employee_Vault/Inbox` folder for new files.

**No additional configuration needed!** Just drop files into the Inbox folder and the watcher will detect them.

**Test it**:
```bash
# Create a test file
echo "Test task: Review quarterly report" > AI_Employee_Vault/Inbox/test-task.txt
```

### Option B: Gmail Watcher (Advanced)

The Gmail Watcher monitors your Gmail inbox for emails with priority keywords.

**Setup Steps**:

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project: "AI Employee"
   - Enable Gmail API

2. **Create OAuth2 Credentials**:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Download credentials JSON file
   - Save as `credentials.json` in project root

3. **Update .env file**:
   ```bash
   WATCHER_TYPE=gmail
   GMAIL_CREDENTIALS_PATH=credentials.json
   GMAIL_TOKEN_PATH=token.json
   ```

4. **First-time authentication**:
   ```bash
   # Run the Gmail watcher once to authenticate
   python src/watchers/gmail_watcher.py
   # This will open a browser for OAuth consent
   # After approval, token.json will be created
   ```

## Step 6: Open Vault in Obsidian

1. Launch Obsidian
2. Click "Open folder as vault"
3. Navigate to `AI_Employee_Vault` in your project directory
4. Click "Open"

You should now see:
- Dashboard.md
- Company_Handbook.md
- All the folders (Inbox, Needs_Action, Done, etc.)

**Tip**: Pin Dashboard.md for quick access.

## Step 7: Start the Watcher

### Using PM2 (Recommended for production)

```bash
# Install PM2 globally
npm install -g pm2

# Start File System Watcher
pm2 start src/watchers/filesystem_watcher.py --interpreter python3 --name ai-watcher

# OR start Gmail Watcher
pm2 start src/watchers/gmail_watcher.py --interpreter python3 --name ai-watcher

# View logs
pm2 logs ai-watcher

# Check status
pm2 status

# Save process list for auto-start on boot
pm2 save
pm2 startup
```

### Manual Start (for development/testing)

```bash
# Start File System Watcher
python src/watchers/filesystem_watcher.py

# OR start Gmail Watcher
python src/watchers/gmail_watcher.py

# Press Ctrl+C to stop
```

## Step 8: Test the System

### Test 1: Input Detection

**For File System Watcher**:
```bash
# Create a test action file
echo "Urgent: Review contract for Client A" > AI_Employee_Vault/Inbox/urgent-task.txt

# Wait up to 60 seconds
# Check AI_Employee_Vault/Needs_Action for new file
```

**For Gmail Watcher**:
- Send yourself an email with "urgent" or "invoice" in the subject
- Wait up to 2 minutes
- Check AI_Employee_Vault/Needs_Action for new file

### Test 2: Claude Processing

```bash
# Navigate to project root
cd "/path/to/Daniel's FTE"

# Run Claude Code on the vault
cd AI_Employee_Vault && claude

# In Claude, say:
# "Process all files in Needs_Action and create plans"

# Claude should:
# 1. Read action files
# 2. Read Company_Handbook.md
# 3. Create Plan.md files
# 4. Move action files to Done
# 5. Update Dashboard.md
```

### Test 3: Verify Dashboard

Open `AI_Employee_Vault/Dashboard.md` in Obsidian and verify:
- System Status shows "Watcher: Running"
- Pending Actions count is updated
- Recent Activity shows your test actions

## Step 9: Using Agent Skills

Agent Skills provide reusable commands for common operations.

### Available Skills (Bronze Tier)

1. **setup-vault**: Initialize vault structure
   ```bash
   python -m src.skills.setup_vault
   ```

2. **start-watcher**: Launch watcher process
   ```bash
   python -m src.skills.watcher_manager start
   ```

3. **stop-watcher**: Stop watcher process
   ```bash
   python -m src.skills.watcher_manager stop
   ```

4. **process-inbox**: Run Claude on pending actions
   ```bash
   python -m src.skills.process_inbox
   ```

5. **view-dashboard**: Display current system status
   ```bash
   python -m src.skills.view_dashboard
   ```

## Troubleshooting

### Watcher Not Detecting Files

**Problem**: Files in Inbox aren't being processed

**Solutions**:
- Check watcher is running: `pm2 status` or check terminal
- Verify file extensions are supported (.txt, .md, .pdf, .docx, .csv)
- Check logs: `AI_Employee_Vault/Logs/watcher-YYYY-MM-DD.log`
- Ensure check_interval isn't too long (default: 60 seconds)

### Claude Code Not Finding Vault

**Problem**: Claude says it can't find files

**Solutions**:
- Ensure you're running Claude from within the `AI_Employee_Vault` directory
- Check that `CLAUDE.md` exists in the vault or project root
- Verify vault path in .env file
- Check folder permissions

### Gmail Watcher Authentication Errors

**Problem**: "Invalid credentials" or "Token expired"

**Solutions**:
- Delete `token.json` and re-authenticate
- Verify `credentials.json` is valid
- Check OAuth consent screen is configured
- Ensure Gmail API is enabled in Google Cloud Console

### Logs Not Being Created

**Problem**: No log files in AI_Employee_Vault/Logs

**Solutions**:
- Verify Logs folder exists
- Check file permissions
- Ensure watcher is actually running
- Look for errors in terminal output

## Daily Usage

### Morning Routine

1. Open Obsidian and check Dashboard.md
2. Review pending actions in Needs_Action folder
3. Run Claude to process new items
4. Review generated plans in Plans folder

### Adding Manual Tasks

1. Create new .md file in Needs_Action folder
2. Add YAML frontmatter with required fields
3. Write task description in body
4. Claude will process it on next run

### Monitoring System Health

```bash
# Check watcher status
pm2 status

# View recent logs
pm2 logs ai-watcher --lines 50

# Check disk usage
du -sh AI_Employee_Vault/

# View error logs
grep ERROR AI_Employee_Vault/Logs/*.log
```

## Next Steps

Once Bronze Tier is working smoothly:

1. **Silver Tier**: Add multiple watchers, MCP servers, HITL workflows
2. **Gold Tier**: Full automation with accounting, social media, CEO briefings
3. **Customization**: Modify Company_Handbook.md to match your workflow
4. **Optimization**: Tune check intervals, add custom priority keywords

## Getting Help

- **Documentation**: See `specs/001-bronze-tier-foundation/` for detailed specs
- **Issues**: Check logs in `AI_Employee_Vault/Logs/`
- **Community**: Join Wednesday research meetings (see hackathon document)

## Security Reminders

- ✅ Never commit `.env` file to Git
- ✅ Rotate OAuth tokens monthly
- ✅ Review audit logs weekly
- ✅ Keep credentials in secure storage
- ✅ Use dry-run mode for testing

---

**Congratulations!** You now have a working Bronze Tier Personal AI Employee system. The foundation is in place for building more advanced automation in Silver and Gold tiers.
