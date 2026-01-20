# Platinum Tier Demo Video Script

## Overview
Demonstrate the dual-agent Cloud + Local Executive architecture for AI Employee

**Duration**: ~5-7 minutes

---

## Act I: Introduction (0:00-0:45)

### Opening Scene
**Visual**: Split screen showing two terminals - left "Cloud VM", right "Local Machine"

**Narration**:
"Welcome to the Platinum Tier of the Personal AI Employee. In this demonstration, we'll showcase the dual-agent architecture that separates draft generation in the cloud from approval and execution on your local machine."

**On Screen**:
- Show `AI_Employee_Vault` structure
- Point out `Cloud_Status.md` and `Dashboard.md`
- Highlight deployment folders (`deployment/cloud/`, `deployment/local/`)

---

## Act II: Cloud Agent - Email Drafting (0:45-2:30)

### Scene 1: Incoming Email
**Visual**: Show sample email in Gmail interface

**Demo Steps**:

```bash
# Show email action in Needs_Action
cat AI_Employee_Vault/Needs_Action/email_client_inquiry.yaml
```

**Expected Output**:
```yaml
---
action_id: email_client_001
type: email
source: gmail
priority: high
---
Client asking about project timeline
```

### Scene 2: Cloud Watcher Detection
**Demo**:
```bash
# Start cloud email watcher
python3 src/watchers/cloud_email_watcher.py AI_Employee_Vault/
```

**Expected Output**:
```
✓ Found email action: email_client_001
✓ Created DRAFT action: AI_Employee_Vault/Needs_Action/email_draft_20260123...
```

### Scene 3: Draft Generation
**Visual**: Show created draft file

```bash
# Show draft creation
cat AI_Employee_Vault/Pending_Approval/email_draft_*.yaml
```

**Key Points**:
- Highlight `DRAFT_MODE: true`
- Show **"HANDOVER REQUIRED"** notice
- Point out `requires_approval: true`
- Emphasize: **NO EMAIL SENT**

---

## Act III: Vault Sync (2:30-3:15)

### Scene: Syncthing in Action

**Visual**: Show Syncthing web UI with sync in progress

**Narration**:
"The draft email is now being synchronized from the cloud VM to the local machine via Syncthing. This encrypted sync happens securely without exposing credentials."

**Demo**:
```bash
# Show sync status (from status-mcp.mcp)
echo "Sync complete: Pending_Approval/email_draft_..."
```

**Key Points**:
- Show `<30s sync latency`
- Highlight `.gitignore-sync` exclusions
- Note no secrets in sync

---

## Act IV: Local Agent - Approval (3:15-4:30)

### Scene 1: Local Agent Detection
**Demo**:
```bash
# Show local approval handler scanning
python3 src/handlers/local_approval.py AI_Employee_Vault/ --scan
```

**Expected Output**:
```
Found 1 pending drafts:
  - email_draft_20260123_103045.yaml
```

### Scene 2: Review and Approval
**Demo**:
```bash
# Review draft
cat AI_Employee_Vault/Pending_Approval/email_draft_*.yaml
```

**Visual**: Focus on email content, recipient, subject

**Narration**:
"The local agent has detected a draft requiring approval. This is the Human-in-the-Loop checkpoint. Let's review the email before sending."

**Interactive Approval**:
```bash
# Process with approval
python3 src/handlers/local_approval.py AI_Employee_Vault/
```

**User Input**: "yes"

**Expected Output**:
```
Reviewing draft: email_draft_20260123_103045.yaml
To: client@example.com
Subject: Re: Project Timeline Inquiry

✓ Email sent successfully to client@example.com
✓ Draft moved to Approved folder
```

---

## Act V: Odoo Workflow Demo (4:30-5:30)

### Scene 1: Cloud Draft Report
**Demo**:
```bash
# Run in draft mode on cloud
python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft draft-report
```

**Expected Output**:
```
✓ Connected to Odoo (draft mode)
Generating draft invoice report...
✓ Report generated: AI_Employee_Vault/Reports/draft_invoices_20260123.csv
  Total invoices: 3
```

**Visual**: Show CSV report with draft invoices

### Scene 2: Local Approval for Posting
**Demo**:
```bash
# Switch to live mode (local)
python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode live post 15
```

**Expected Output**:
```
✓ Connected to Odoo (live mode)
Invoice 15 validated successfully
✓ Approval request created: Pending_Approval/invoice_15_approval.yaml
  Manual approval needed for invoice 15
```

### Scene 3: Post Invoice
**Narration**:
"The cloud agent validated the invoice, but posting requires local approval. After review, the local agent approves and posts the invoice."

**Demo**:
```bash
# Show approval file
cat AI_Employee_Vault/Pending_Approval/invoice_15_approval.yaml

# Approve and post
python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode live post 15 --no-approval
```

**Key Focus**: Show audit log in `Logs/` folder

---

## Act VI: Conflict Resolution (5:30-6:15)

### Scene: Dual-Agent Simulation

**Demo**:
```bash
# Create action both agents can see
echo '---\naction_id: race_condition_test\n---\n' > AI_Employee_Vault/Needs_Action/race_test.yaml

# Simulate two agents trying to claim
python3 deployment/vault-sync/claim-task.py AI_Employee_Vault/ cloud-agent-001 race_test.yaml &
python3 deployment/vault-sync/claim-task.py AI_Employee_Vault/ local-agent-001 race_test.yaml &
wait
```

**Narration**:
"In a rare edge case, both agents might see the same action before sync completes. Our claim-by-move validator prevents double-processing."

**Show Result**:
- Only one agent successfully claims
- Atomic move prevents both from processing
- Conflict detected and logged

---

## Act VII: Dashboard & Summary (6:15-6:45)

### Scene: Status Dashboard
**Demo**:
```bash
# Show cloud status
cat AI_Employee_Vault/Cloud_Status.md

# Show main dashboard
cat AI_Employee_Vault/Dashboard.md
```

**Visual**: Show both dashboards in split view

**Key Metrics to Highlight**:
- Cloud: Drafts created, Sync status
- Local: Approvals processed, Emails sent, Invoices posted
- Both: Zero conflicts, <30s sync latency

---

## Act VIII: Conclusion (6:45-7:00)

### Recap
**On Screen**:
```
✓ Cloud: Draft generation for emails and invoices
✓ Vault: Secure sync with Syncthing
✓ Local: Approval and execution
✓ Safety: Atomic claim-by-move prevents conflicts
✓ Security: No secrets in cloud, HITL mandatory
```

### Call to Action
**Narration**:
"The Platinum Tier AI Employee is now production-ready with enterprise-grade security, dual-agent architecture, and human approval workflows."

**Final Screen**:
- GitHub URL
- Documentation link
- Setup instructions for cloud VM

---

## Demo Prerequisites

Before recording, ensure:

1. Odoo VM running (or DRY_RUN=true)
2. Gmail credentials configured (or use mock files)
3. Email SMTP configured (or use mock sending)
4. Syncthing installed and configured
5. PM2 configured with ecosystem.config.js
6. All .env variables set

## Safety Measures

- Use DRY_RUN=true for most demos
- Have sample action files ready
- Pre-create approval requests for smooth flow
- Keep real credentials off-screen
- Use test Odoo instance or sandbox

---

## Notes for Recording

1. **Practice each segment** - Know the expected outputs
2. **Use terminal zoom** - Make text readable on video
3. **Highlight key sections** - Use terminal highlighting or mouse
4. **Speak slowly and clearly** - Complex architecture
5. **Pause for emphasis** - On security/HITL points
6. **Show file paths** - Help viewers orient themselves
7. **Use real examples** - But anonymize client data

## After Recording

- Post to YouTube with timestamps
- Link from README.md
- Create GIF for README
- Share on LinkedIn with commentary
