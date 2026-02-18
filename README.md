# Daniel's FTE (Digital FTE)

Hackathon 0 Platinum implementation: cloud draft agent + local executive agent, coordinated by a vault-first workflow with strict HITL.

## Core Model

- Cloud role (`AGENT_ROLE=cloud`): triage and draft-only outputs.
- Local role (`AGENT_ROLE=local`): approvals, sensitive local channels, final MCP execution.
- State machine:
  - `Needs_Action/<domain>/`
  - `In_Progress/<agent>/` (claim-by-move)
  - `Pending_Approval/<domain>/`
  - `Approved|Rejected/<domain>/`
  - `Done/`
- External actions are executed only through MCP servers.

## Project Layout

```text
AI_Employee_Vault/
  Needs_Action/
  In_Progress/
  Plans/
  Pending_Approval/
  Approved/
  Rejected/
  Signals/
  Done/
  Logs/

dashboard/                          # Next.js operator UI
src/orchestration/orchestrator.py   # Role-aware orchestrator
mcp-servers/email-mcp/index.js
mcp-servers/social-mcp/index.js
deployment/cloud/odoo-mcp.js
deployment/cloud/docker-compose.odoo.yml
deployment/cloud/config/Caddyfile
```

## Local Quick Start (Windows)

1. Install deps

```powershell
python -m pip install -e .
python -m playwright install chromium
```

2. Configure `.env` from `.env.example`

3. Start dashboard

```powershell
START_DASHBOARD.bat
```

4. Start local agent

```powershell
START_BRAIN_LOCAL.bat
```

5. Start cloud agent (dev mode)

```powershell
START_BRAIN_CLOUD.bat
```

## Platinum Gate Validation

```powershell
RUN_PLATINUM_DEMO_GATE.bat
```

Expected flow: cloud draft -> local approval -> MCP execution -> audit logs -> `Done/`.

Structural checklist:

```powershell
RUN_HACKATHON_REQUIREMENTS_CHECK.bat
```

## Cloud Deployment (Odoo + HTTPS + Backup + Health)

See `deployment/cloud/README.md`.

## Documentation

- Architecture: `docs/architecture.md`
- Lessons learned: `docs/lessons-learned.md`
- Hackathon compliance mapping: `docs/hackathon0-compliance.md`
- Vault sync playbook: `docs/guides/vault-sync-guide.md`

## Security Notes

- Keep secrets in `.env`/OS secret stores only.
- Keep `DRY_RUN=true` for initial validation.
- Do not sync secrets/session folders to cloud sync targets.
