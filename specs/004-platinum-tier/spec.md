---
title: "Platinum Tier - Local-First Digital FTE (Dashboard + Brain)"
short_name: platinum-tier
tier: platinum
feature_number: 004
ratified: 2026-01-20
last_amended: 2026-02-14
status: active
---

# Platinum Tier: Local-First Digital FTE (Current Repo Reality)

## User Description

Operate a local-first "Digital FTE" that:
- Provides a web UI to manage approvals and social drafts
- Uses a Python orchestrator to monitor the vault and execute approved actions
- Treats external/public actions as sensitive and requires explicit human approval
- Can generate and publish Facebook posts using Qwen (copy generation) + Playwright (browser automation)

## User Scenarios

### Scenario A: Create, Approve, Post to Facebook (Primary)
1. User opens the dashboard Social page
2. User generates a draft with Qwen (optional) and edits the content
3. User queues the post, creating an approval file in `AI_Employee_Vault/Pending_Approval/`
4. User approves in the UI (or moves the file to `AI_Employee_Vault/Approved/`)
5. Orchestrator posts the approved `## Content` to Facebook via Playwright
6. The approval file is moved to `AI_Employee_Vault/Done/` and an audit log entry is written

### Scenario B: Human-in-the-Loop Safety (Always-On)
1. A sensitive action is proposed (public post, invoice posting, etc.)
2. The system writes a clear approval request file
3. Nothing executes until the file is explicitly approved
4. Rejected approvals are not executed

### Scenario C: Orchestrator Liveness in the UI
1. Orchestrator runs locally
2. It writes a heartbeat file on a short interval
3. The dashboard shows whether the brain is currently running

## Success Criteria

- The dashboard runs locally and can view approvals, social drafts, and status.
- The orchestrator detects approved items within a short time window (seconds).
- For Facebook approvals, the system posts exactly what was approved (no regeneration after approval).
- `DRY_RUN=true` prevents live external actions (including browser posting).
- No secrets are committed: credentials are provided via environment variables / local session dirs.

## Functional Requirements

### FR-001: Vault-First Workflow (Local-First)
- The vault folder `AI_Employee_Vault/` is the source of truth for actions, approvals, and logs.
- Approval folders are used as the execution state machine:
  - `Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`

### FR-002: Web UI for Management
- A local dashboard provides:
  - Login gate (password-based)
  - Social post creation and queueing for approval
  - Approval review and approve/reject actions
  - Visibility into orchestrator running status

### FR-003: Orchestrator Executes Approved Items
- The orchestrator monitors `AI_Employee_Vault/Approved/` for `.md` and `.yaml` files.
- On successful execution it moves items to `AI_Employee_Vault/Done/`.
- On transient failures it retries with a backoff (without losing the approval file).

### FR-004: Facebook Posting via Qwen + Playwright
- Draft generation uses Qwen CLI locally.
- Publishing uses Playwright with a persistent session directory (`FACEBOOK_SESSION_DIR`).
- If the approved file contains `## Content`, that text is posted exactly.
- If no content exists, the system may generate then post (but this is not the normal UI flow).

### FR-005: Auditability and Safety Controls
- Every approval decision is logged with timestamp and file reference.
- Orchestrator liveness is observable via a heartbeat file in `AI_Employee_Vault/Logs/`.
- A global `DRY_RUN` mode exists for safe testing.

## Non-Goals (In This Repo As Implemented Today)

- Always-on cloud deployment, PM2-managed cloud services, Syncthing-based cloud/local handover.
- Multi-agent claim-by-move conflict resolution between cloud and local agents.
- Storing or syncing secrets (tokens, cookies, sessions) via git or vault sync.

