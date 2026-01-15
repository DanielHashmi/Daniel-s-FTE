# Silver Tier Quickstart

This guide will get your AI Employee running in production for real work.

## Prerequisites
- Python 3.12+
- Node.js v20+ (for PM2)
- PM2 (`npm install -g pm2`)
- Virtual environment (venv)
- Credentials for Gmail API (optional for testing)

**System Requirements:**
- Linux/WSL2: `libnspr4` library (for WhatsApp watcher)
- Disk space: ~500MB for dependencies and browsers

## 1. Install PM2 (Process Manager)

PM2 keeps your AI Employee running 24/7, even after system restarts.

```bash
# Check if Node.js is installed
node --version

# If not installed, install Node.js first, then:
npm install -g pm2

# Verify PM2 is installed
pm2 --version
```

## 2. Install Python Dependencies

**CRITICAL:** All dependencies must be installed in a virtual environment.

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install all required dependencies
pip install watchdog google-auth google-auth-oauthlib google-api-python-client pyyaml python-dotenv playwright fastmcp mcp

# Install Playwright browsers
playwright install chromium

# Verify installations
python3 -c "from fastmcp import FastMCP; print('✓ FastMCP installed')"
python3 -c "from google_auth_oauthlib.flow import InstalledAppFlow; print('✓ Google Auth installed')"
python3 -c "from playwright.sync_api import sync_playwright; print('✓ Playwright installed')"
```

**Expected:** All three verification checks should print success messages.

**Note:** If you're on WSL2 and WhatsApp watcher fails, install system library:
```bash
sudo apt-get update
sudo apt-get install libnspr4
```

## 3. Configure Environment

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Create your environment file
cp .env.example .env

# Edit it
nano .env
# OR
code .env
```

**Set these values:**

```bash
# IMPORTANT: Set to false for production
DRY_RUN=false

# Adjust intervals based on your needs
GMAIL_INTERVAL=60          # Check Gmail every 60 seconds
WHATSAPP_INTERVAL=60       # Check WhatsApp every 60 seconds
LINKEDIN_INTERVAL=300      # Check LinkedIn every 5 minutes

# Orchestrator settings
ORCHESTRATOR_POLL_INTERVAL=5    # Check for new actions every 5 seconds
HEALTH_CHECK_INTERVAL=60        # Health check every minute
DASHBOARD_UPDATE_INTERVAL=30    # Update dashboard every 30 seconds

# Approval requirements
REQUIRE_EMAIL_APPROVAL=true     # Force email approval
REQUIRE_SOCIAL_APPROVAL=true    # Force social approval
```

**Save and close** (Ctrl+X, then Y, then Enter in nano)

## 4. Configure Gmail (Optional)

**Note:** Gmail credentials are optional. The system works without them, but won't monitor email.

If you want email monitoring:

1. **Get OAuth credentials from Google Cloud Console**
2. **Download `credentials.json`** and place in project root
3. **Run OAuth flow** (first time only):
   ```bash
   source venv/bin/activate
   python3 -c "from src.watchers.gmail import GmailWatcher; w = GmailWatcher(); w.check_for_updates()"
   ```
4. **Follow browser prompts** to authorize
5. **Verify `gmail_token.json`** was created

## 5. Verify Wrapper Scripts

The project uses wrapper scripts to activate the virtual environment before running Python. Verify they exist:

```bash
ls -la run-*.sh
```

You should see:
- `run-orchestrator.sh`
- `run-mcp-email.sh`
- `run-mcp-social.sh`

These scripts are already configured in `ecosystem.config.js`.

## 6. Initialize Vault Structure

The vault structure is automatically created by the orchestrator, but you can verify it:
```bash
ls AI_Employee_Vault/
# Should see: Dashboard.md, Company_Handbook.md, Inbox/, Needs_Action/, Plans/, etc.
```

## 7. Start the System with PM2

Start all services (orchestrator, watchers, MCP servers):
```bash
pm2 start ecosystem.config.js
pm2 logs
```

Check status:
```bash
pm2 status
```

## 6. Test Workflow

Choose your testing approach based on your needs:

### Option 1: Quick Automated Test (Recommended First)

**Time:** 2 minutes | **Purpose:** Verify basic functionality automatically

```bash
./quick-test.sh
```

**Expected Output:**
```
🧪 Silver Tier Quick Test
=========================
✓ All vault directories exist
✓ All Python modules import correctly
✓ Action file processed
✓ Plan file created
✓ Audit logs working

🎉 All tests passed!
```

### Option 2: Interactive Demo Workflow

**Time:** 5 minutes | **Purpose:** See complete workflow with explanations

```bash
./demo-workflow.sh
```

**Shows:**
- Realistic email scenario creation
- Orchestrator processing in real-time
- Plan generation
- Approval workflow
- Audit logging
- Dashboard updates

### Option 3: Manual Test (Detailed Control)

1. **Create a test action file** in `AI_Employee_Vault/Needs_Action/`:
   ```bash
   cat > AI_Employee_Vault/Needs_Action/test_action.md << 'EOF'
   ---
   id: "test_001"
   type: "email"
   source: "manual"
   priority: "normal"
   timestamp: "2026-01-15T12:00:00Z"
   status: "pending"
   metadata:
     sender: "test@example.com"
     subject: "Test Email"
   ---

   # Test Email

   This is a test email to verify the system is working.
   EOF
   ```

2. **Watch the orchestrator logs**:
   ```bash
   pm2 logs ai-orchestrator
   ```

3. **Verify plan creation**:
   ```bash
   ls AI_Employee_Vault/Plans/
   # Should see a new plan file
   ```

4. **Check for approval requests** (if action is sensitive):
   ```bash
   ls AI_Employee_Vault/Pending_Approval/
   ```

5. **Approve or reject** using the manage-approval skill:
   ```bash
   # In Claude Code CLI
   /manage-approval list
   /manage-approval approve <approval-id>
   ```

6. **Verify completion**:
   ```bash
   ls AI_Employee_Vault/Done/
   # Original action file should be moved here
   ```

7. **Check audit logs**:
   ```bash
   cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool
   ```

### Option 4: Integration Tests

Run the full test suite:
```bash
pytest tests/integration/test_watchers.py -v
```

### Real-Time Monitoring

Keep this running in a separate terminal to watch system activity:

```bash
./monitor.sh
```

**Shows:**
- PM2 process status
- Vault file counts
- Recent activity
- Today's statistics
- Latest log entries

Updates every 3 seconds.

## 7. Monitor System Health

View the dashboard:
```bash
cat AI_Employee_Vault/Dashboard.md
```

Check PM2 status:
```bash
pm2 status
pm2 monit
```

## 8. Stop the System

```bash
pm2 stop all
# or
pm2 delete all
```

## Troubleshooting

### Issue 1: PM2 Services Crash with "ModuleNotFoundError"

**Symptoms:**
```
ModuleNotFoundError: No module named 'google'
ModuleNotFoundError: No module named 'fastmcp'
```

**Root Cause:** PM2 is using system Python instead of virtual environment.

**Solution:**
Verify wrapper scripts exist and are executable:
```bash
ls -la run-*.sh
# Should see: run-orchestrator.sh, run-mcp-email.sh, run-mcp-social.sh

# If missing, recreate them (see SETUP_TROUBLESHOOTING.md)
chmod +x run-*.sh
pm2 restart all
```

### Issue 2: WhatsApp Watcher Fails with "libnspr4.so" Error

**Symptoms:**
```
error while loading shared libraries: libnspr4.so: cannot open shared object file
```

**Solution:**
```bash
sudo apt-get update
sudo apt-get install libnspr4
pm2 restart ai-orchestrator
```

### Issue 3: Services Start but Don't Process Actions

**Symptoms:**
- PM2 shows "online" but no files are processed
- No logs appearing

**Solution:**
```bash
# Check orchestrator logs
pm2 logs ai-orchestrator --lines 50

# Verify vault structure
ls -la AI_Employee_Vault/

# Create test action and wait 10 seconds
cat > AI_Employee_Vault/Needs_Action/test.md << 'EOF'
---
id: "test_001"
type: "email"
source: "manual"
priority: "high"
timestamp: "2026-01-15T12:00:00Z"
status: "pending"
---

Test action
EOF

sleep 10
ls AI_Employee_Vault/Plans/
```

### Issue 4: PM2 Shows High Restart Count

**Symptoms:**
```
│ ai-orchestrator  │ online  │ 15      │ 10s     │
```

**Solution:**
```bash
# Check error logs
pm2 logs ai-orchestrator --err --lines 50

# Delete and restart fresh
pm2 delete all
pm2 start ecosystem.config.js
```

### Issue 5: Gmail Authentication Fails

**Symptoms:**
- Browser doesn't open during authentication
- "credentials.json not found" error

**Solution:**
```bash
# Verify credentials file exists
ls -la credentials.json

# Run authentication with virtual environment
source venv/bin/activate
python3 -c "from src.watchers.gmail import GmailWatcher; w = GmailWatcher(); w._authenticate()"
```

### Issue 6: Virtual Environment Not Found

**Symptoms:**
```
bash: venv/bin/activate: No such file or directory
```

**Solution:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install watchdog google-auth google-auth-oauthlib google-api-python-client pyyaml python-dotenv playwright fastmcp mcp
playwright install chromium
```

### Issue 7: Slow Startup on WSL2

**Symptoms:**
- Services take 30+ seconds to start

**Root Cause:** WSL2 file system performance when accessing Windows files.

**Solution:**
This is normal on WSL2. Wait 30-60 seconds after `pm2 start` before checking status.

### Verification Checklist

After fixing issues:
```bash
# 1. Check PM2 status (all should be "online")
pm2 status

# 2. Check for errors
pm2 logs --err --lines 20

# 3. Test with action file
cat > AI_Employee_Vault/Needs_Action/test_$(date +%s).md << 'EOF'
---
id: "test_001"
type: "email"
source: "manual"
priority: "high"
timestamp: "2026-01-15T12:00:00Z"
status: "pending"
---

Test action
EOF

# 4. Wait and verify plan creation
sleep 10
ls AI_Employee_Vault/Plans/
```

**For more detailed troubleshooting, see:** `SETUP_TROUBLESHOOTING.md` in project root

## Production Deployment

1. Set `DRY_RUN=false` in .env
2. Configure proper credentials for Gmail and LinkedIn
3. Set up PM2 to start on system boot:
   ```bash
   pm2 startup
   pm2 save
   ```
4. Configure log rotation:
   ```bash
   pm2 install pm2-logrotate
   ```
5. Monitor with PM2 Plus (optional):
   ```bash
   pm2 link <secret> <public>
   ```

## Next Steps

- Configure Company_Handbook.md with your preferences
- Set up scheduled tasks using the scheduler skill
- Integrate with real email and social media accounts
- Customize approval thresholds in plan_manager.py
