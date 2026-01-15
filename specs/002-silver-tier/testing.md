# Silver Tier Testing Guide

Comprehensive testing guide for validating all Silver Tier features with real scenarios.

---

## Quick Start Testing

### Option 1: Automated Quick Test (2 minutes)

Run the automated test suite:
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

### Option 2: Interactive Demo (5 minutes)

Run the interactive demo workflow:
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

### Option 3: System Readiness Check

Verify all dependencies and structure:
```bash
./test-system.sh
```

**Checks:**
- Python 3.12+ installed
- Required dependencies available
- Vault structure exists
- PM2 installation

---

## Phase 1: Basic Orchestrator Test (10 minutes)

### Test 1.1: Start Orchestrator Manually (Dry Run)

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

## Phase 2: Action File Processing Test (15 minutes)

### Test 2.1: Create a Simple Action File

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

### Test 2.2: Start Orchestrator and Watch Processing

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

### Test 2.3: Verify Plan Creation

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

### Test 2.4: Check Audit Logs

```bash
# View today's audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool
```

**Expected Log Entries:**
- `create_plan` action with success result
- Timestamp, actor (plan_manager), target (plan file path)

---

## Phase 3: HITL Approval Workflow Test (20 minutes)

### Test 3.1: Create Approval Request Manually

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

### Test 3.2: List Pending Approvals

```bash
# In Claude Code CLI or terminal
/manage-approval list
```

**Expected Output:**
- Shows appr_test_001 with status "pending"
- Displays action type, created date, context

### Test 3.3: Approve the Action

```bash
/manage-approval approve appr_test_001
```

**Expected Behavior:**
1. File moves from Pending_Approval/ to Approved/
2. Orchestrator detects the approved file (within 5 seconds)
3. Logs: "Found approved item: test_approval_001.md"
4. Action is executed (in dry-run mode, logs the action)
5. File moves to Done/
6. Audit log records approval and execution

### Test 3.4: Test Rejection

```bash
# Create another approval request
cat > AI_Employee_Vault/Pending_Approval/test_approval_002.md << 'EOF'
---
id: "appr_test_002"
type: "approval"
action_type: "send_email"
created: "2026-01-15T14:35:00Z"
status: "pending"
context:
  recipient: "test@example.com"
---

# Test Approval Request

Test rejection workflow.
EOF

# Reject it
/manage-approval reject appr_test_002
```

**Expected Behavior:**
1. File moves from Pending_Approval/ to Rejected/
2. Orchestrator detects the rejection
3. Audit log records the rejection
4. No action is executed

---

## Phase 4: Real-World Use Cases

### Use Case 1: Urgent Client Email Management

**Scenario:** You're in a meeting and miss an urgent client email. AI monitors inbox, detects urgency, creates action plan, and asks for approval before responding.

#### Step 1: Create the urgent email scenario

```bash
cat > AI_Employee_Vault/Needs_Action/urgent_client.md << 'EOF'
---
id: "urgent_001"
type: "email"
source: "gmail"
priority: "high"
timestamp: "2026-01-15T18:00:00Z"
status: "pending"
metadata:
  sender: "john.smith@acmecorp.com"
  subject: "URGENT: Need proposal by tomorrow 9am"
---

# URGENT Email from Client

**From:** john.smith@acmecorp.com (Acme Corp - $500K client)
**Subject:** URGENT: Need proposal by tomorrow 9am

## Email Content

Hi, Our board meeting is tomorrow at 9am and they want to see your proposal for the Q2 project. Can you send it ASAP?

We need:
1. Project timeline
2. Cost breakdown
3. Team allocation

This is time-sensitive - they're making the decision tomorrow.

Thanks,
John Smith
EOF
```

#### Step 2: Run the AI orchestrator

```bash
# Run orchestrator for 10 seconds
timeout 10 python3 src/orchestration/orchestrator.py
```

**What's happening:**
- Orchestrator detects the urgent email
- Analyzes the content
- Identifies it's from a high-value client
- Creates an execution plan
- Moves file to Done/

#### Step 3: Review the AI-generated plan

```bash
# Check if file was processed
ls AI_Employee_Vault/Needs_Action/urgent_client.md 2>/dev/null && echo "Still in Needs_Action" || echo "✓ Processed and moved"

# View the AI-generated plan
cat AI_Employee_Vault/Plans/*urgent*.md

# Check for approval request
ls AI_Employee_Vault/Pending_Approval/*urgent*.md
```

**Expected Plan Content:**
- Recognizes urgency and high-value client
- Outlines steps: gather proposal materials, draft response, send email
- Flags email send for human approval
- Includes timeline and priority markers

#### Step 4: Approve and execute

```bash
# List pending approvals
/manage-approval list

# Approve the action
/manage-approval approve <approval-id>

# Verify execution in logs
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool
```

---

## Phase 5: Multi-Channel Watcher Testing

### Test 5.1: Gmail Watcher (Optional - Requires Credentials)

**Setup:**
```bash
# Place your OAuth credentials
cp /path/to/credentials.json .

# Run authentication
python3 -c "from src.watchers.gmail import GmailWatcher; w = GmailWatcher(); w._authenticate()"
```

**Test:**
1. Send yourself an important email with "URGENT" in subject
2. Watch orchestrator logs: `pm2 logs ai-orchestrator`
3. Check for action file creation in Needs_Action/
4. Verify plan creation in Plans/

### Test 5.2: WhatsApp Watcher (Optional - Requires Setup)

**Setup:**
```bash
# First-time setup (scan QR code)
python3 << 'EOF'
from src.watchers.whatsapp import WhatsAppWatcher
w = WhatsAppWatcher(interval=30, headless=False)
w._setup_browser()
input('Scan QR code, then press Enter...')
w.stop()
EOF
```

**Test:**
1. Send yourself a WhatsApp message with "urgent" keyword
2. Watch for detection in logs
3. Verify action file creation

### Test 5.3: LinkedIn Watcher (Optional - Requires Token)

**Setup:**
```bash
# Add LinkedIn token to .env
echo "LINKEDIN_ACCESS_TOKEN=your_token_here" >> .env
```

**Test:**
1. Send yourself a LinkedIn message
2. Watch for detection in logs
3. Verify action file creation

---

## Phase 6: PM2 Production Testing

### Test 6.1: Start All Services with PM2

```bash
pm2 start ecosystem.config.js
pm2 logs
```

**Expected:**
- All three services start: ai-orchestrator, mcp-email, mcp-social
- All show "online" status
- No crash loops or high restart counts

### Test 6.2: Test with PM2 Running

```bash
# Create test action
cat > AI_Employee_Vault/Needs_Action/pm2_test.md << 'EOF'
---
id: "pm2_test_001"
type: "email"
source: "manual"
priority: "normal"
timestamp: "2026-01-15T16:00:00Z"
status: "pending"
---

PM2 test action
EOF

# Wait 10 seconds
sleep 10

# Check if processed
ls AI_Employee_Vault/Plans/*pm2_test*.md
```

### Test 6.3: Monitor System Health

```bash
# Use the monitoring script
./monitor.sh
```

**Shows:**
- PM2 process status
- Vault file counts
- Recent activity
- Today's statistics
- Latest log entries

Updates every 3 seconds.

---

## Phase 7: Integration Testing

### Test 7.1: Run Integration Test Suite

```bash
pytest tests/integration/test_watchers.py -v
```

**Expected:**
- All tests pass
- Watchers can be instantiated
- Action files are created correctly
- Plans are generated

---

## Verification Checklist

After completing all tests, verify:

```bash
# 1. Check PM2 status (all should be "online")
pm2 status

# 2. Check for errors
pm2 logs --err --lines 20

# 3. Verify vault structure
ls -la AI_Employee_Vault/

# 4. Check audit logs exist
ls -lh AI_Employee_Vault/Logs/

# 5. Verify dashboard updates
cat AI_Employee_Vault/Dashboard.md

# 6. Test action processing
cat > AI_Employee_Vault/Needs_Action/final_test_$(date +%s).md << 'EOF'
---
id: "final_test_001"
type: "email"
source: "manual"
priority: "high"
timestamp: "2026-01-15T12:00:00Z"
status: "pending"
---

Final verification test
EOF

# 7. Wait and verify plan creation
sleep 10
ls AI_Employee_Vault/Plans/
```

---

## Success Criteria

- [ ] System check passes (`./test-system.sh`)
- [ ] Quick test passes (`./quick-test.sh`)
- [ ] Demo workflow completes (`./demo-workflow.sh`)
- [ ] PM2 services start successfully
- [ ] Action files are processed within 10 seconds
- [ ] Plans are created correctly
- [ ] Approval workflow works (approve and reject)
- [ ] Dashboard updates automatically
- [ ] Audit logs capture all actions
- [ ] Monitor shows real-time activity
- [ ] Integration tests pass

---

## Troubleshooting Test Failures

### Test fails: "ModuleNotFoundError"
```bash
source venv/bin/activate
pip install -e .
```

### Test fails: "PM2 command not found"
```bash
npm install -g pm2
```

### Test fails: "Playwright browser not found"
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

## Next Steps After Testing

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
   - `quickstart.md` - Production deployment guide
   - `research.md` - Architecture decisions
   - `spec.md` - Feature specifications
