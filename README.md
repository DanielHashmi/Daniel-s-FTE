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

High-level structure (see [CODEBASE_STRUCTURE.md](CODEBASE_STRUCTURE.md) for complete details):

```
bin/                                # Executable scripts & entry points
config/                             # Configuration files (.env variants)
src/                                # Main application source code
  ├── orchestration/               # Vault-based orchestrator
  ├── skills/                      # AI skill implementations
  ├── social/                      # Social media posting
  ├── watchers/                    # Input watchers
  └── mcp/                         # MCP server integrations
mcp-servers/                        # External MCP implementations
dashboard/                          # Next.js operator UI
deployment/                         # Cloud & Kubernetes configs
docker/                             # Container definitions
docs/                               # Documentation
specs/                              # Tier-based specifications
history/                            # Decision records & PHRs
session-data/                       # Browser sessions (gitignored)
.tmp/                               # Temporary runtime files (gitignored)

AI_Employee_Vault/                  # Core system state & workflow
  ├── Needs_Action/
  ├── In_Progress/
  ├── Pending_Approval/
  ├── Approved/
  ├── Rejected/
  ├── Done/
  ├── Plans/
  └── Logs/
```

## Local Quick Start (Windows)

1. Install dependencies

```powershell
python -m pip install -e .
python -m playwright install chromium
```

2. Configure environment from template

```powershell
Copy-Item config/.env.example .env
# Edit .env with your credentials
```

3. Start dashboard

```powershell
./bin/START_DASHBOARD.bat
```

4. Start local agent

```powershell
./bin/START_BRAIN_LOCAL.bat
```

5. Start cloud agent (dev mode)

```powershell
./bin/START_BRAIN_CLOUD.bat
```

## Validation & Testing

Verify Platinum Tier implementation:

```powershell
python scripts/platinum_demo_gate.py
```

Expected flow: cloud draft → local approval → MCP execution → audit logs → `Done/`.

Verify structural requirements:

```powershell
python scripts/check_hackathon_requirements.py
```

## Cloud Deployment (Odoo + HTTPS + Backup + Health)

See `deployment/cloud/README.md`.

## Documentation

- **Project Structure**: See [CODEBASE_STRUCTURE.md](CODEBASE_STRUCTURE.md) for detailed directory layout and file organization
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Lessons Learned**: [docs/lessons-learned.md](docs/lessons-learned.md)
- **Hackathon Compliance**: [docs/hackathon0-compliance.md](docs/hackathon0-compliance.md)
- **Vault Sync Guide**: [docs/guides/vault-sync-guide.md](docs/guides/vault-sync-guide.md)
- **Hackathon 0 Overview**: [docs/hackathon0-guide.md](docs/hackathon0-guide.md)

## Security Notes

- Keep secrets in `.env`/OS secret stores only.
- Keep `DRY_RUN=true` for initial validation.
- Do not sync secrets/session folders to cloud sync targets.
