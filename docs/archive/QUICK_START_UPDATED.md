# Quick Start Guide - AI Employee System

Get your AI Employee running in 15 minutes.

---

## Prerequisites

- Linux/WSL2 environment
- Python 3.12+
- Node.js and npm (for PM2)
- Git

---

## Quick Setup (Copy-Paste Commands)

```bash
# Navigate to project
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# 1. Install PM2
npm install -g pm2

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install all dependencies
pip install watchdog google-auth google-auth-oauthlib google-api-python-client pyyaml python-dotenv playwright fastmcp mcp

# 4. Install Playwright browsers
playwright install chromium

# 5. Create environment file
cp .env.example .env

# 6. Start the system
pm2 start ecosystem.config.js

# 7. Save PM2 configuration
pm2 save

# 8. Check status
pm2 status
```

**Expected:** All three services (ai-orchestrator, mcp-email, mcp-social) should show "online".

---

## Verify It's Working

```bash
# Create a test task
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

---

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

---

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

# View specific service logs
pm2 logs ai-orchestrator

# Check status
pm2 status

# Save configuration
pm2 save
```

---

## Optional: Configure Gmail Monitoring

If you want AI to monitor your Gmail:

1. Go to https://console.cloud.google.com/
2. Create project and enable Gmail API
3. Download OAuth credentials as `credentials.json`
4. Place in project root
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

6. Restart orchestrator:

```bash
pm2 restart ai-orchestrator
```

---

## Optional: Configure WhatsApp Monitoring

If you want AI to monitor WhatsApp:

1. Install system dependency:

```bash
sudo apt-get update
sudo apt-get install libnspr4
```

2. Scan QR code:

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
python3 << 'EOF'
from src.watchers.whatsapp import WhatsAppWatcher
watcher = WhatsAppWatcher(interval=60, headless=False)
watcher._setup_browser()
input("After scanning QR code, press Enter...")
watcher.stop()
EOF
```

3. Restart orchestrator:

```bash
pm2 restart ai-orchestrator
```

---

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

The wrapper scripts should handle this automatically. If you still see errors:

```bash
# Verify wrapper scripts exist
ls -la run-*.sh

# If missing, see SETUP_TROUBLESHOOTING.md
```

### Services online but not processing

```bash
# Check orchestrator logs
pm2 logs ai-orchestrator --lines 50

# Verify vault structure
ls -la AI_Employee_Vault/

# Create test action file (see "Verify It's Working" above)
```

---

## Next Steps

- Read `PRODUCTION_GUIDE.md` for detailed setup
- Read `TESTING_GUIDE.md` for testing workflows
- Read `SETUP_TROUBLESHOOTING.md` for common issues
- Edit `AI_Employee_Vault/Company_Handbook.md` to customize behavior
- Configure auto-start: `pm2 startup` (follow printed command)

---

## Architecture Overview

**Components:**
- **ai-orchestrator**: Main coordinator, runs all watchers, processes actions
- **mcp-email**: Email sending capabilities via MCP protocol
- **mcp-social**: LinkedIn posting capabilities via MCP protocol

**Workflow:**
1. You create action file in `Needs_Action/`
2. Orchestrator detects it (polls every 5 seconds)
3. Creates execution plan in `Plans/`
4. Creates approval request in `Pending_Approval/`
5. You approve by moving to `Approved/`
6. Orchestrator executes via MCP server
7. Moves completed file to `Done/`
8. Logs everything to audit trail

**Key Directories:**
- `Needs_Action/` - Put tasks here
- `Pending_Approval/` - Review and approve here
- `Approved/` - Approved actions (auto-processed)
- `Done/` - Completed actions
- `Plans/` - Generated execution plans
- `Logs/` - Audit trail (JSON format)

---

## Support

For issues, see `SETUP_TROUBLESHOOTING.md` or check logs:

```bash
pm2 logs --err --lines 100
```
