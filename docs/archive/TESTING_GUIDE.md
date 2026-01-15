# Silver Tier Real-World Testing Guide

This guide walks you through testing all features with real scenarios, from basic to advanced.

## Phase 1: System Readiness Check (5 minutes)

### Step 1.1: Run System Check
```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
./test-system.sh
```

**Expected Output:** All checks should pass (✓). If any fail, install missing dependencies.

### Step 1.2: Verify Vault Structure
```bash
ls -la AI_Employee_Vault/
```

**Expected:** You should see Dashboard.md, Company_Handbook.md, and all subdirectories (Inbox, Needs_Action, Plans, etc.)

---

## Phase 2: Basic Orchestrator Test (10 minutes)

### Test 2.1: Start Orchestrator Manually (Dry Run)

**Purpose:** Verify the orchestrator starts without errors and all imports work.

```bash
# Set dry run mode
export DRY_RUN=true

# Start orchestrator directly (not via PM2)
python3 src/orchestration/orchestrator.py
```

**What to Watch For:**
- ✓ "Starting Orchestrator..." message
- ✓ "Started gmail_watcher thread"
- ✓ "Started whatsapp_watcher thread"
- ✓ "Started linkedin_watcher thread"
- ✗ No import errors or exceptions

**Expected Behavior:**
- Orchestrator runs in a loop (5-second poll interval)
- Watchers start in background threads
- No crashes or errors

**Stop the orchestrator:** Press `Ctrl+C`

---

## Phase 3: Action File Processing Test (15 minutes)

### Test 3.1: Create a Simple Action File

**Scenario:** Simulate an incoming email request.

```bash
cat > AI_Employee_Vault/Needs_Action/test_email_action.md << 'EOF'
---
id: "test_email_001"
type: "email"
source: "manual_test"
priority: "normal"
timestamp: "2026-01-15T14:00:00Z"
status: "pending"
metadata:
  sender: "client@example.com"
  subject: "Request for project update"
  thread_id: "test_thread_123"
---

# Incoming Email Request

**From:** client@example.com
**Subject:** Request for project update

## Message Content

Hi,

Could you please send me an update on the Q1 project status? I need this by end of week.

Thanks,
Client
EOF
```

### Test 3.2: Start Orchestrator and Watch Processing

```bash
# Terminal 1: Start orchestrator
python3 src/orchestration/orchestrator.py
```

```bash
# Terminal 2: Watch the action file
watch -n 1 'ls -lh AI_Employee_Vault/Needs_Action/'
```

**Expected Behavior (within 5-10 seconds):**
1. Orchestrator detects the file in Needs_Action/
2. Logs: "Processing action file: test_email_action.md"
3. Logs: "Plan created: [timestamp]_plan_test_email_001.md"
4. File moves from Needs_Action/ to Done/
5. New plan file appears in Plans/

### Test 3.3: Verify Plan Creation

```bash
# Check Plans directory
ls -lh AI_Employee_Vault/Plans/

# Read the generated plan
cat AI_Employee_Vault/Plans/*plan_test_email_001.md
```

**Expected Plan Content:**
- YAML frontmatter with plan ID, action reference, status
- Objective section describing the task
- Execution steps (analyze, draft, approval, send)
- "**APPROVAL**" marker for sensitive actions

### Test 3.4: Check Audit Logs

```bash
# View today's audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq '.'
```

**Expected Log Entries:**
- `create_plan` action with success result
- Timestamp, actor (plan_manager), target (plan file path)

---

## Phase 4: HITL Approval Workflow Test (20 minutes)

### Test 4.1: Create Approval Request Manually

**Scenario:** Test the approval workflow for a sensitive action (sending email).

```bash
cat > AI_Employee_Vault/Pending_Approval/test_approval_001.md << 'EOF'
---
id: "appr_test_001"
type: "approval"
action_type: "send_email"
created: "2026-01-15T14:30:00Z"
status: "pending"
context:
  plan_id: "plan_test_email_001"
  recipient: "client@example.com"
  subject: "Q1 Project Update"
---

# Approval Request: Send Email

**Action:** Send project update email to client@example.com

**Subject:** Q1 Project Update

**Draft Content:**
Hi Client,

Here's the Q1 project update you requested:
- Phase 1: Complete (100%)
- Phase 2: In Progress (75%)
- Phase 3: Scheduled for Feb 2026

Best regards,
AI Employee

**Approve this action?**
EOF
```

### Test 4.2: List Pending Approvals

```bash
# In Claude Code CLI or terminal
/manage-approval list
```

**Expected Output:**
- Shows appr_test_001 with status "pending"
- Displays action type, created date, context

### Test 4.3: Approve the Action

```bash
/manage-approval approve appr_test_001
```

**Expected Behavior:**
1. File moves from Pending_Approval/ to Approved/
2. Orchestrator detects the approved file (within 5 seconds)
3. Logs: "Found approved item: test_approval_001.md"
4. Logs: "Approved action ready for execution"
5. File moves from Approved/ to Done/

### Test 4.4: Verify Approval Logging

```bash
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.action_type == "approval_decision")'
```

**Expected:**
- Log entry with decision="approved"
- Reason: "Human approved via manage-approval skill"

### Test 4.5: Test Rejection Flow

```bash
# Create another approval request
cat > AI_Employee_Vault/Pending_Approval/test_approval_002.md << 'EOF'
---
id: "appr_test_002"
type: "approval"
action_type: "post_linkedin"
created: "2026-01-15T14:45:00Z"
status: "pending"
context:
  plan_id: "plan_social_001"
  content: "Excited to announce our Q1 results!"
---

# Approval Request: LinkedIn Post

Post update to LinkedIn: "Excited to announce our Q1 results!"

Approve?
EOF

# Reject it
/manage-approval reject appr_test_002
```

**Expected:**
- File moves to Rejected/ then to Done/
- Audit log shows decision="rejected"

---

## Phase 5: Dashboard Monitoring Test (10 minutes)

### Test 5.1: Watch Dashboard Updates

```bash
# Terminal 1: Keep orchestrator running
python3 src/orchestration/orchestrator.py
```

```bash
# Terminal 2: Watch dashboard updates
watch -n 2 'cat AI_Employee_Vault/Dashboard.md'
```

**Expected Updates (every 30 seconds):**
- Last Updated timestamp changes
- Watcher status shows "Running" for all watchers
- Pending Actions count reflects current state
- Recent Activity shows latest actions

### Test 5.2: Verify Dashboard Content

```bash
cat AI_Employee_Vault/Dashboard.md
```

**Expected Sections:**
- System Status with watcher states
- Pending Actions count
- Recent Activity list
- Errors section (should be empty)

---

## Phase 6: Gmail Watcher Test (30 minutes)

**⚠️ Prerequisites:** Gmail API credentials required

### Test 6.1: Setup Gmail Credentials

**Option A: If you have credentials.json:**
```bash
# Place your OAuth credentials file
cp /path/to/your/credentials.json .

# First run will trigger OAuth flow
python3 -c "from src.watchers.gmail import GmailWatcher; w = GmailWatcher(); w._authenticate()"
```

**Option B: Skip Gmail testing:**
```bash
# Gmail watcher will log warnings but won't crash
# System continues to work without Gmail
```

### Test 6.2: Test Gmail Watcher (if credentials available)

1. **Send yourself a test email** with subject containing "URGENT" or mark it as important
2. **Start orchestrator:**
   ```bash
   python3 src/orchestration/orchestrator.py
   ```
3. **Watch for action file creation:**
   ```bash
   watch -n 2 'ls -lh AI_Employee_Vault/Needs_Action/'
   ```

**Expected (within 60 seconds):**
- GmailWatcher detects the important email
- Creates action file: `[timestamp]_gmail_watcher_email.md`
- Action file contains sender, subject, snippet
- Orchestrator processes it and creates a plan

### Test 6.3: Verify Gmail Action File

```bash
cat AI_Employee_Vault/Done/*gmail_watcher*.md
```

**Expected Content:**
- YAML frontmatter with email metadata
- Sender, subject, thread_id
- Email snippet/preview

---

## Phase 7: WhatsApp Watcher Test (30 minutes)

**⚠️ Prerequisites:** Playwright installed, WhatsApp Web access

### Test 7.1: Setup WhatsApp Session

```bash
# Start WhatsApp watcher in non-headless mode (first time only)
python3 -c "
from src.watchers.whatsapp import WhatsAppWatcher
w = WhatsAppWatcher(interval=30, headless=False)
w._setup_browser()
print('Browser opened. Scan QR code in the browser window.')
input('Press Enter after scanning QR code...')
w.stop()
"
```

**Steps:**
1. Browser window opens with WhatsApp Web
2. Scan QR code with your phone
3. Wait for WhatsApp to load
4. Press Enter in terminal
5. Session saved to `whatsapp_session/` directory

### Test 7.2: Test WhatsApp Monitoring

**⚠️ Note:** WhatsApp watcher is a proof-of-concept. Full implementation requires more robust scraping logic.

```bash
# Start orchestrator with WhatsApp watcher
python3 src/orchestration/orchestrator.py
```

**Manual Test:**
1. Send yourself a WhatsApp message
2. Watch orchestrator logs for detection
3. Check if action file is created (implementation may need enhancement)

---

## Phase 8: MCP Servers Test (20 minutes)

### Test 8.1: Start MCP Servers with PM2

```bash
# Start all services
pm2 start ecosystem.config.js

# Check status
pm2 status
```

**Expected Output:**
```
┌─────┬──────────────────┬─────────┬─────────┐
│ id  │ name             │ status  │ restart │
├─────┼──────────────────┼─────────┼─────────┤
│ 0   │ ai-orchestrator  │ online  │ 0       │
│ 1   │ mcp-email        │ online  │ 0       │
│ 2   │ mcp-social       │ online  │ 0       │
└─────┴──────────────────┴─────────┴─────────┘
```

### Test 8.2: View MCP Server Logs

```bash
# Email server logs
pm2 logs mcp-email --lines 20

# Social server logs
pm2 logs mcp-social --lines 20

# Orchestrator logs
pm2 logs ai-orchestrator --lines 50
```

### Test 8.3: Test Email MCP (via skill)

```bash
# In Claude Code CLI
/email-ops send --to "test@example.com" --subject "Test Email" --body "This is a test" --dry-run
```

**Expected:**
- Skill connects to MCP server
- Returns success message (in dry-run mode)
- No actual email sent

### Test 8.4: Test Social MCP (via skill)

```bash
# In Claude Code CLI
/social-ops post --content "Test post from AI Employee" --dry-run
```

**Expected:**
- Skill connects to MCP server
- Duplicate detection runs
- Returns success message (in dry-run mode)

---

## Phase 9: End-to-End Integration Test (45 minutes)

### Test 9.1: Complete Workflow Test

**Scenario:** Email arrives → Plan created → Approval requested → Action executed

**Step 1: Create realistic action file**
```bash
cat > AI_Employee_Vault/Needs_Action/integration_test.md << 'EOF'
---
id: "int_test_001"
type: "email"
source: "integration_test"
priority: "high"
timestamp: "2026-01-15T15:00:00Z"
status: "pending"
metadata:
  sender: "boss@company.com"
  subject: "URGENT: Send Q1 report to board"
  thread_id: "urgent_thread_456"
---

# URGENT Email from Boss

**From:** boss@company.com
**Subject:** URGENT: Send Q1 report to board

## Message

Please send the Q1 financial report to the board members immediately. They need it for tomorrow's meeting.

Attach the latest version from our shared drive.

Thanks,
Boss
EOF
```

**Step 2: Start orchestrator and monitor**
```bash
# Terminal 1
pm2 logs ai-orchestrator --lines 100 -f

# Terminal 2
watch -n 1 'echo "=== Needs_Action ===" && ls AI_Employee_Vault/Needs_Action/ && echo "" && echo "=== Plans ===" && ls AI_Employee_Vault/Plans/ && echo "" && echo "=== Pending_Approval ===" && ls AI_Employee_Vault/Pending_Approval/'
```

**Step 3: Observe the flow**

Within 10 seconds, you should see:
1. ✓ Orchestrator detects integration_test.md
2. ✓ Plan created in Plans/
3. ✓ File moved to Done/
4. ✓ (If email sending is sensitive) Approval request created in Pending_Approval/

**Step 4: Handle approval (if created)**
```bash
/manage-approval list
/manage-approval approve <approval-id>
```

**Step 5: Verify completion**
```bash
# Check audit logs
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq '.' | tail -50

# Check dashboard
cat AI_Employee_Vault/Dashboard.md
```

---

## Phase 10: Stress Testing (30 minutes)

### Test 10.1: Multiple Concurrent Actions

```bash
# Create 10 action files rapidly
for i in {1..10}; do
cat > AI_Employee_Vault/Needs_Action/stress_test_$i.md << EOF
---
id: "stress_$i"
type: "task"
source: "stress_test"
priority: "normal"
timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status: "pending"
metadata:
  task_number: "$i"
---

# Stress Test Task $i

This is stress test task number $i.
EOF
done
```

**Monitor processing:**
```bash
pm2 logs ai-orchestrator -f
```

**Expected:**
- All 10 files processed within 30 seconds
- 10 plans created
- No crashes or errors
- Audit logs show all actions

### Test 10.2: Verify System Stability

```bash
# Check PM2 status
pm2 status

# Check for restarts (should be 0)
pm2 list

# Check memory usage
pm2 monit
```

---

## Phase 11: Error Handling Tests (20 minutes)

### Test 11.1: Malformed Action File

```bash
cat > AI_Employee_Vault/Needs_Action/bad_format.md << 'EOF'
This file has no YAML frontmatter and should be handled gracefully.
EOF
```

**Expected:**
- Orchestrator logs error
- System continues running
- File may be skipped or moved to Done/ with error logged

### Test 11.2: Missing Vault Directory

```bash
# Temporarily rename a directory
mv AI_Employee_Vault/Plans AI_Employee_Vault/Plans_backup

# Watch orchestrator handle it
pm2 logs ai-orchestrator -f
```

**Expected:**
- Vault.ensure_structure() recreates the directory
- System continues operating
- No crashes

```bash
# Restore
mv AI_Employee_Vault/Plans_backup AI_Employee_Vault/Plans
```

### Test 11.3: Watcher Crash Recovery

```bash
# Kill a watcher thread (simulated by stopping orchestrator)
pm2 stop ai-orchestrator

# Wait 10 seconds

# Restart
pm2 start ai-orchestrator
```

**Expected:**
- PM2 restarts the orchestrator automatically
- Watchers restart
- System resumes normal operation

---

## Phase 12: Production Readiness Check (15 minutes)

### Test 12.1: Verify All Security Requirements

```bash
# Check .gitignore excludes sensitive files
cat .gitignore | grep -E "\.env|token\.json|credentials\.json|whatsapp_session"
```

**Expected:** All sensitive patterns present

### Test 12.2: Verify Audit Logging

```bash
# Count audit log entries
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq -s 'length'
```

**Expected:** Multiple entries from all tests

### Test 12.3: Verify HITL Coverage

```bash
# Search for approval markers in plan files
grep -r "APPROVAL" AI_Employee_Vault/Plans/
```

**Expected:** Sensitive actions (email, post, etc.) have approval steps

### Test 12.4: PM2 Startup Configuration

```bash
# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Follow the instructions printed
```

---

## Troubleshooting Common Issues

### Issue 1: Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Install in development mode
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH="/mnt/c/Users/kk/Desktop/Daniel's FTE:$PYTHONPATH"
```

### Issue 2: PM2 Python Path Issues

**Symptom:** PM2 can't find Python modules

**Solution:** Edit ecosystem.config.js:
```javascript
env: {
  PYTHONUNBUFFERED: "1",
  PYTHONPATH: "/mnt/c/Users/kk/Desktop/Daniel's FTE",
  NODE_ENV: "production"
}
```

### Issue 3: Playwright Browser Not Found

**Symptom:** `Executable doesn't exist at /path/to/chromium`

**Solution:**
```bash
playwright install chromium
```

### Issue 4: Permission Errors on Vault

**Symptom:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```bash
chmod -R u+w AI_Employee_Vault/
```

### Issue 5: Gmail Authentication Fails

**Symptom:** `google.auth.exceptions.RefreshError`

**Solution:**
```bash
# Delete old token and re-authenticate
rm gmail_token.json
# Run OAuth flow again
```

---

## Success Criteria Checklist

After completing all tests, verify:

- [ ] Orchestrator starts without errors
- [ ] All 3 watchers start successfully
- [ ] Action files are processed within 10 seconds
- [ ] Plans are created correctly
- [ ] Approval workflow works (approve/reject)
- [ ] Dashboard updates every 30 seconds
- [ ] Audit logs capture all actions
- [ ] MCP servers respond to requests
- [ ] PM2 manages all processes
- [ ] System handles 10+ concurrent actions
- [ ] Error handling works gracefully
- [ ] No sensitive data in git
- [ ] All HITL actions require approval

---

## Next Steps After Testing

1. **Configure Production Credentials:**
   - Set up real Gmail OAuth
   - Add LinkedIn API token
   - Configure WhatsApp session

2. **Customize Behavior:**
   - Edit Company_Handbook.md with your preferences
   - Adjust approval thresholds in plan_manager.py
   - Configure watcher intervals in .env

3. **Deploy to Production:**
   - Set `DRY_RUN=false` in .env
   - Configure PM2 startup
   - Set up log rotation
   - Monitor with PM2 Plus (optional)

4. **Create Pull Request:**
   - Review all changes
   - Run final integration test
   - Create PR: 002-silver-tier → 001-bronze-tier-foundation

---

## Support

If you encounter issues during testing:
1. Check PM2 logs: `pm2 logs`
2. Check audit logs: `cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json`
3. Review quickstart.md for setup instructions
4. Check AGENTS.md for architecture details
