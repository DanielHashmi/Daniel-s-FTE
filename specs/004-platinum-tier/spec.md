---
title: Platinum Tier - Cloud + Local Executive AI Employee
short_name: platinum-tier
tier: platinum
feature_number: 004
ratified: 2026-01-20
last_amended: 2026-01-20
status: draft
---

# Platinum Tier: Always-On Cloud + Local Executive (Production-ish AI Employee)

## User Description
Build the Platinum Tier as defined in the hackathon document: Deploy the AI Employee on cloud 24/7 with work-zone specialization between Cloud (draft-only actions) and Local (approval/execution). Use synced vault for communication, deploy Odoo on cloud, and demonstrate offline-online handover workflow.

## User Scenarios

### Primary Scenario: Offline Email Processing Handover
1. Email arrives while Local is offline
2. Cloud Agent triages email, drafts reply, creates approval file in synced vault
3. Local Agent (when online) presents approval request to user
4. User approves via file move to /Approved
5. Local Agent executes send via MCP, logs to audit, moves to /Done
6. Both agents see completion via vault sync

### Secondary Scenario: Odoo Accounting Workflow
1. Cloud Agent syncs draft invoices from cloud Odoo instance
2. Creates approval requests for posting/payments
3. Local Agent handles final approvals and execution
4. Audit trail maintained in shared vault

### Edge Scenario: Conflict Resolution
1. Both agents detect same task simultaneously
2. Claim-by-move rule (/In_Progress/<agent>/) prevents double-work
3. Losing agent ignores task, winning agent completes

## Success Criteria
- Cloud deployment runs 24/7 with 99.9% uptime (PM2 monitoring)
- Vault sync completes <30s with Git/Syncthing
- Offline-online handover completes end-to-end in <5min user time
- No secret data synced (credentials stay local/cloud separated)
- Odoo MCP integration supports draft/live modes
- 100% task ownership via claim-by-move (no double-processing)
- Demo video shows complete email workflow across cloud/local boundary

## Functional Requirements

### FR-001: Cloud Deployment Infrastructure
- Deploy orchestrator, watchers, MCP servers on cloud VM (Oracle Free Tier)
- PM2 process manager for all services with auto-restart
- Health monitoring dashboard in vault (/Cloud_Status.md)
- HTTPS for Odoo instance with SSL cert (Let's Encrypt)

### FR-002: Work-Zone Specialization
- Cloud scope: Email triage/drafts, social drafts/scheduling, Odoo draft syncs
- Local scope: Approvals, WhatsApp, banking/payments, final executions
- Enforced via domain-specific folders: /Needs_Action/cloud-email/, /Needs_Action/local-payments/

### FR-003: Synced Vault Communication (Phase 1)
- Bidirectional vault sync using Git (push/pull every 30s) or Syncthing
- Communication via structured folders:
  | Folder | Purpose | Writer | Reader |
  |--------|---------|--------|--------|
  | /Needs_Action/cloud-* | Cloud-detected tasks | Cloud | Local |
  | /Needs_Action/local-* | Local-detected tasks | Local | Cloud |
  | /Pending_Approval/* | Approval requests | Both | Human/Local |
  | /In_Progress/<agent>/ | Task ownership claim | Agent | Both |
  | /Updates/cloud | Cloud status updates | Cloud | Local |
- Claim-by-move rule: Move task file to own it exclusively

### FR-004: Odoo Cloud Deployment
- Odoo Community 19+ on cloud VM with Accounting, Sales modules
- JSON-RPC API exposed via HTTPS
- Automated daily backups to object storage
- MCP server integration for draft/live accounting actions
- Draft mode: Read/sync only, no writes
- Live mode: Full CRUD with Local approval

### FR-005: Security & Data Isolation
- Secrets never sync (.env, tokens, WhatsApp sessions, banking creds stay environment-specific)
- Vault sync excludes: node_modules, .git, secrets folders
- Audit log of all sync operations (file moved/created/deleted)
- Single-writer rule for Dashboard.md (Local only)

### FR-006: Demo Workflow Validation
- End-to-end test: Email → Cloud draft → Local approval → Execution
- Verify no double-processing via claim-by-move
- Measure sync latency <30s, handover time <5min

## Key Entities

### CloudAgent
- Capabilities: Email triage, social drafts, Odoo draft sync
- Owned folders: /Needs_Action/cloud-*, /Updates/cloud
- Constraints: No WhatsApp, no banking, no final executions

### LocalAgent
- Capabilities: Approvals, WhatsApp, banking, final executions
- Owned folders: /Needs_Action/local-*, Dashboard.md writes
- Constraints: No cloud deploys, no always-on operation

### SyncedVault
- State: Markdown files only, no secrets/binaries
- Sync mechanism: Git or Syncthing
- Conflict resolution: Claim-by-move + last-write-wins for status files

## Assumptions
- Oracle Cloud Free Tier VM available (2 instances max)
- Git/Syncthing sync reliable over internet
- Human user approves within 24h of requests
- Odoo self-hosted (no SaaS)

## Risks & Mitigations
- **Risk**: Sync conflicts → Mitigation: Claim-by-move + unique filenames
- **Risk**: Secrets leak → Mitigation: .gitignore + sync exclusions
- **Risk**: Cloud downtime → Mitigation: Local fallback + offline queue

## Non-Goals
- Direct agent-to-agent messaging (Phase 2)
- Multi-cloud/multi-local scaling
- Real-time sync (<5s latency)
