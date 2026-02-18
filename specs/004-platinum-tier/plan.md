# Implementation Plan: Platinum Tier (Hackathon 0)

**Date**: 2026-02-15  
**Spec**: [spec.md](spec.md)

## Summary

Implement full Platinum requirements with a cloud draft agent and local executive agent sharing a vault-based workflow. All sensitive actions remain HITL-gated and execute via MCP only after local approval.

## Architecture

### Components

- **Vault**: `AI_Employee_Vault/`
  - Folder state machine with domain subfolders
  - Claim-by-move queue using `In_Progress/<agent>/`
- **Cloud Agent**: `AGENT_ROLE=cloud`
  - Processes cloud-owned `Needs_Action` items
  - Drafts approvals into `Pending_Approval/<domain>/`
  - Writes signals for local merge
- **Local Agent**: `AGENT_ROLE=local`
  - Merges signals and updates dashboard
  - Handles approvals and executes approved external actions
- **Dashboard**: `dashboard/`
  - Domain-aware management UI
  - Approval operations
  - Orchestrator heartbeat visibility
- **MCP Layer**:
  - `mcp-servers/email-mcp/index.js`
  - `mcp-servers/social-mcp/index.js`
  - `deployment/cloud/odoo-mcp.js`
- **Cloud Odoo Stack**:
  - `deployment/cloud/docker-compose.odoo.yml`
  - `deployment/cloud/config/Caddyfile`
  - `deployment/cloud/healthcheck_odoo.sh`

## Process Model

### Local
1. `START_DASHBOARD.bat`
2. `START_BRAIN_LOCAL.bat` (or PM2 local app)

### Cloud
1. `pm2 start deployment/cloud/ecosystem.config.js`
2. optional `docker compose --env-file .env.cloud -f deployment/cloud/docker-compose.odoo.yml up -d`

## Key Flows

### Cloud Draft -> Local Approve -> MCP Execute

1. Cloud claims owned action from `Needs_Action/`.
2. Cloud creates plan + draft in `Pending_Approval/<domain>/`.
3. Human approves by moving to `Approved/<domain>/` (dashboard or file move).
4. Local executes via MCP and logs action.
5. Item and plan move to `Done/`.

### Dashboard Single Writer

- Cloud writes markdown updates to `Signals/`.
- Local agent merges signals during dashboard updates.
- Only local updates `Dashboard.md`.

## Validation Strategy

### Automated Gate

- `scripts/platinum_demo_gate.py`
  - simulates local offline and cloud draft cycle
  - validates approval and execution lifecycle
  - verifies logs and completion markers

### Unit Safety

- `tests/unit/test_approval_manager.py`
  - content extraction from `## Content`
  - exact approved content posted to MCP tool call

## Configuration

Core runtime env keys:

- `AGENT_ROLE`, `AGENT_ID`, `STRICT_WORK_ZONES`
- `WATCHER_*_ENABLED` toggles
- `DRY_RUN`, `DEV_MODE`, `REASONING_ENGINE`
- `PYTHON_EXE` (optional)
- cloud-specific values in `.env.cloud`
