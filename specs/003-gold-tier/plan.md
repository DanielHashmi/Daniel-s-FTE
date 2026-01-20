# Implementation Plan: Gold Tier Autonomous Employee

**Branch**: `003-gold-tier` | **Date**: 2026-01-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-gold-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The Gold Tier transforms the AI Employee from a functional assistant into a fully autonomous business partner. Core capabilities include: (1) Ralph Wiggum loop for persistent multi-step task execution, (2) Odoo 19 accounting integration for financial intelligence, (3) automated weekly CEO Briefing with business insights, (4) comprehensive error recovery and graceful degradation, (5) expanded social media presence (Facebook, Instagram, Twitter), (6) comprehensive audit logging, and (7) architecture documentation. The system operates 24/7 with minimal human oversight, providing proactive business intelligence and strategic recommendations.

## Technical Context

**Language/Version**: Python 3.13+ (established in Bronze/Silver Tier)
**Primary Dependencies**:
- **Existing (Silver Tier)**: playwright, mcp, google-api-python-client, PM2/supervisord
- **New (Gold Tier)**: Odoo API (xmlrpc/json-2), Facebook SDK, Twitter API client, Instagram API client
- **Ralph Wiggum Loop**: Persistent state file + recursive execution loop
- **Watchdog**: PM2 health checks + custom Python watchdog

**Storage**: File-based (Obsidian vault markdown files, JSON audit logs, no database)
**Testing**: pytest (established), integration tests for MCP servers, contract tests for external APIs
**Target Platform**: Cross-platform (Linux/WSL2, macOS, Windows) - local-first architecture
**Project Type**: Single project (CLI/automation system with Agent Skills)
**Performance Goals**:
- CEO Briefing generation: < 5 minutes for weekly analysis
- Odoo transaction sync: < 2 minutes for 1000 transactions
- Ralph Wiggum loop iteration: < 30 seconds per task step
- Social media post scheduling: < 10 seconds per platform

**Constraints**:
- 24/7 autonomous operation without manual intervention
- Graceful degradation when components fail (80% functionality with one component down)
- 90-day audit log retention (estimated 1-5 GB storage)
- OAuth token refresh / API Key management without manual re-authentication
- Rate limit compliance for all external APIs

**Scale/Scope**:
- Single user/business owner deployment
- ~1000 financial transactions per month
- ~100 tasks per week
- 4 social media platforms (LinkedIn, Facebook, Instagram, Twitter)
- ~50 emails per day across all watchers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Local-First Architecture ✅ PASS
- **Requirement**: All sensitive data MUST remain on user's local machine
- **Implementation**: Obsidian vault stores all data locally (financial transactions, task history, audit logs, briefings)
- **External APIs**: Odoo, Facebook, Instagram, Twitter APIs used only for necessary integrations with secure credential management
- **Compliance**: Full compliance - no cloud storage of sensitive data

### II. Human-in-the-Loop for Sensitive Actions ✅ PASS
- **Requirement**: AI MUST NOT execute sensitive actions without explicit human approval
- **Implementation**:
  - Social media posts (all platforms) require approval (FR-038)
  - Financial transactions already covered by Silver Tier HITL
  - Approval workflow via `/Pending_Approval/` folder (established pattern)
- **Compliance**: Full compliance - all sensitive actions gated by HITL

### III. Agent Skills First ✅ PASS
- **Requirement**: All AI functionality MUST be implemented as Agent Skills
- **Implementation**:
  - FR-054: Mandates Agent Skills for all AI functionality
  - FR-055: Specific skills required (accounting sync, briefing generation, social media posting, error recovery, audit log management)
- **Compliance**: Full compliance - specification explicitly requires Agent Skills pattern

### IV. Security & Credential Management ✅ PASS
- **Requirement**: Credentials MUST NEVER be stored in plain text or committed to version control
- **Implementation**:
  - API Keys for Odoo and social media in OS-native secure storage (Security Considerations section)
  - Audit logs sanitize sensitive data (FR-043)
  - Environment variables for API keys
- **Compliance**: Full compliance - security considerations explicitly address credential management

### V. Comprehensive Audit Logging ✅ PASS
- **Requirement**: Every action MUST be logged with timestamp, action type, actor, parameters, result, approval status
- **Implementation**:
  - FR-042: Log every external action with all required fields
  - FR-044: Daily log consolidation
  - FR-045: 90-day retention minimum
  - FR-048: Approval audit trail
- **Compliance**: Full compliance - User Story 6 dedicated to comprehensive audit logging

### VI. Graceful Degradation & Error Recovery ✅ PASS
- **Requirement**: System MUST continue operating when components fail
- **Implementation**:
  - User Story 4 (P1) entirely dedicated to error recovery and graceful degradation
  - FR-025-FR-033: Exponential backoff, token refresh, component isolation, watchdog process
  - SC-002: 90% automatic recovery from transient errors
  - SC-012: 80% functionality maintained when one component down
- **Compliance**: Full compliance - error recovery is a P1 user story

### VII. Tiered Delivery & Incremental Value ✅ PASS
- **Requirement**: Features MUST be delivered in tiers (Bronze → Silver → Gold)
- **Implementation**:
  - Gold Tier builds on completed Bronze Tier and 90% complete Silver Tier
  - Dependencies section explicitly lists "Silver Tier Completion" as prerequisite
  - Prioritized user stories (P1, P2, P3) enable incremental delivery within Gold Tier
- **Compliance**: Full compliance - Gold Tier is the third tier in progression

### VIII. Observability & Transparency ✅ PASS
- **Requirement**: System MUST provide visibility into operations via Dashboard.md and human-readable formats
- **Implementation**:
  - CEO Briefing provides weekly transparency into system operations (User Story 3)
  - Dashboard.md updates for degraded states (FR-028, acceptance scenario 4.3)
  - All data in human-readable formats (Markdown, JSON)
  - Comprehensive audit logging provides full operation history
- **Compliance**: Full compliance - CEO Briefing enhances transparency beyond Silver Tier

**GATE RESULT**: ✅ **PASS** - All constitution principles satisfied. No violations. Proceed to Phase 0 research.

---

## Constitution Check (Post-Design Re-Evaluation)

*Re-evaluated after Phase 1 design completion (research.md, data-model.md, contracts/interfaces.md, quickstart.md)*

### I. Local-First Architecture ✅ PASS (Confirmed)
- **Design Verification**: All entities in data-model.md are file-based (Markdown, JSON) stored in Obsidian vault
- **No Cloud Dependencies**: Financial transactions, audit logs, briefings, social media posts all stored locally
- **External APIs**: Only for necessary integrations (Odoo, Facebook, Instagram, Twitter) with secure credential management
- **Compliance**: Design maintains full local-first architecture

### II. Human-in-the-Loop for Sensitive Actions ✅ PASS (Confirmed)
- **Design Verification**: contracts/interfaces.md specifies HITL approval interface for all sensitive actions
- **Social Media Posts**: All platforms require approval requests in Pending_Approval/ (Social Media Post entity, status transitions)
- **Financial Transactions**: Covered by Silver Tier HITL (maintained in Gold Tier)
- **Compliance**: Design enforces HITL for all sensitive actions

### III. Agent Skills First ✅ PASS (Confirmed)
- **Design Verification**: contracts/interfaces.md defines 5 Agent Skills (odoo-accounting, briefing-gen, social-ops, error-recovery, audit-mgmt)
- **All AI Functionality**: Implemented as Agent Skills per FR-054 and FR-055
- **Compliance**: Design follows Agent Skills pattern throughout

### IV. Security & Credential Management ✅ PASS (Confirmed)
- **Design Verification**: quickstart.md emphasizes environment variables, OS-native secure storage, .env in .gitignore
- **Audit Log Sanitization**: Audit Log Entry entity includes parameter sanitization (FR-043)
- **Token Refresh**: research.md documents OAuth 2.0 token refresh for all SDKs
- **Compliance**: Design implements secure credential management

### V. Comprehensive Audit Logging ✅ PASS (Confirmed)
- **Design Verification**: Audit Log Entry entity includes all required fields (timestamp, action type, actor, parameters, approval status, result, duration)
- **Daily Consolidation**: Specified in data-model.md (FR-044)
- **90-Day Retention**: Specified in data-model.md (FR-045)
- **Compliance**: Design provides comprehensive audit logging

### VI. Graceful Degradation & Error Recovery ✅ PASS (Confirmed)
- **Design Verification**: Error Recovery Record entity captures all recovery attempts
- **Error Recovery Skill**: contracts/interfaces.md defines /error-recovery skill with retry logic
- **Exponential Backoff**: Specified in research.md and contracts
- **Compliance**: Design implements robust error recovery

### VII. Tiered Delivery & Incremental Value ✅ PASS (Confirmed)
- **Design Verification**: quickstart.md verifies Bronze and Silver Tier prerequisites before Gold Tier implementation
- **Incremental Approach**: Phase-by-phase implementation (Phase 1-9 in quickstart)
- **Compliance**: Design maintains tiered delivery approach

### VIII. Observability & Transparency ✅ PASS (Confirmed)
- **Design Verification**: CEO Briefing entity provides weekly transparency
- **Dashboard Integration**: quickstart.md includes PM2 metrics integration
- **Human-Readable Formats**: All entities use Markdown/JSON (data-model.md)
- **Compliance**: Design enhances observability and transparency

**POST-DESIGN GATE RESULT**: ✅ **PASS** - All constitution principles satisfied after design phase. Design artifacts maintain full compliance. Ready for implementation (/sp.tasks).

## Project Structure

### Documentation (this feature)

```text
specs/003-gold-tier/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── interfaces.md    # Agent Skills and MCP server interfaces
├── checklists/          # Quality validation
│   └── requirements.md  # Specification quality checklist (completed)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/
├── orchestration/           # Existing (Silver Tier)
│   ├── orchestrator.py      # Main orchestration loop
│   ├── plan_manager.py      # Plan creation and management
│   ├── claude_invoker.py    # Claude Code integration
│   └── approval_manager.py  # HITL approval workflow
├── watchers/                # Existing (Silver Tier)
│   ├── base.py              # BaseWatcher abstract class
│   ├── gmail.py             # Gmail watcher
│   ├── whatsapp.py          # WhatsApp watcher
│   └── linkedin.py          # LinkedIn watcher
├── mcp/                     # Existing (Silver Tier) + New (Gold Tier)
│   ├── email_server.py      # Email MCP server (existing)
│   ├── social_server.py     # LinkedIn MCP server (existing)
│   ├── odoo_server.py       # NEW: Odoo accounting MCP server
│   ├── facebook_server.py   # NEW: Facebook MCP server
│   ├── instagram_server.py  # NEW: Instagram MCP server
│   └── twitter_server.py    # NEW: Twitter MCP server
├── lib/                     # Existing (Silver Tier) + Enhanced (Gold Tier)
│   ├── vault.py             # Vault path management and file operations
│   ├── logging.py           # Audit logging (enhanced for Gold Tier)
│   ├── retry.py             # NEW: Exponential backoff retry logic
│   └── watchdog.py          # NEW: Process monitoring and restart
└── skills/                  # NEW: Gold Tier Agent Skills
    ├── accounting_sync/     # Odoo transaction sync skill
    ├── briefing_gen/        # CEO Briefing generation skill
    ├── social_post/         # Multi-platform social media posting skill
    ├── error_recovery/      # Error recovery and graceful degradation skill
    └── audit_mgmt/          # Audit log management skill

.claude/
└── skills/                  # Agent Skills (Claude Code framework)
    ├── odoo-accounting/     # Odoo sync skill definition
    ├── briefing-gen/        # CEO Briefing skill definition
    ├── social-ops/          # Social media operations (enhanced)
    ├── error-recovery/      # Error recovery skill definition
    └── audit-mgmt/          # Audit management skill definition

.claude/
└── plugins/
    └── ralph-wiggum/        # NEW: Stop hook for persistent task execution
        ├── stop-hook.sh     # Stop hook script
        └── config.json      # Ralph Wiggum loop configuration

AI_Employee_Vault/           # Existing (Bronze/Silver Tier) + Enhanced (Gold Tier)
├── Dashboard.md             # Real-time system status (enhanced)
├── Company_Handbook.md      # AI behavior rules
├── Business_Goals.md        # Business objectives and targets
├── Inbox/                   # Raw inputs
├── Needs_Action/            # Structured action files
├── Done/                    # Completed action files
├── Plans/                   # Claude-generated plan files
├── Logs/                    # Audit logs (enhanced for Gold Tier)
│   ├── 2026-01-19.json      # Daily consolidated logs
│   └── Archive/             # NEW: Compressed logs > 90 days
├── Pending_Approval/        # Files awaiting human approval
├── Approved/                # Human-approved action files
├── Rejected/                # Human-rejected action files
├── Accounting/              # NEW: Financial data from Odoo
│   ├── transactions/        # Transaction data by month
│   └── summaries/           # Financial summary reports
├── Briefings/               # NEW: Weekly CEO Briefings
│   └── 2026-01-13_Monday_Briefing.md
└── Quarantine/              # NEW: Corrupted files for human review

tests/
├── unit/                    # Unit tests for individual components
│   ├── test_retry.py        # NEW: Retry logic tests
│   ├── test_watchdog.py     # NEW: Watchdog tests
│   └── test_briefing.py     # NEW: CEO Briefing generation tests
├── integration/             # Integration tests
│   ├── test_odoo_sync.py    # NEW: Odoo integration tests
│   ├── test_social_post.py  # NEW: Social media posting tests
│   └── test_ralph_loop.py   # NEW: Ralph Wiggum loop tests
└── fixtures/                # Test fixtures and mock data
    ├── odoo_transactions.json
    └── social_posts.json
```

**Structure Decision**: Single project structure (Option 1) is appropriate for this CLI/automation system. The existing Bronze/Silver Tier structure is extended with new Gold Tier components (Odoo MCP server, social media MCP servers, Ralph Wiggum plugin, enhanced audit logging, CEO Briefing generation). All AI functionality is implemented as Agent Skills in `.claude/skills/` following the constitution requirement.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All constitution principles are satisfied. This section is not applicable.