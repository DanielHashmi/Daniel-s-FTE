# 🚀 Quick Start: Testing Silver Tier

Get your AI Employee system up and running in 5 minutes!

## Prerequisites Check

```bash
# Run system check
./test-system.sh
```

This verifies:
- ✓ Python 3.12+
- ✓ Required dependencies
- ✓ Vault structure
- ✓ PM2 installation

---

## Option 1: Quick Automated Test (Recommended First)

**Time:** 2 minutes
**What it does:** Tests basic functionality automatically

```bash
./quick-test.sh
```

**Expected Result:**
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

---

## Option 2: Interactive Demo

**Time:** 5 minutes
**What it does:** Shows complete workflow with explanations

```bash
./demo-workflow.sh
```

**You'll see:**
1. Realistic email scenario created
2. Orchestrator processing in real-time
3. Plan generation
4. Approval workflow
5. Audit logging
6. Dashboard updates

---

## Option 3: Manual Testing

### Step 1: Start the System

```bash
# Start all services with PM2
pm2 start ecosystem.config.js

# View logs
pm2 logs
```

### Step 2: Create a Test Action

```bash
cat > AI_Employee_Vault/Needs_Action/my_test.md << 'EOF'
---
id: "my_test_001"
type: "email"
source: "manual"
priority: "normal"
timestamp: "2026-01-15T16:00:00Z"
status: "pending"
metadata:
  sender: "test@example.com"
  subject: "Test Email"
---

# Test Email

This is my first test of the AI Employee system!
EOF
```

### Step 3: Watch It Process

```bash
# In another terminal, run the monitor
./monitor.sh
```

**Within 10 seconds you'll see:**
- File disappears from Needs_Action/
- New plan appears in Plans/
- File moves to Done/
- Dashboard updates

### Step 4: Check Results

```bash
# View the generated plan
ls -lh AI_Employee_Vault/Plans/
cat AI_Employee_Vault/Plans/*my_test*.md

# Check audit logs
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq '.'

# View dashboard
cat AI_Employee_Vault/Dashboard.md
```

---

## Real-Time Monitoring

Keep this running in a separate terminal to watch system activity:

```bash
./monitor.sh
```

Shows:
- PM2 process status
- Vault file counts
- Recent activity
- Today's statistics
- Latest log entries

Updates every 3 seconds.

---

## Testing Approval Workflow

### Create an Approval Request

```bash
cat > AI_Employee_Vault/Pending_Approval/test_approval.md << 'EOF'
---
id: "appr_test_001"
type: "approval"
action_type: "send_email"
created: "2026-01-15T16:00:00Z"
status: "pending"
context:
  recipient: "client@example.com"
  subject: "Test Email"
---

# Approval Request

Send test email to client@example.com?
EOF
```

### Approve or Reject

```bash
# List pending approvals
/manage-approval list

# Approve
/manage-approval approve appr_test_001

# OR reject
/manage-approval reject appr_test_001
```

### Watch Processing

The orchestrator will detect the approval/rejection within 5 seconds and:
- Move file to Approved/ or Rejected/
- Log the decision
- Process the action (if approved)
- Move to Done/

---

## Testing with Real Services

### Gmail Watcher (Optional)

**Setup:**
```bash
# Place your OAuth credentials
cp /path/to/credentials.json .

# Run authentication
python3 -c "from src.watchers.gmail import GmailWatcher; w = GmailWatcher(); w._authenticate()"
```

**Test:**
1. Send yourself an important email
2. Watch orchestrator logs: `pm2 logs ai-orchestrator`
3. Check for action file creation

### WhatsApp Watcher (Optional)

**Setup:**
```bash
# First-time setup (scan QR code)
python3 -c "
from src.watchers.whatsapp import WhatsAppWatcher
w = WhatsAppWatcher(interval=30, headless=False)
w._setup_browser()
input('Scan QR code, then press Enter...')
w.stop()
"
```

**Test:**
1. Send yourself a WhatsApp message
2. Watch for detection in logs

---

## Common Commands

### PM2 Management

```bash
# Start all services
pm2 start ecosystem.config.js

# Stop all services
pm2 stop all

# Restart all services
pm2 restart all

# View logs
pm2 logs

# View specific service logs
pm2 logs ai-orchestrator
pm2 logs mcp-email
pm2 logs mcp-social

# Monitor resources
pm2 monit

# Check status
pm2 status
```

### Manual Orchestrator (for debugging)

```bash
# Run orchestrator directly (not via PM2)
export DRY_RUN=true
python3 src/orchestration/orchestrator.py

# Stop with Ctrl+C
```

### Clean Up Test Files

```bash
# Remove all test files
rm -f AI_Employee_Vault/Needs_Action/test_*.md
rm -f AI_Employee_Vault/Needs_Action/demo_*.md
rm -f AI_Employee_Vault/Plans/test_*.md
rm -f AI_Employee_Vault/Plans/demo_*.md
rm -f AI_Employee_Vault/Done/test_*.md
rm -f AI_Employee_Vault/Done/demo_*.md
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

```bash
# Install in development mode
pip install -e .

# OR set PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### "PM2 command not found"

```bash
npm install -g pm2
```

### "Playwright browser not found"

```bash
playwright install chromium
```

### Orchestrator not processing files

1. Check PM2 logs: `pm2 logs ai-orchestrator`
2. Verify vault structure: `./test-system.sh`
3. Check file permissions: `ls -la AI_Employee_Vault/`
4. Try manual run: `python3 src/orchestration/orchestrator.py`

### No audit logs appearing

1. Check Logs directory exists: `ls -la AI_Employee_Vault/Logs/`
2. Check file permissions
3. Look for errors in orchestrator logs

---

## Next Steps

After successful testing:

1. **Configure Production:**
   - Set `DRY_RUN=false` in .env
   - Add real Gmail credentials
   - Configure LinkedIn token
   - Set up WhatsApp session

2. **Customize Behavior:**
   - Edit `AI_Employee_Vault/Company_Handbook.md`
   - Adjust approval thresholds in `src/orchestration/plan_manager.py`
   - Configure watcher intervals in `.env`

3. **Production Deployment:**
   ```bash
   pm2 save
   pm2 startup
   # Follow the instructions printed
   ```

4. **Read Full Documentation:**
   - `TESTING_GUIDE.md` - Comprehensive testing scenarios
   - `specs/002-silver-tier/quickstart.md` - Detailed setup
   - `AGENTS.md` - Architecture and rules

---

## Success Checklist

- [ ] System check passes (`./test-system.sh`)
- [ ] Quick test passes (`./quick-test.sh`)
- [ ] Demo workflow completes (`./demo-workflow.sh`)
- [ ] PM2 services start successfully
- [ ] Action files are processed within 10 seconds
- [ ] Plans are created correctly
- [ ] Approval workflow works
- [ ] Dashboard updates automatically
- [ ] Audit logs capture all actions
- [ ] Monitor shows real-time activity

---

## Getting Help

- **Check logs:** `pm2 logs`
- **View audit trail:** `cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json`
- **Read testing guide:** `TESTING_GUIDE.md`
- **Review architecture:** `AGENTS.md`

---

**Ready to test?** Start with: `./quick-test.sh`
