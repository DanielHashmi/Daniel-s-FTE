# Production Deployment Guide - Real Use

This guide will get your AI Employee running in production for REAL work.

---

## STEP 1: Install PM2 (Process Manager)

PM2 keeps your AI Employee running 24/7, even after system restarts.

```bash
# Install Node.js if you don't have it
# Check if you have it:
node --version

# If not installed, install Node.js first, then:
npm install -g pm2

# Verify PM2 is installed
pm2 --version
```

**Expected:** PM2 version number displayed

---

## STEP 2: Install Python Dependencies

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

---

## STEP 3: Configure Environment

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
```

**Save and close** (Ctrl+X, then Y, then Enter in nano)

---

## STEP 4: Configure Gmail (For Real Email Monitoring)

**Note:** Gmail credentials are optional. The system works without them, but won't monitor email.

### 4.1: Get Gmail API Credentials

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Name it: "AI Employee"
   - Download the JSON file

### 4.2: Setup Credentials

```bash
# Copy your downloaded credentials file to project root
cp ~/Downloads/client_secret_*.json "/mnt/c/Users/kk/Desktop/Daniel's FTE/credentials.json"

# Activate virtual environment
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate

# Run authentication (this opens browser)
python3 -c "
from src.watchers.gmail import GmailWatcher
w = GmailWatcher()
w._authenticate()
"
```

**What happens:**
1. Browser opens
2. Sign in with your Gmail account
3. Grant permissions
4. Token saved as `gmail_token.json`

**Test it:**
```bash
# Send yourself an important email, then:
source venv/bin/activate
python3 -c "
from src.watchers.gmail import GmailWatcher
w = GmailWatcher()
w.check_for_updates()
"

# Check if action file was created
ls AI_Employee_Vault/Needs_Action/
```

---

## STEP 5: Configure WhatsApp (Optional but Recommended)

**Note:** WhatsApp monitoring is optional. Skip this if you don't need it.

### 5.1: Install System Dependencies (WSL2/Linux)

```bash
# Required for Playwright on WSL2
sudo apt-get update
sudo apt-get install libnspr4
```

### 5.2: First-Time Setup (Scan QR Code)

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate

python3 << 'EOF'
from src.watchers.whatsapp import WhatsAppWatcher

print("Opening WhatsApp Web...")
print("Scan the QR code with your phone")
print("")

watcher = WhatsAppWatcher(interval=60, headless=False)
watcher._setup_browser()

input("After scanning QR code and WhatsApp loads, press Enter...")
watcher.stop()

print("✓ WhatsApp session saved!")
EOF
```

**Steps:**
1. Browser window opens with WhatsApp Web
2. Open WhatsApp on your phone
3. Go to Settings > Linked Devices > Link a Device
4. Scan the QR code
5. Wait for WhatsApp to load completely
6. Press Enter in terminal
7. Session saved for future use

**Test it:**
```bash
# Send yourself a WhatsApp message, then:
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
python3 -c "
from src.watchers.whatsapp import WhatsAppWatcher
w = WhatsAppWatcher(headless=True)
w.check_for_updates()
"
```

---

## STEP 6: Start Production System

**IMPORTANT:** The system uses wrapper scripts that activate the virtual environment automatically.

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Start all services
pm2 start ecosystem.config.js

# Check status
pm2 status
```

**Expected output:**
```
┌─────┬──────────────────┬─────────┬─────────┬─────────┐
│ id  │ name             │ status  │ restart │ uptime  │
├─────┼──────────────────┼─────────┼─────────┼─────────┤
│ 0   │ ai-orchestrator  │ online  │ 0       │ 0s      │
│ 1   │ mcp-email        │ online  │ 0       │ 0s      │
│ 2   │ mcp-social       │ online  │ 0       │ 0s      │
└─────┴──────────────────┴─────────┴─────────┴─────────┘
```

**All should show "online"**

**Verify it's working:**
```bash
# Wait 10 seconds for startup, then check logs
sleep 10
pm2 logs ai-orchestrator --lines 20 --nostream

# You should see JSON log entries indicating the orchestrator is running
```

**If services crash or restart repeatedly:**
```bash
# Check error logs
pm2 logs --err --lines 50

# Common issues:
# 1. Missing dependencies - reinstall: pip install [package]
# 2. Permission issues - check file permissions
# 3. Path issues - verify PYTHONPATH in wrapper scripts
```

---

## STEP 7: Configure Auto-Start on Boot

```bash
# Save current PM2 configuration
pm2 save

# Setup PM2 to start on system boot
pm2 startup

# Follow the command it prints (will be something like):
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u yourusername --hp /home/yourusername
```

**Now your AI Employee will start automatically when your computer boots!**

---

## STEP 7: Monitor Your AI Employee

### View Logs in Real-Time

```bash
# All logs
pm2 logs

# Just orchestrator
pm2 logs ai-orchestrator

# Just email MCP
pm2 logs mcp-email

# Just social MCP
pm2 logs mcp-social
```

### View Dashboard

```bash
# In terminal
cat AI_Employee_Vault/Dashboard.md

# Or open in editor
code AI_Employee_Vault/Dashboard.md
```

### Monitor with Script

```bash
# Real-time monitoring (updates every 3 seconds)
./monitor.sh
```

---

## STEP 8: Daily Usage - How to Actually Use It

### Scenario 1: Let AI Monitor Your Email

**What happens automatically:**
1. AI checks your Gmail every 60 seconds
2. Detects important/urgent emails
3. Creates action file in Needs_Action/
4. Generates execution plan
5. If it needs to send email, creates approval request
6. You get notified (check Pending_Approval/)

**Your workflow:**
```bash
# Check for pending approvals
ls AI_Employee_Vault/Pending_Approval/

# Read the approval request
cat AI_Employee_Vault/Pending_Approval/*.md

# Approve or reject
/manage-approval list
/manage-approval approve <id>
# OR
/manage-approval reject <id>
```

**Real example:**
```bash
# Morning routine:
pm2 logs ai-orchestrator --lines 50  # See what AI detected overnight
ls AI_Employee_Vault/Pending_Approval/  # Check what needs approval
/manage-approval list  # Review all pending
/manage-approval approve appr_001  # Approve the ones you want
```

---

### Scenario 2: Give AI a Task Manually

**When you need AI to do something:**

```bash
# Create a task file
cat > AI_Employee_Vault/Inbox/my_task.md << 'EOF'
---
id: "task_$(date +%s)"
type: "email"
source: "manual"
priority: "high"
timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status: "pending"
metadata:
  task: "Send Q1 report to board"
---

# Task: Send Q1 Report

Send the Q1 financial report to board@company.com

Include:
- Revenue summary
- Expense breakdown
- Projections for Q2

Deadline: EOD today
EOF

# Move to Needs_Action (or AI will pick it up from Inbox)
mv AI_Employee_Vault/Inbox/my_task.md AI_Employee_Vault/Needs_Action/
```

**Within 5 seconds:**
- AI detects the file
- Creates execution plan
- Asks for approval if needed
- You approve
- AI executes

---

### Scenario 3: Review What AI Did Today

```bash
# View today's audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool

# Count actions
echo "Total actions today: $(cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep -c action_type)"

# See what plans were created
ls -lh AI_Employee_Vault/Plans/

# Check completed actions
ls -lh AI_Employee_Vault/Done/
```

---

### Scenario 4: Post to LinkedIn

```bash
# Create social media task
cat > AI_Employee_Vault/Needs_Action/linkedin_post.md << 'EOF'
---
id: "social_$(date +%s)"
type: "social"
source: "manual"
priority: "normal"
timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status: "pending"
metadata:
  platform: "linkedin"
---

# LinkedIn Post

Excited to announce our Q1 results!

Key highlights:
- 50% revenue growth
- 3 new major clients
- Expanded team to 25 people

Looking forward to an amazing Q2! 🚀

#startup #growth #tech
EOF

mv AI_Employee_Vault/Inbox/linkedin_post.md AI_Employee_Vault/Needs_Action/
```

**AI will:**
1. Create plan
2. Check for duplicate content
3. Ask for approval
4. Post after approval

---

## STEP 9: Customize Behavior

### Edit Company Handbook

```bash
code AI_Employee_Vault/Company_Handbook.md
```

**Add your preferences:**
```markdown
# Communication Style
- Professional but friendly
- Keep emails concise
- Always include action items

# Approval Thresholds
- Emails to clients: ALWAYS require approval
- Internal emails: Auto-send if < 3 recipients
- Social media: ALWAYS require approval
- Financial actions: ALWAYS require approval

# Priority Rules
- Emails from boss@company.com: HIGH priority
- Emails with "URGENT": HIGH priority
- LinkedIn messages: NORMAL priority
- WhatsApp from family: LOW priority (don't process)
```

### Adjust Watcher Intervals

```bash
# Edit .env
nano .env

# Change intervals based on your needs:
GMAIL_INTERVAL=30          # More frequent (every 30 seconds)
WHATSAPP_INTERVAL=120      # Less frequent (every 2 minutes)
LINKEDIN_INTERVAL=600      # Even less (every 10 minutes)

# Restart to apply changes
pm2 restart all
```

---

## STEP 10: Maintenance & Monitoring

### Daily Checks

```bash
# Morning routine:
pm2 status                                    # Check all services running
pm2 logs ai-orchestrator --lines 20          # See recent activity
ls AI_Employee_Vault/Pending_Approval/       # Check pending approvals
cat AI_Employee_Vault/Dashboard.md           # Review dashboard
```

### Weekly Maintenance

```bash
# Check logs for errors
pm2 logs --err --lines 100

# Clean up old files (optional)
find AI_Employee_Vault/Done/ -name "*.md" -mtime +30 -delete  # Delete files older than 30 days

# Restart services (good practice)
pm2 restart all
```

### If Something Goes Wrong

```bash
# Check status
pm2 status

# View errors
pm2 logs --err

# Restart specific service
pm2 restart ai-orchestrator

# Restart all
pm2 restart all

# Stop all (if needed)
pm2 stop all

# Delete all and start fresh
pm2 delete all
pm2 start ecosystem.config.js
```

---

## STEP 11: Advanced Features

### Schedule Recurring Tasks

Create `Config/schedules.json`:
```json
{
  "schedules": [
    {
      "id": "daily_report",
      "cron": "0 9 * * *",
      "action": "send_daily_report",
      "description": "Send daily report at 9am"
    },
    {
      "id": "weekly_summary",
      "cron": "0 17 * * 5",
      "action": "send_weekly_summary",
      "description": "Send weekly summary Friday 5pm"
    }
  ]
}
```

### Use Skills Directly

```bash
# Send email via skill
/email-ops send --to "client@example.com" --subject "Q1 Report" --body "Please find attached..." --attachment "report.pdf"

# Post to LinkedIn via skill
/social-ops post --content "Excited to announce..." --schedule "2026-01-16T10:00:00Z"

# Manage approvals
/manage-approval list
/manage-approval approve appr_001
/manage-approval reject appr_002
```

---

## STEP 12: Troubleshooting Production Issues

### Issue: AI not detecting emails

**Check:**
```bash
pm2 logs ai-orchestrator | grep gmail
```

**Common causes:**
- Gmail token expired
- Credentials invalid
- Watcher not running

**Fix:**
```bash
# Re-authenticate
python3 -c "from src.watchers.gmail import GmailWatcher; w = GmailWatcher(); w._authenticate()"

# Restart
pm2 restart ai-orchestrator
```

---

### Issue: Approvals not processing

**Check:**
```bash
ls AI_Employee_Vault/Pending_Approval/
ls AI_Employee_Vault/Approved/
pm2 logs ai-orchestrator | grep approval
```

**Fix:**
```bash
# Manually move to Approved to test
mv AI_Employee_Vault/Pending_Approval/test.md AI_Employee_Vault/Approved/

# Watch logs
pm2 logs ai-orchestrator -f
```

---

### Issue: High CPU/Memory usage

**Check:**
```bash
pm2 monit
```

**Fix:**
```bash
# Increase intervals in .env
GMAIL_INTERVAL=120
WHATSAPP_INTERVAL=180
ORCHESTRATOR_POLL_INTERVAL=10

# Restart
pm2 restart all
```

---

## STEP 13: Security Best Practices

### Protect Credentials

```bash
# Ensure .env is in .gitignore
grep ".env" .gitignore

# Set proper permissions
chmod 600 .env
chmod 600 gmail_token.json
chmod 600 credentials.json

# Never commit these files
git status  # Should not show .env or token files
```

### Review Audit Logs Regularly

```bash
# Weekly review
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool | grep -A5 "approval_decision"

# Check for suspicious activity
cat AI_Employee_Vault/Logs/*.json | grep "error\|failed\|unauthorized"
```

---

## STEP 14: Backup Your Data

```bash
# Backup vault
tar -czf ai_employee_backup_$(date +%Y%m%d).tar.gz AI_Employee_Vault/

# Backup configuration
cp .env .env.backup
cp ecosystem.config.js ecosystem.config.js.backup

# Store backups safely
mv ai_employee_backup_*.tar.gz ~/Backups/
```

---

## Your Daily Workflow

### Morning (5 minutes)
```bash
pm2 status                                    # Check system health
pm2 logs ai-orchestrator --lines 50          # Review overnight activity
ls AI_Employee_Vault/Pending_Approval/       # Check pending approvals
/manage-approval list                         # Review and approve
```

### Throughout Day (as needed)
```bash
# Check for new approvals
ls AI_Employee_Vault/Pending_Approval/

# Give AI new tasks
cat > AI_Employee_Vault/Needs_Action/task.md << 'EOF'
[your task here]
EOF

# Monitor activity
./monitor.sh
```

### Evening (2 minutes)
```bash
cat AI_Employee_Vault/Dashboard.md           # Review day's activity
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool | tail -50  # Check logs
```

---

## Success Metrics

After 1 week of production use, you should see:
- [ ] 50+ emails processed automatically
- [ ] 10+ plans created
- [ ] 5+ approvals handled
- [ ] 0 missed urgent emails
- [ ] Complete audit trail
- [ ] System uptime > 99%

---

## Getting Help

**Check logs first:**
```bash
pm2 logs --err --lines 100
```

**Check audit trail:**
```bash
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool
```

**Check system status:**
```bash
pm2 status
./monitor.sh
```

---

## You're Live!

Your AI Employee is now running in production, monitoring your channels 24/7.

**Next:** Just use it! Let it monitor your email, give it tasks, approve actions, and watch it work.

**Remember:** You're in control. AI asks for approval on sensitive actions. You decide what gets executed.
