# Data Models

## 1. Action File (Input)
**Location**: `AI_Employee_Vault/Needs_Action/`
**Format**: Markdown with YAML frontmatter

```yaml
---
# Unique identifier
id: "act_12345678"
# Type of event detected
type: "email" | "message" | "file_drop" | "schedule"
# Source system
source: "gmail" | "whatsapp" | "linkedin" | "cron"
# Priority level
priority: "urgent" | "normal" | "low"
# Detection timestamp
timestamp: "2026-01-15T14:30:00Z"
# Current processing status
status: "pending" | "processing" | "completed" | "failed"
# Metadata bag (source specific)
metadata:
  sender: "client@example.com"
  subject: "Invoice needed"
  thread_id: "gym-123"
---

# Content
[Full content or snippet of the message/event]

# Context
[Additional context extracted by watcher]
```

## 2. Plan File (Execution)
**Location**: `AI_Employee_Vault/Plans/`
**Format**: Markdown

```yaml
---
id: "plan_98765432"
action_ref: "act_12345678"
created: "2026-01-15T14:32:00Z"
status: "planning" | "in_progress" | "blocked" | "completed" | "error"
---

# Objective
Create and send invoice #1001 to Client X for $500.

# Risk Assessment
- **Sensitivity**: High (Financial document)
- **Approvals Required**: Email send

# Execution Steps
- [x] 1. Generate Invoice PDF (Completed 14:33)
- [ ] 2. Draft Email to Client (Pending)
- [ ] 3. **APPROVAL**: Send Email (Blocked: requires approval)
- [ ] 4. Log Transaction (Pending)

# Results
[Execution logs/outputs appended here]
```

## 3. Approval Request (HITL)
**Location**: `AI_Employee_Vault/Pending_Approval/`
**Format**: Markdown

```yaml
---
id: "appr_55555"
type: "approval"
action_type: "send_email"
created: "2026-01-15T14:35:00Z"
expires: "2026-01-16T14:35:00Z"
status: "pending"
context:
  plan_id: "plan_98765432"
  step_index: 3
---

# Request: Send Email to New Contact

**Reason**: Sending financial document to external recipient.

## Action Details
- **To**: client@example.com
- **Subject**: Invoice #1001
- **Attachments**: invoice_1001.pdf

## Preview
Dear Client,
Please find attached...

## Instructions
- Move to `Approved/` to execute.
- Move to `Rejected/` to cancel.
```

## 4. Audit Log (System Record)
**Location**: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
**Format**: JSON Array of Objects

```json
{
  "timestamp": "2026-01-15T14:30:00Z",
  "action_type": "watcher_detect",
  "actor": "gmail_watcher",
  "target": "gmail_api",
  "result": "success",
  "parameters": {
    "message_count": 1
  },
  "details": {
    "action_id": "act_12345678"
  }
}
```
