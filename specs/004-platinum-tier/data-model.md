# Platinum Tier Data Model (Vault + Approvals)

This document describes the data artifacts that the current implementation reads/writes.

## Vault Folders (State Machine)

- `AI_Employee_Vault/Pending_Approval/`: created by UI/skills; waiting for a human decision
- `AI_Employee_Vault/Approved/`: human-approved; orchestrator executes
- `AI_Employee_Vault/Rejected/`: human-rejected; orchestrator records and closes out
- `AI_Employee_Vault/Done/`: completed approvals/actions

## Social Approval File (Markdown)

Created by the dashboard social API when queueing a post.

Path:
- `AI_Employee_Vault/Pending_Approval/SOCIAL_<PLATFORM>_<TIMESTAMP>_<N>.md`

Frontmatter fields (subset):
- `type: social`
- `action: social_post`
- `platform: facebook|twitter|...`
- `requires_approval: true`
- `brain: qwen|manual`
- `qwen_prompt: |` (optional multi-line)

Body fields:
- `## Content`
- Post text (plain text; what the human is approving)
- `*This post requires approval before posting*` (note line)

Execution rule:
- If `## Content` exists, the orchestrator posts that content exactly after approval.

## Invoice Posting Approval File (YAML Frontmatter + Markdown Body)

Created by the Odoo accounting script when posting in live mode with approval required.

Path:
- `AI_Employee_Vault/Pending_Approval/invoice_<ID>_approval.yaml`

YAML frontmatter fields (subset):
- `type: invoice_posting`
- `invoice_id: <int>`
- `mode: live`
- `action: post`
- `requires_approval: true`

Body:
- Human-readable summary and instructions to approve/reject by moving the file.

## Orchestrator Heartbeat (JSON)

Written by the orchestrator so the dashboard can display liveness.

Path:
- `AI_Employee_Vault/Logs/orchestrator_heartbeat.json`

Fields:
- `timestamp` (UTC ISO-like string)
- `pid` (process id)
- `poll_interval_seconds`

## Audit Logs (JSON Lines)

The orchestrator and subsystems write structured audit logs to:
- `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

Format:
- One JSON object per line (JSONL), including:
  - `timestamp`, `level`, `message`, `logger`
  - `action_type`, `actor`, `target`, `result`
  - `details` and `parameters` (sanitized)

