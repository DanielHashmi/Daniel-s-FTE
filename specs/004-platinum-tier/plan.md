# Implementation Plan: Platinum Tier (Local-First Dashboard + Brain)

**Date**: 2026-02-14  
**Spec**: [spec.md](spec.md)

## Summary

This repo's "Platinum Tier" implementation is centered on a single-machine, local-first loop:
- A Next.js dashboard creates and manages approval files inside `AI_Employee_Vault/`
- A Python orchestrator watches the vault and executes items that a human has approved

Cloud VM + sync handover is not the primary path in the current implementation.

## Architecture

### Components

- **Vault**: `AI_Employee_Vault/`
  - File-based state machine: `Pending_Approval/` -> `Approved/` or `Rejected/` -> `Done/`
- **Dashboard (UI + API)**: `dashboard/` (Next.js)
  - Reads/writes vault files (approvals, social drafts, status)
  - Shows orchestrator status from a heartbeat file
- **Orchestrator ("brain")**: `src/orchestration/orchestrator.py`
  - Runs watchers in background threads
  - Processes approvals quickly (Approved/ and Rejected/)
  - Writes liveness heartbeat

### Process Model

Two local processes are expected during normal operation:
1. `START_DASHBOARD.bat` (web UI)
2. `START_BRAIN.bat` (orchestrator)

## Key Flows

### Facebook: Qwen Draft -> Approval -> Playwright Post

1. Generate draft text with Qwen in the UI:
   - API: `dashboard/src/app/api/social/facebook/generate/route.ts`
   - Qwen spawn wrapper: `dashboard/src/lib/qwen.ts`
   - Invocation: `qwen -y --input-format text` with prompt passed via stdin
2. Queue a post for approval:
   - API: `dashboard/src/app/api/social/post/route.ts`
   - Writes a Markdown file into `AI_Employee_Vault/Pending_Approval/`
3. Approve:
   - Dashboard approval UI moves the file to `AI_Employee_Vault/Approved/`
4. Execute:
   - Orchestrator detects the approved file
   - Execution handler: `src/orchestration/approval_manager.py`
   - Posts the approved `## Content` via:
     - `src/social/facebook_qwen_poster.py --mode post --content "<approved content>"`

HITL guarantee is enforced at execution time: if a file contains approved `## Content`,
the orchestrator posts that content exactly (no regeneration after approval).

### Orchestrator Liveness (UI Status)

- Orchestrator writes `AI_Employee_Vault/Logs/orchestrator_heartbeat.json`
- Dashboard reads the heartbeat via `dashboard/src/app/api/social/accounts/route.ts`

## Configuration

Recommended `.env` keys (repo root, gitignored):

- `DRY_RUN=true|false`
- `REASONING_ENGINE=qwen|claude`
- `QWEN_PATH=qwen` (Windows often needs `qwen.cmd`)
- `FACEBOOK_COMPOSER_URL=...`
- `FACEBOOK_SESSION_DIR=facebook_session`
- `FACEBOOK_HEADLESS=true|false`
- `FACEBOOK_LOGIN_WAIT_SECONDS=600`
- `FACEBOOK_KEEP_OPEN_SECONDS=0`
- `FACEBOOK_BROWSER_CHANNEL=chrome` (optional)
- `DASHBOARD_PASSWORD=...` (dashboard login)
- `SESSION_SECRET=...` (dashboard session cookie signing)

## Verification / Acceptance Checks

1. Start dashboard and brain.
2. Confirm heartbeat updates: `AI_Employee_Vault/Logs/orchestrator_heartbeat.json`
3. Create a Facebook post in the UI and queue it for approval.
4. Approve it and confirm:
   - In dry-run mode: no browser opens, file moves to `Done/`.
   - In live mode: Playwright opens a persistent browser context and submits the post.

## Future Enhancements (Not Required For Current State)

- Add explicit UI controls to capture social sessions (Facebook/LinkedIn/WhatsApp).
- Strengthen the vault file schema validation (reject malformed approval files early).
- Expand tests for the social approval execution path (unit + E2E).

