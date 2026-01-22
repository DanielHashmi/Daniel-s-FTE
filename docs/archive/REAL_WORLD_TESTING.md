# Real-World Use Cases - Step by Step Testing

This guide shows you EXACTLY what the AI Employee does in real life, with working examples you can run.

---

## 🎯 REAL USE CASE #1: Urgent Client Email Management

### What This Solves in Real Life:
- You're in a meeting and miss an urgent client email
- AI monitors your inbox 24/7
- Detects urgent messages
- Creates action plan
- Asks for your approval before responding
- Sends response and logs everything

### Let's See It Work:

#### Step 1: Create the urgent email scenario

Run these commands ONE AT A TIME:

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
```

```bash
# Create the urgent email file
cat > AI_Employee_Vault/Needs_Action/urgent_client.md << 'ENDOFFILE'
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
ENDOFFILE
```

```bash
# Verify the file was created
ls -lh AI_Employee_Vault/Needs_Action/urgent_client.md
```

**You should see:** File created successfully

---

#### Step 2: Run the AI orchestrator to process it

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

---

#### Step 3: See what the AI created

```bash
# Check if file was processed
echo "=== Checking if file was processed ==="
ls AI_Employee_Vault/Needs_Action/urgent_client.md 2>/dev/null && echo "Still in Needs_Action" || echo "✓ Processed and moved"
```

```bash
# View the AI-generated plan
echo ""
echo "=== AI-GENERATED PLAN ==="
cat AI_Employee_Vault/Plans/*urgent*.md
```

**You should see a plan like:**
```
# Objective
Handle urgent client request from Acme Corp

# Execution Steps
- [ ] 1. Analyze email content
- [ ] 2. Draft response
- [ ] 3. **APPROVAL**: Send Reply
- [ ] 4. Archive Email
```

---

#### Step 4: Check the audit log

```bash
# View audit trail
echo ""
echo "=== AUDIT LOG ==="
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool | tail -20
```

**You should see:** JSON log entries showing:
- Action detected
- Plan created
- Timestamp
- Actor (orchestrator)

---

## 🎯 REAL USE CASE #2: Approval Workflow for Sensitive Actions

### What This Solves in Real Life:
- AI wants to send an email to a client
- You need to approve it first (safety!)
- AI creates approval request
- You review and approve/reject
- AI executes only after approval
- Everything logged for compliance

### Let's See It Work:

#### Step 1: Create an approval request

```bash
cat > AI_Employee_Vault/Pending_Approval/send_proposal.md << 'ENDOFFILE'
---
id: "appr_001"
type: "approval"
action_type: "send_email"
created: "2026-01-15T18:30:00Z"
status: "pending"
context:
  recipient: "john.smith@acmecorp.com"
  subject: "Q2 Project Proposal - Acme Corp"
  has_attachment: true
---

# Approval Request: Send Client Proposal

**Action:** Send Q2 proposal to Acme Corp client

## Email Details
- **To:** john.smith@acmecorp.com
- **Subject:** Q2 Project Proposal - Acme Corp
- **Attachment:** Q2_Proposal_Final.pdf

## Draft Email:
Hi John,

Please find attached our Q2 project proposal including:
- Project timeline (12 weeks)
- Cost breakdown ($250K)
- Team allocation (5 engineers)

Available for questions before your board meeting tomorrow.

Best regards

## Risk Assessment
- Sensitivity: HIGH (client communication, financial data)
- Reversibility: LOW (cannot unsend)
- Impact: HIGH (affects $500K client relationship)

**Do you approve sending this email?**
ENDOFFILE
```

```bash
# Verify created
ls -lh AI_Employee_Vault/Pending_Approval/send_proposal.md
```

---

#### Step 2: List pending approvals

```bash
echo "=== PENDING APPROVALS ==="
ls -lh AI_Employee_Vault/Pending_Approval/
```

**You should see:** send_proposal.md waiting for your decision

---

#### Step 3: Approve it (simulate human approval)

```bash
# Move to Approved folder (simulating /manage-approval approve)
mv AI_Employee_Vault/Pending_Approval/send_proposal.md AI_Employee_Vault/Approved/
echo "✓ Approval granted"
```

---

#### Step 4: Let orchestrator process the approval

```bash
# Run orchestrator to detect approval
timeout 10 python3 src/orchestration/orchestrator.py
```

---

#### Step 5: Check what happened

```bash
echo "=== APPROVAL PROCESSED ==="
ls AI_Employee_Vault/Approved/ 2>/dev/null && echo "Still in Approved" || echo "✓ Moved to Done"
ls -lh AI_Employee_Vault/Done/send_proposal.md
```

```bash
# Check audit log for approval decision
echo ""
echo "=== APPROVAL AUDIT LOG ==="
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep -A5 "approval_decision" | tail -10
```

**You should see:** Log entry showing approval was granted and processed

---

## 🎯 REAL USE CASE #3: Multi-Task Processing

### What This Solves in Real Life:
- Multiple tasks come in throughout the day
- AI processes them all automatically
- Prioritizes by urgency
- Creates plans for each
- You review and approve as needed

### Let's See It Work:

#### Step 1: Create multiple tasks at once

```bash
# Task 1: Client follow-up
cat > AI_Employee_Vault/Needs_Action/task1_followup.md << 'ENDOFFILE'
---
id: "task_001"
type: "email"
source: "manual"
priority: "normal"
timestamp: "2026-01-15T19:00:00Z"
status: "pending"
metadata:
  task: "Follow up with client on proposal"
---

# Task: Client Follow-up
Follow up with Acme Corp on proposal status
ENDOFFILE
```

```bash
# Task 2: Social media post
cat > AI_Employee_Vault/Needs_Action/task2_linkedin.md << 'ENDOFFILE'
---
id: "task_002"
type: "social"
source: "manual"
priority: "low"
timestamp: "2026-01-15T19:01:00Z"
status: "pending"
metadata:
  task: "Post Q1 results to LinkedIn"
---

# Task: LinkedIn Post
Post about our successful Q1 results
ENDOFFILE
```

```bash
# Task 3: Urgent meeting prep
cat > AI_Employee_Vault/Needs_Action/task3_meeting.md << 'ENDOFFILE'
---
id: "task_003"
type: "task"
source: "manual"
priority: "high"
timestamp: "2026-01-15T19:02:00Z"
status: "pending"
metadata:
  task: "Prepare slides for tomorrow's board meeting"
---

# URGENT: Board Meeting Prep
Prepare presentation slides for tomorrow 9am board meeting
ENDOFFILE
```

```bash
# Verify all created
echo "=== TASKS CREATED ==="
ls -lh AI_Employee_Vault/Needs_Action/task*.md
```

---

#### Step 2: Process all tasks

```bash
# Run orchestrator
timeout 15 python3 src/orchestration/orchestrator.py
```

**What's happening:**
- AI detects all 3 tasks
- Processes them in priority order (high → normal → low)
- Creates plans for each
- Moves to Done/

---

#### Step 3: See the results

```bash
echo "=== TASKS PROCESSED ==="
ls AI_Employee_Vault/Needs_Action/task*.md 2>/dev/null && echo "Some still pending" || echo "✓ All processed"
```

```bash
echo ""
echo "=== PLANS CREATED ==="
ls -lh AI_Employee_Vault/Plans/
```

```bash
echo ""
echo "=== VIEW HIGH PRIORITY PLAN ==="
cat AI_Employee_Vault/Plans/*task_003*.md
```

---

## 🎯 REAL USE CASE #4: Dashboard Monitoring

### What This Solves in Real Life:
- You want to see system status at a glance
- How many pending actions?
- What's been processed today?
- Any errors?

### Let's See It Work:

```bash
echo "=== AI EMPLOYEE DASHBOARD ==="
cat AI_Employee_Vault/Dashboard.md
```

**You should see:**
- System status
- Watcher states
- Pending action count
- Recent activity
- Today's statistics

---

## 🎯 REAL USE CASE #5: Complete Audit Trail

### What This Solves in Real Life:
- Compliance requirements
- "What did the AI do today?"
- "When was that email sent?"
- Complete audit trail

### Let's See It Work:

```bash
echo "=== TODAY'S ACTIVITY ==="
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool
```

```bash
echo ""
echo "=== ACTIVITY SUMMARY ==="
echo "Total actions: $(cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json 2>/dev/null | grep -c action_type || echo 0)"
echo "Plans created: $(cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json 2>/dev/null | grep -c create_plan || echo 0)"
echo "Approvals: $(cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json 2>/dev/null | grep -c approval_decision || echo 0)"
```

---

## 📊 Summary: What You Just Saw

### Use Case 1: Email Management
✓ AI detected urgent client email
✓ Created action plan automatically
✓ Identified need for approval
✓ Logged everything

### Use Case 2: Approval Workflow
✓ Created approval request
✓ You approved it
✓ AI processed approval
✓ Logged decision

### Use Case 3: Multi-Task Processing
✓ Handled 3 tasks simultaneously
✓ Prioritized by urgency
✓ Created plans for each
✓ Processed efficiently

### Use Case 4: Dashboard
✓ Real-time system status
✓ Activity tracking
✓ Error monitoring

### Use Case 5: Audit Trail
✓ Complete activity log
✓ Compliance-ready
✓ Searchable history

---

## 🚀 Real-World Value

**Before AI Employee:**
- Manually check email every 30 min
- Miss urgent messages
- No prioritization
- No audit trail
- Forget follow-ups

**After AI Employee:**
- 24/7 monitoring
- Automatic prioritization
- Safety approvals
- Complete audit trail
- Never miss important tasks

---

## 💡 Next Steps

1. **Run these tests** to see it work
2. **Configure real Gmail** to monitor your actual inbox
3. **Set up WhatsApp** to monitor messages
4. **Customize** approval thresholds
5. **Deploy with PM2** for production

---

## ❓ Questions?

- **"How do I connect real Gmail?"** → See TESTING_GUIDE.md section on Gmail setup
- **"How do I customize behavior?"** → Edit AI_Employee_Vault/Company_Handbook.md
- **"How do I deploy for real?"** → Install PM2, run `pm2 start ecosystem.config.js`

---

## 🎯 The Bottom Line

This system is your **24/7 AI assistant** that:
- Monitors all your communication channels
- Prioritizes what's important
- Creates action plans
- **Asks for your approval** on sensitive actions
- Executes after approval
- Logs everything for compliance

**You focus on decisions. AI handles execution.**
