# Hackathon 0 Compliance Checklist (Exact Tier Mapping)

Source: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`

Note: The source names Claude Code as the default executor. This repo uses Qwen as primary reasoning engine by user direction, with equivalent file-based reasoning workflow and optional Claude-path support.

## Bronze Tier: Foundation

- [x] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
  - `AI_Employee_Vault/Dashboard.md`
  - `AI_Employee_Vault/Company_Handbook.md`
- [x] One working watcher script (Gmail OR file system monitoring)
  - `src/watchers/gmail.py`
  - `src/watchers/filesystem.py`
- [x] Reasoning engine reads/writes vault
  - `src/orchestration/plan_manager.py`
  - `src/lib/vault.py`
- [x] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
  - `src/lib/vault.py` (`ensure_structure`)
- [x] AI functionality implemented as Agent Skills
  - `.claude/skills/`

## Silver Tier: Functional Assistant

- [x] All Bronze requirements plus
- [x] Two+ watchers (Gmail + WhatsApp + LinkedIn)
  - `src/watchers/gmail.py`
  - `src/watchers/whatsapp.py`
  - `src/watchers/linkedin.py`
- [x] Automatically post on LinkedIn about business
  - `scripts/create_linkedin_autopost_action.py`
  - `RUN_LINKEDIN_AUTOPOST_ACTION.bat`
  - `src/orchestration/draft_manager.py` + `src/orchestration/approval_manager.py`
- [x] Reasoning loop creates `Plan.md` files
  - `src/orchestration/plan_manager.py`
- [x] One working MCP server for external action (email)
  - `mcp-servers/email-mcp/index.js`
  - `src/mcp/stdio_client.py`
- [x] HITL approval workflow
  - `AI_Employee_Vault/Pending_Approval|Approved|Rejected|Done`
  - `src/orchestration/approval_manager.py`
  - `.claude/skills/manage-approval/`
- [x] Basic scheduling via cron/Task Scheduler
  - `.claude/skills/scheduler/scripts/main_operation.py`
  - `AI_Employee_Vault/Config/schedules.json`
- [x] AI functionality implemented as Agent Skills
  - `.claude/skills/`

## Gold Tier: Autonomous Employee

- [x] All Silver requirements plus
- [x] Full cross-domain integration (Personal + Business)
  - `src/lib/vault.py` (domain routing)
  - `src/watchers/base.py` (domain action files)
  - `.claude/skills/cross-domain-orchestrator/`
- [x] Odoo Community accounting integration via MCP (JSON-RPC)
  - `deployment/cloud/odoo-mcp.js`
  - `.claude/skills/odoo-accounting/scripts/main_operation.py`
  - `src/watchers/odoo.py`
- [x] Facebook + Instagram integration (post + summary)
  - Posting: `mcp-servers/social-mcp/index.js`
  - Summary: `.claude/skills/social-media-suite/scripts/main_operation.py --action summary`
- [x] Twitter/X integration (post + summary)
  - Posting: `mcp-servers/social-mcp/index.js`
  - Summary: `.claude/skills/social-media-suite/scripts/main_operation.py --action summary`
- [x] Multiple MCP servers for different action types
  - Email: `mcp-servers/email-mcp/index.js`
  - Social: `mcp-servers/social-mcp/index.js`
  - Odoo: `deployment/cloud/odoo-mcp.js`
- [x] Weekly business/accounting audit with CEO briefing
  - `.claude/skills/ceo-briefing/scripts/main_operation.py`
  - Output: `AI_Employee_Vault/Briefings/`
- [x] Error recovery and graceful degradation
  - `src/utils/retry.py`
  - `.claude/skills/error-recovery/`
  - `src/orchestration/watchdog.py`
- [x] Comprehensive audit logging
  - `src/lib/logging.py`
  - `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
- [x] Ralph Wiggum loop for persistent multi-step completion
  - `.claude/skills/ralph-wiggum-loop/scripts/main_operation.py`
  - `AI_Employee_Vault/Ralph_State/`, `AI_Employee_Vault/Ralph_History/`
- [x] Documentation of architecture and lessons learned
  - `docs/architecture.md`
  - `docs/lessons-learned.md`
- [x] AI functionality implemented as Agent Skills
  - `.claude/skills/`

## Platinum Tier: Always-On Cloud + Local Executive

- [x] All Gold requirements plus
- [x] Run AI Employee on cloud 24/7 (watchers + orchestrator + health)
  - PM2 profiles: `ecosystem.config.js`, `deployment/cloud/ecosystem.config.js`
  - Health: `src/orchestration/watchdog.py`, `deployment/cloud/healthcheck_odoo.sh`
- [x] Work-zone specialization
  - Role split: `src/orchestration/orchestrator.py` (`AGENT_ROLE`, `AGENT_ID`)
  - Strict ownership: `STRICT_WORK_ZONES=true`
  - Cloud draft-only + local final execution
- [x] Delegation via synced vault (Phase 1)
  - Domain paths:
    - `Needs_Action/<domain>/`
    - `Plans/<domain>/`
    - `Pending_Approval/<domain>/`
  - Claim-by-move:
    - `In_Progress/<agent>/`
  - Single writer dashboard:
    - local only updates dashboard
  - Cloud updates via signals:
    - `Signals/` written by cloud, merged by local
  - Sync playbook:
    - `docs/guides/vault-sync-guide.md`
- [x] Security rule (state sync only, secrets excluded)
  - `.gitignore`
  - `.gitignore-sync`
- [x] Deploy Odoo on cloud with HTTPS, backups, health monitoring
  - `deployment/cloud/docker-compose.odoo.yml`
  - `deployment/cloud/config/Caddyfile`
  - `deployment/cloud/healthcheck_odoo.sh`
  - `deployment/cloud/README.md`
- [x] Cloud Odoo draft-only and local approval for posting
  - guard in `.claude/skills/odoo-accounting/scripts/main_operation.py`
  - guard in `deployment/cloud/odoo-mcp.js`
  - local posting via `src/orchestration/approval_manager.py`
- [x] Optional A2A phase acknowledged; vault remains audit record
  - `specs/004-platinum-tier/contracts/mcp-sync.yaml`
- [x] Platinum minimum passing gate
  - `scripts/platinum_demo_gate.py`
  - `RUN_PLATINUM_DEMO_GATE.bat`

## Regression Tests Added for Critical Requirements

- `tests/unit/test_approval_manager.py`
  - extracts exact `## Content`
  - verifies approved content is posted exactly
- `tests/integration/test_us1_offline_email.py`
  - cloud drafts while local offline
  - local executes approved email and moves to `Done`
- `tests/integration/test_mcp_email.py`
  - markdown cloud draft detection + email MCP execution path
- `tests/integration/test_ralph_loop.py`
  - Ralph suitability and state creation checks

## Automated Structural Checker

- `scripts/check_hackathon_requirements.py`
- Wrapper: `RUN_HACKATHON_REQUIREMENTS_CHECK.bat`
