# Personal AI Employee Architecture

This document captures the implemented system architecture across Bronze, Silver, Gold, and Platinum tiers.

## 1. Core Layers

### Perception (Watchers)
- Python watchers inherit `src/watchers/base.py`.
- Channels:
  - Gmail: `src/watchers/gmail.py`
  - WhatsApp: `src/watchers/whatsapp.py`
  - LinkedIn: `src/watchers/linkedin.py`
  - File drops: `src/watchers/filesystem.py`
  - Banking: `src/watchers/banking.py`
  - Odoo sync: `src/watchers/odoo.py`
- Output: action files in `AI_Employee_Vault/Needs_Action/<domain>/`.

### Reasoning (Plan + Draft)
- Plan generation:
  - `src/orchestration/plan_manager.py`
  - `src/orchestration/qwen_invoker.py` (primary in this repo)
  - `src/orchestration/claude_invoker.py` (optional fallback path)
- Cloud draft generation:
  - `src/orchestration/draft_manager.py`

### Action (MCP + HITL)
- Approval state machine:
  - `Pending_Approval` -> `Approved|Rejected` -> `Done`
- Local execution handlers:
  - `src/orchestration/approval_manager.py`
- MCP servers:
  - Email: `mcp-servers/email-mcp/index.js`
  - Social: `mcp-servers/social-mcp/index.js`
  - Odoo: `deployment/cloud/odoo-mcp.js`

## 2. Vault-First Workflow

`AI_Employee_Vault/` is the system of record:
- `Needs_Action/<domain>/`
- `In_Progress/<agent>/`
- `Plans/<domain>/`
- `Pending_Approval/<domain>/`
- `Approved/<domain>/`
- `Rejected/<domain>/`
- `Signals/`
- `Done/`
- `Logs/`

Claim-by-move ownership is enforced by the orchestrator:
- first mover from `Needs_Action` to `In_Progress/<agent>` owns the task.

## 3. Cloud + Local Specialization (Platinum)

- Cloud (`AGENT_ROLE=cloud`):
  - triage
  - create draft approvals
  - never execute final sensitive actions
- Local (`AGENT_ROLE=local`):
  - approval handling
  - final MCP sends/posts
  - single writer for dashboard updates

Strict mode:
- `STRICT_WORK_ZONES=true` in `src/orchestration/orchestrator.py`.

## 4. Reliability and Safety

- Process supervision:
  - PM2 app profiles in `ecosystem.config.js` and `deployment/cloud/ecosystem.config.js`
- Heartbeat:
  - `AI_Employee_Vault/Logs/orchestrator_heartbeat.json`
- Watchdog:
  - `src/orchestration/watchdog.py`
- Retry/backoff:
  - `src/utils/retry.py`
- Error recovery queues:
  - `Recovery_Queue`, `Quarantine`, `Alerts`

## 5. Odoo Deployment (Platinum)

Cloud Odoo stack:
- Compose: `deployment/cloud/docker-compose.odoo.yml`
- HTTPS proxy: `deployment/cloud/config/Caddyfile`
- Health check: `deployment/cloud/healthcheck_odoo.sh`
- Bootstrap docs: `deployment/cloud/README.md`

Accounting policy:
- Cloud accounting operations are draft-only.
- Local approval/execution required for posting invoices/payments.

## 6. UI Surfaces

- Web dashboard: `dashboard/` (approvals, social drafts, stats, liveness).
- Vault can be viewed/edited in Obsidian as local memory/operations board.
