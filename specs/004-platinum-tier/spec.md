---
title: "Platinum Tier - Hackathon 0 Compliance"
short_name: platinum-tier
tier: platinum
feature_number: 004
ratified: 2026-01-20
last_amended: 2026-02-15
status: active
---

# Platinum Tier: Always-On Cloud + Local Executive

## User Description

Operate a hackathon-compliant Digital FTE where cloud and local agents share a synced vault, with strict HITL controls and MCP-based external actions.

## User Scenarios

### Scenario A: Cloud Draft, Local Execute (Email)
1. Email arrives while local machine is offline
2. Cloud agent triages and writes draft approval in `Pending_Approval/<domain>/`
3. Local user approves after returning
4. Local agent executes send via MCP
5. Action and plan move to `Done/`, with audit logs recorded

### Scenario B: Social Drafts and Final Post
1. Cloud drafts social content (Facebook/Instagram/Twitter/LinkedIn)
2. Human approves in UI or by moving file to `Approved/`
3. Local agent posts exactly approved content via MCP
4. Action is logged and archived in `Done/`

### Scenario C: Odoo Cloud + Local Approval
1. Cloud Odoo sync obtains draft accounting state
2. Posting invoices/payments requires local approval
3. Local executes approved posting through Odoo MCP
4. Logs preserve full action history

## Success Criteria

- Cloud orchestrator can run continuously and write drafts/signals.
- Local orchestrator is the only executor of approved external actions.
- Claim-by-move avoids duplicate ownership in synced vault workflows.
- Dashboard remains local single-writer with cloud signals merged by local.
- Odoo cloud deployment includes HTTPS, backups, and health monitoring artifacts.
- Platinum gate flow passes: cloud draft -> local approve -> MCP execute -> done + logs.

## Functional Requirements

### FR-001: Vault-First State Machine
- `AI_Employee_Vault/` is system of record.
- State transitions use folders:
  - `Needs_Action/` -> `In_Progress/<agent>/` -> `Pending_Approval/` -> `Approved|Rejected` -> `Done/`

### FR-002: Cloud/Local Work-Zone Specialization
- Cloud role: triage + draft-only workflows for email/social/accounting.
- Local role: approvals, WhatsApp/banking sessions, and final send/post/payment actions.
- Role behavior is controlled by `AGENT_ROLE`, `AGENT_ID`, and strict ownership policy.

### FR-003: Claim-by-Move Delegation
- First agent to move from `Needs_Action` to `In_Progress/<agent>/` owns the item.
- Other agents skip already-claimed work.

### FR-004: HITL For Sensitive Actions
- Sensitive actions are never executed from pending state.
- Execution requires explicit move to `Approved/`.
- Rejections are logged and not executed.

### FR-005: MCP Action Layer
- External side effects execute via MCP servers:
  - Email MCP
  - Social MCP
  - Odoo MCP
- `DRY_RUN` and `DEV_MODE` must be supported.

### FR-006: Odoo Cloud Deployment Controls
- Odoo stack must include:
  - cloud deployment compose
  - HTTPS proxy config
  - automated backup service
  - health-check script

### FR-007: Ralph Wiggum Persistence Loop
- Persistent loop must iterate orchestration cycles until completion condition or max iterations.
- Loop state/history must be recorded in vault folders.

### FR-008: Audit Logging and Traceability
- All approval decisions and executed actions are logged with timestamps and outcome.
- Heartbeat file enables liveness checks.

### FR-009: Web UI Operational Surface
- Local dashboard supports:
  - approvals list + approve/reject actions
  - social draft queueing
  - orchestrator liveness status
  - domain-aware file operations

### FR-010: Platinum Demo Gate
- Minimum gate:
  - local offline
  - cloud drafts approval
  - local approves and executes via MCP
  - logs written
  - task moved to `Done/`

## Non-Goals

- Replacing vault handoffs with A2A messaging (optional phase 2)
- Removing HITL for sensitive actions
