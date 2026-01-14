# Implementation Plan: Bronze Tier - Personal AI Employee Foundation

**Branch**: `001-bronze-tier-foundation` | **Date**: 2026-01-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bronze-tier-foundation/spec.md`

## Summary

Build the foundational layer of the Personal AI Employee system (Bronze Tier) consisting of:
1. **Obsidian Vault Structure**: Local knowledge base at AI_Employee_Vault/ with organized folders for workflow management
2. **Watcher System**: Background process monitoring one input source (Gmail OR File System) to detect new work
3. **Claude Code Integration**: AI processing engine that reads action files, creates plans, and updates dashboard
4. **Agent Skills**: Reusable capabilities packaged as Claude Agent Skills for vault setup, watcher management, and inbox processing

**Technical Approach**: Python-based watcher scripts using abstract base class pattern, file-based communication via Markdown with YAML frontmatter, Claude Code as reasoning engine operating on local vault, all functionality exposed as Agent Skills per constitutional requirement.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- watchdog 6.0+ (file system monitoring)
- google-auth 2.27+ and google-api-python-client 2.187+ (Gmail Watcher, if chosen)
- pyyaml 6.0+ (YAML frontmatter parsing)
- python-dotenv 1.0+ (environment variable management)

**Storage**: File system (Markdown files with YAML frontmatter in AI_Employee_Vault/)
**Testing**: pytest 8.0+ with pytest-cov for coverage
**Target Platform**: Cross-platform (Windows 10+, macOS 12+, Linux with kernel 5.0+, WSL supported)
**Project Type**: Single project (Python scripts + Agent Skills)
**Performance Goals**:
- Watcher detects inputs within 2 minutes
- Claude processes action files in under 30 seconds
- System runs 24 hours without crashes
- Memory usage under 50MB for Watcher

**Constraints**:
- All data must remain local (constitutional requirement)
- No external services except chosen input source API
- Must work offline except for input detection and Claude API calls
- Logs must not exceed 100MB per month
- Setup process must not require advanced technical skills

**Scale/Scope**:
- Single user system
- Handle 10-50 action files per day
- Support 1-2 concurrent Claude processing sessions
- Vault size up to 1GB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Local-First Architecture ✅ PASS
- **Requirement**: All sensitive data on local machine, Obsidian vault as knowledge base
- **Implementation**: AI_Employee_Vault at project root, all data in Markdown files, no cloud storage
- **Status**: Compliant

### Principle II: Human-in-the-Loop for Sensitive Actions ✅ PASS
- **Requirement**: No sensitive actions without approval
- **Implementation**: Bronze Tier has no action execution (read-only), only creates plans for review
- **Status**: Compliant (HITL workflows deferred to Silver Tier)

### Principle III: Agent Skills First ✅ PASS
- **Requirement**: All AI functionality as Agent Skills
- **Implementation**: setup-vault, start-watcher, stop-watcher, process-inbox, view-dashboard as skills
- **Status**: Compliant

### Principle IV: Security & Credential Management ✅ PASS
- **Requirement**: No plain text credentials, environment variables, .env in .gitignore
- **Implementation**: .env.example template, credentials in environment variables, dry-run mode
- **Status**: Compliant

### Principle V: Comprehensive Audit Logging ✅ PASS
- **Requirement**: Log all actions with timestamp, actor, parameters, result
- **Implementation**: AI_Employee_Vault/Logs/watcher-YYYY-MM-DD.log and claude-YYYY-MM-DD.log
- **Status**: Compliant

### Principle VI: Graceful Degradation & Error Recovery ✅ PASS
- **Requirement**: Continue operating when components fail, auto-restart, retry logic
- **Implementation**: Watcher error handling, exponential backoff, watchdog process
- **Status**: Compliant

### Principle VII: Tiered Delivery & Incremental Value ✅ PASS
- **Requirement**: Bronze Tier independently functional before Silver
- **Implementation**: This IS Bronze Tier - foundation for future tiers
- **Status**: Compliant

### Principle VIII: Observability & Transparency ✅ PASS
- **Requirement**: Dashboard showing status, human-readable formats
- **Implementation**: Dashboard.md with real-time status, Markdown/JSON formats
- **Status**: Compliant

### Principle IX: Modular Integration via MCP ⚠️ DEFERRED
- **Requirement**: External integrations via MCP servers
- **Implementation**: Bronze Tier uses direct API calls (Gmail) or file system monitoring
- **Status**: MCP integration deferred to Silver Tier (acceptable per tiered delivery)

**Overall Gate Status**: ✅ PASS - All applicable principles satisfied, MCP deferred appropriately

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-tier-foundation/
├── spec.md                    # Feature specification (complete)
├── plan.md                    # This file (in progress)
├── research.md                # Phase 0 output (to be created)
├── data-model.md              # Phase 1 output (to be created)
├── quickstart.md              # Phase 1 output (to be created)
├── contracts/                 # Phase 1 output (to be created)
│   ├── watcher-interface.md   # Watcher abstract interface
│   ├── action-file-schema.yaml # Action file YAML schema
│   └── plan-file-schema.yaml  # Plan file YAML schema
└── tasks.md                   # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
AI_Employee_Vault/             # Obsidian vault (created by setup)
├── Inbox/                     # Drop folder for File System Watcher
├── Needs_Action/              # Pending action files
├── Done/                      # Completed action files
├── Plans/                     # Generated plan files
├── Logs/                      # System logs
├── Pending_Approval/          # Approval requests (Silver Tier)
├── Approved/                  # Approved actions (Silver Tier)
├── Rejected/                  # Rejected actions (Silver Tier)
├── Dashboard.md               # Real-time system status
└── Company_Handbook.md        # AI behavior rules

src/
├── watchers/
│   ├── __init__.py
│   ├── base_watcher.py        # Abstract base class
│   ├── gmail_watcher.py       # Gmail monitoring (optional)
│   └── filesystem_watcher.py  # File system monitoring (optional)
├── skills/
│   ├── __init__.py
│   ├── setup_vault.py         # Vault initialization skill
│   ├── watcher_manager.py     # Start/stop watcher skill
│   └── process_inbox.py       # Claude processing skill
├── utils/
│   ├── __init__.py
│   ├── yaml_parser.py         # YAML frontmatter handling
│   ├── logger.py              # Logging utilities
│   └── retry.py               # Retry decorator
└── config.py                  # Configuration management

tests/
├── unit/
│   ├── test_base_watcher.py
│   ├── test_yaml_parser.py
│   └── test_retry.py
├── integration/
│   ├── test_filesystem_watcher.py
│   ├── test_gmail_watcher.py
│   └── test_vault_setup.py
└── fixtures/
    ├── sample_action_file.md
    └── sample_plan_file.md

.env.example                   # Environment variable template
.gitignore                     # Includes .env
pyproject.toml                 # Python project configuration
README.md                      # Setup and usage instructions
```

**Structure Decision**: Single project structure chosen because:
- All components are Python-based
- No frontend/backend separation needed
- Agent Skills are Python modules
- Simple deployment model (single process per component)

## Complexity Tracking

> No constitutional violations requiring justification. All principles satisfied or appropriately deferred per tiered delivery model.
