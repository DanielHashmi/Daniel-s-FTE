# Phase 0: Research Findings

## 1. Process Management Architecture
**Decision**: Use PM2 with `ecosystem.config.js` and bash wrapper scripts.
**Rationale**: PM2 provides built-in autorestart, logging, and monitoring (FR-009, FR-010).
**Alternatives**:
- `supervisord`: Good but configuration is less dynamic than JS-based PM2 config.
- `systemd`: Too complex for user-level installation and management.
- Custom python loop: Re-inventing the wheel for process lifecycle.

**Critical Implementation Detail**: PM2 uses system Python by default. Wrapper scripts (`run-orchestrator.sh`, `run-mcp-email.sh`, `run-mcp-social.sh`) activate the virtual environment and set PYTHONPATH before executing Python code.

## 2. Orchestration Pattern
**Decision**: `orchestrator.py` as a master loop running under PM2.
**Function**:
- Monitors file system events (or polls) for `Needs_Action` and `Pending_Approval` changes.
- Triggers `/process-inbox` skill when action files appear.
- Monitors `Completed` actions to trigger next steps in Plans.
- Runs `watchdog` logic implies checking PM2 status (via `pm2 list` or API).
**Rationale**: Centralized control logic compliant with FR-035. Separates "doing" (Skills) from "coordinating" (Orchestrator).

**Implementation**: Watchers run as daemon threads within the orchestrator process, not as separate PM2 processes. This simplifies deployment and reduces resource usage.

## 3. MCP Server Integration
**Decision**: Build standalone Python MCP servers (`email_server.py`, `social_server.py`) using FastMCP library.
**Pattern**:
- Servers start as PM2 processes via wrapper scripts.
- Skills (`email-ops`, `social-ops`) connect to them via MCP Client (stdio or SSE).
- *Fallback*: Skills currently implement direct logic/DRY_RUN.
- *Refinement*: For Silver Tier, we will prioritize direct logic in Skills for simplicity (complying with "All AI functionality as Agent Skills" FR-044) BUT wrapping them as MCP servers is required by FR-027.
- *Hybrid Approach*: The Skill script *is* the client. The Server runs in background.

**Dependencies**: Requires `fastmcp` and `mcp` packages installed in virtual environment.

## 4. Human-In-The-Loop (HITL) storage
**Decision**: File-based state machine in `AI_Employee_Vault`.
- `Pending_Approval/`: Request files.
- `Approved/`: User moves files here to approve.
- `Rejected/`: User moves files here to reject.
**Rationale**: Non-blocking, simpler than an interactive CLI prompts, leverages OS file explorer as UI (FR-193).

## 5. Security - Credentials
**Decision**: `.env` file loaded by `python-dotenv`.
**Key names**: `GMAIL_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `OPENAI_API_KEY` (if used).
**Rationale**: Standard practice, keeps secrets out of code (FR-008 implies logging errors, but implies we handle credentials safely).

**Gmail OAuth**: Requires `credentials.json` (OAuth client) and `gmail_token.json` (user token). Both excluded from git.

## 6. Resolved Clarifications
- **Orchestrator vs Watchdog**: Orchestrator performs coordination; Watchdog (FR-013) is a specific function (possibly sub-thread or separate script) ensuring health. Decision: Watchdog runs as separate thread inside Orchestrator or separate PM2 process. We will implement it as a function within `orchestrator.py` that runs every 60s.

## 7. Deployment Architecture (Production Lessons)

### System Components
- **Orchestrator**: Main coordinator managing watcher threads, plan generation, approval workflow, dashboard updates, and health checks
- **Watchers**: Gmail, WhatsApp, LinkedIn (run as daemon threads within orchestrator)
- **MCP Servers**: Email and Social servers (separate PM2 processes)

### Resource Usage (Observed)
- ai-orchestrator: 40-50 MB RAM, <1% CPU idle
- mcp-email: 50-60 MB RAM
- mcp-social: 50-60 MB RAM
- Total: ~150 MB RAM

### Critical Dependencies
- **Python packages**: `watchdog`, `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `pyyaml`, `python-dotenv`, `playwright`, `fastmcp`, `mcp`
- **System libraries** (Linux/WSL2): `libnspr4` (required for Playwright Chromium)
- **Playwright browsers**: Chromium (installed via `playwright install chromium`)

### Common Issues Resolved
1. **ModuleNotFoundError**: Solved by wrapper scripts that activate venv and set PYTHONPATH
2. **Logger.warning() missing**: AuditLogger only has `info()` and `error()` methods
3. **Vault path access**: Use `vault.root` not `vault.dirs["root"]`
4. **Missing dependencies**: Install all packages in venv, not system Python

## 8. Architecture Decisions

### Watcher Threading Model
**Decision**: Watchers run as daemon threads within orchestrator process.
**Rationale**: Simpler deployment, shared memory space, easier coordination.
**Alternative**: Separate PM2 processes per watcher (rejected due to complexity).

### Logging Architecture
**Decision**: Structured JSON logging to daily files (`Logs/YYYY-MM-DD.json`).
**Format**:
```json
{
  "timestamp": "ISO 8601",
  "level": "INFO|ERROR",
  "message": "...",
  "logger": "orchestrator|plan_manager|approval_manager",
  "action_type": "...",
  "actor": "...",
  "target": "...",
  "result": "success|failure",
  "parameters": {},
  "details": {}
}
```

### Dashboard Updates
**Decision**: Dashboard updated every 30 seconds by orchestrator.
**Content**: Watcher status, pending action count, recent activity, errors, timestamp.
**Location**: `AI_Employee_Vault/Dashboard.md`

## 9. Claude Code Reasoning Loop Integration (Critical)

**Decision**: Use Claude Code CLI (`claude -p`) as the reasoning engine for plan generation.

**Hackathon Requirement**: Per the hackathon guide: *"The Brain: Claude Code acts as the reasoning engine... It uses its File System tools to read your tasks and write reports."*

**Implementation**:
- `src/orchestration/claude_invoker.py`: Module that shells out to `claude` CLI
- `plan_manager.py`: Updated to use Claude invoker with template fallback

**Pattern**:
```text
Action File → claude_invoker.py → Claude Code CLI → Plan.md
                    │
                    └── Fallback to templates if CLI unavailable
```

**Key Features**:
1. **Rate Limiting**: Max 10 invocations per minute to prevent API abuse
2. **Timeout Handling**: 120 second timeout per invocation
3. **Graceful Fallback**: Template-based planning if Claude unavailable
4. **Context Injection**: Company_Handbook.md and Business_Goals.md passed to Claude
5. **Audit Logging**: All invocations logged with prompt, response, duration

**Why Claude Code CLI vs API**:
- **Hackathon Compliance**: Guide specifies "Claude Code" not "Claude API"
- **No API Key Management**: Uses existing Claude Code subscription
- **Local-First**: Keeps reasoning local to the user's machine
- **Cost Control**: User's existing subscription covers usage

**Alternative Considered**: Direct Anthropic API
- Rejected because hackathon guide specifically mentions "Claude Code"
- Would require separate API key management
- Less aligned with local-first philosophy
