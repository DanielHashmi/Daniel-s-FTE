# Codebase Structure

**Last Updated:** February 25, 2026  
**Status:** Restructured for clarity and maintainability

## Overview

The Personal AI Employee codebase has been reorganized into a clean, hierarchical structure that separates concerns between source code, configuration, deployment, documentation, and runtime artifacts.

---

## Directory Guide

### Root Level: Essential Files Only
```
.env                      # Local environment variables (gitignored)
.env.example              # Template for environment setup
.gitignore                # Git ignore rules (updated for new structure)
README.md                 # Project overview
pyproject.toml            # Python package configuration
package.json              # Node.js dependencies
package-lock.json         # Locked Node dependencies
```

### `/bin` - Executable Scripts & Startup Tools
Entry point for all command-line operations.

```
bin/
├── start-brain.bat              # Main daemon startup (Windows)
├── start-brain-local.bat        # Local agent startup
├── start-brain-cloud.bat        # Cloud agent startup
├── start-dashboard.bat          # Dashboard UI startup
├── start-odoo.bat               # Odoo integration startup
├── start-edge-debug-profile1.bat # Development startup
├── run-mcp-email.sh             # Email MCP server
├── run-mcp-social.sh            # Social media MCP server
├── run-orchestrator.sh          # Main orchestrator process
├── quick-test.sh                # Quick test suite
├── test-system.sh               # System integration tests
├── monitor.sh                   # System monitoring script
├── verify-testing-tools.sh      # Verify test dependencies
├── quick_start.py               # Python quick start helper
├── create_test_invoice.py       # Invoice creation utility
├── TEST_QWEN_TASK.py            # Qwen model testing
├── test_live_tweet.js           # Twitter/X live testing
│
└── demos/                       # Demo scripts (organized)
    ├── open-demo.bat            # Open demo interface
    ├── run-all-demos.sh         # Execute all demos
    └── demo-workflow.sh         # Workflow demonstration
```

**Usage:** Execute scripts from this directory for system operations.

### `/config` - Configuration Files
Centralized configuration management.

```
config/
├── .env.example                 # Standard environment template
├── .env.cloud.example           # Cloud deployment config
└── defaults/                    # Default configuration files (future)
```

**Usage:** Keep all `.env` variants here. Update `.env` locally, never commit.

### `/src` - Main Application Source Code
Core logic, orchestration, and business logic.

```
src/
├── orchestration/               # Main orchestrator (vault-based workflow)
│   ├── orchestrator.py         # Role-aware orchestration engine
│   └── ...
├── actions/                     # Action handlers
├── handlers/                    # Event handlers
├── lib/                         # Shared libraries & utilities
│   ├── config.py               # Configuration loader (UPDATED session paths)
│   └── ...
├── mcp/                         # MCP integrations
├── skills/                      # AI skills implementations
├── social/                      # Social media posting
│   ├── instagram_playwright_poster.py  # Instagram (UPDATED paths)
│   ├── facebook_qwen_poster.py        # Facebook (UPDATED paths)
│   └── ...
├── utils/                       # Utility functions
└── watchers/                    # Input watchers
    ├── whatsapp.py             # WhatsApp watcher (UPDATED paths)
    ├── linkedin.py             # LinkedIn watcher (UPDATED paths)
    └── ...
```

**Code Updates Made:**
- Updated session paths from `instagram_session` to `session-data/instagram`
- Updated session paths from `facebook_session` to `session-data/facebook`
- Updated session paths from `whatsapp_session` to `session-data/whatsapp`
- Updated session paths from `linkedin_session` to `session-data/linkedin`

### `/mcp-servers` - MCP Server Implementations
External protocol server implementations for integrations.

```
mcp-servers/
├── email-mcp/                   # Email service integration
├── social-mcp/                  # Social media integration
└── node_modules/                # npm dependencies
```

### `/dashboard` - Next.js User Interface
Web-based operator dashboard for the AI Employee.

```
dashboard/
├── src/                         # React components & pages
├── public/                      # Static assets
├── package.json                 # UI dependencies
├── tsconfig.json                # TypeScript configuration
├── next.config.ts               # Next.js configuration
└── run-dev.cmd                  # Development server launcher
```

### `/deployment` - Deployment & Infrastructure
Deployment configurations for different environments.

```
deployment/
├── cloud/                       # Cloud deployment configs
│   └── docker-compose.odoo.yml # Odoo cloud deployment
├── local/                       # Local development configs
└── k8s/                         # Kubernetes manifests
```

### `/docker` - Docker Container Definitions
Docker files for containerized services.

```
docker/
├── gmail-watcher.Dockerfile     # Gmail watcher service
├── orchestrator.Dockerfile      # Orchestrator service
└── docker-compose.yml           # Multi-service composition
```

### `/docs` - Documentation
Comprehensive project documentation.

```
docs/
├── architecture.md              # System architecture
├── README.md                    # Documentation index
├── guides/                      # Setup and usage guides
├── archive/                     # Historical documentation
└── hackathon0-guide.md         # Hackathon 0 guide (MOVED from root)
```

### `/specs` - Project Specifications
Tier-based specifications and requirements.

```
specs/
├── 001-bronze-tier-foundation/  # Bronze tier specs
│   ├── spec.md
│   ├── plan.md
│   └── tasks.md
├── 002-silver-tier/             # Silver tier specs
├── 003-gold-tier/               # Gold tier specs
└── 004-platinum-tier/           # Platinum tier specs (current)
```

### `/history` - Project History & Decision Records
Prompt History Records (PHRs) and decision tracking.

```
history/
└── prompts/                     # Prompt History Records
    ├── constitution/           # Constitutional decisions
    ├── general/                # General decisions
    └── <feature-name>/        # Feature-specific PHRs
```

### `/AI_Employee_Vault` - Running System State
Core operational state and vault-based workflow (do not commit runtime data).

```
AI_Employee_Vault/              # LOCAL SYSTEM STATE (pre-commit ignored)
├── Dashboard.md                # Real-time system status
├── Company_Handbook.md         # AI behavior guidelines
├── README.md                   # Vault quick reference
├── Inbox/                      # Raw incoming inputs
├── Needs_Action/               # Pending action files
├── In_Progress/                # Currently processing
├── Pending_Approval/           # Awaiting HITL approval
├── Approved/                   # Human-approved actions
├── Rejected/                   # Rejected actions
├── Done/                       # Completed actions
├── Plans/                      # Generated execution plans
├── Logs/                       # Audit logs
├── Accounting/                 # Financial data
├── Config/                     # Vault-specific configs
└── ...                         # Gold Tier additions
```

### `/tests` - Test Suite
Test files and test configuration.

```
tests/
├── test_*.py                    # Unit and integration tests
├── conftest.py                  # pytest configuration
└── fixtures/                    # Test fixtures
```

### `/session-data` - Browser Session Data (Gitignored)
Persistent browser state for social media login sessions.

```
session-data/                    # Browser persistent context (MOVED, gitignored)
├── facebook/                    # Facebook session data
├── instagram/                   # Instagram session data
├── linkedin/                    # LinkedIn session data
└── whatsapp/                    # WhatsApp session data
```

**Security Note:** Contains sensitive authentication tokens. Never commit.

### `/.tmp` - Temporary Runtime Files (Gitignored)
Transient files generated during operation.

```
.tmp/                           # Temporary files (NEW, gitignored)
├── logs/                       # Runtime logs (MOVED from runtime-logs/)
├── cache/                      # Build cache & artifacts (MOVED from htmlcov/)
└── build/                      # Build output (for future use)
```

**Note:** These are auto-generated during execution. Safe to delete.

### `/scripts` - Development & Deployment Scripts
Development-specific scripts (not entry points in `bin/`).

```
scripts/
├── check_hackathon_requirements.py  # Hackathon validator
├── create_linkedin_autopost_action.py # LinkedIn setup
├── platinum_demo_gate.py             # Demo checker
├── deploy-k8s.ps1                    # Kubernetes deployment
├── deploy-k8s.sh
├── start-dashboard.ps1
└── verify-meta-graph.ps1
```

### `/.specify` - Project Specification Tooling
Reserved for specification and planning tools.

```
.specify/
├── memory/
│   └── constitution.md          # Constitutional rules
├── templates/
│   └── phr-template.prompt.md   # Prompt History Record template
└── ...
```

### Other Important Files

**Root Level Configuration:**
- `.claude/` - Claude Code instructions & skills
- `.vscode/` - VS Code workspace settings
- `.git/` - Git version control
- `.gitignore-sync` - Sync-specific ignore rules
- `ecosystem.config.js` - PM2 process configuration

---

## File Movement Summary

### Created Directories
- ✅ `bin/` - Entry point for all scripts
- ✅ `bin/demos/` - Demo scripts organized  
- ✅ `config/` - Configuration files
- ✅ `session-data/` - Browser session folders
- ✅ `.tmp/` - Temporary runtime files

### Moved Files

**Scripts to `bin/`:**
- START_BRAIN.bat
- START_BRAIN_CLOUD.bat
- START_BRAIN_LOCAL.bat
- START_DASHBOARD.bat
- START_ODOO.bat
- START_EDGE_DEBUG_PROFILE1.bat
- run-mcp-email.sh
- run-mcp-social.sh
- run-orchestrator.sh
- quick-test.sh
- test-system.sh
- monitor.sh
- verify-testing-tools.sh
- quick_start.py
- create_test_invoice.py
- TEST_QWEN_TASK.py
- test_live_tweet.js

**Demo Files to `bin/demos/`:**
- OPEN_DEMO.bat
- run-all-demos.sh
- demo-workflow.sh

**Configuration to `config/`:**
- .env.example
- .env.cloud.example

**Sessions to `session-data/`:**
- facebook_session/ → session-data/facebook/
- instagram_session/ → session-data/instagram/
- linkedin_session/ → session-data/linkedin/
- whatsapp_session/ → session-data/whatsapp/
- ig_get_started_fb_login.html → session-data/
- meta_access_tokens.html → session-data/

**Logs to `.tmp/logs/`:**
- runtime-logs/ → .tmp/logs/
- dashboard_runtime.log → .tmp/logs/
- htmlcov/ → .tmp/cache/

**Documentation to `docs/`:**
- Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md → docs/hackathon0-guide.md

### Code Updates

**Path References Updated in Source Code:**
- `src/watchers/whatsapp.py` - Updated session path
- `src/watchers/linkedin.py` - Updated session path
- `src/social/instagram_playwright_poster.py` - Updated session paths (2 locations)
- `src/social/facebook_qwen_poster.py` - Updated session paths (2 locations)
- `src/lib/config.py` - Updated WhatsApp session path

### .gitignore Updates
- ✅ Added `session-data/` references
- ✅ Added `.tmp/` references
- ✅ Deprecated old directory references
- ✅ Updated path documentation

---

## Key Improvements

1. **Clear Separation of Concerns**
   - Entry points in `bin/`
   - Configuration in `config/`
   - Source code in `src/`
   - Deployment configs separate from runtime

2. **Reduced Root-Level Clutter**
   - Scripts organized hierarchically
   - Temporary files isolated in `.tmp/`
   - Session data isolated in `session-data/`

3. **Better Git Management**
   - Runtime artifacts excluded consistently
   - Sensitive data kept separate
   - Configuration files clearly marked

4. **Developer Experience**
   - Clear entry points for operations
   - Predictable file locations
   - Easy to understand dependencies

5. **Production Ready**
   - Audit logging in `AI_Employee_Vault/Logs/`
   - Configuration management via `config/`
   - Deployment configs in `deployment/`

---

## Migration Notes

This restructuring is **non-breaking** for the running system:
- All session paths have been updated in source code
- Environment variable defaults have been updated
- Git ignores have been updated to track new locations
- Old directories are preserved during migration (can be deleted after verification)

**Verification Checklist:**
- [ ] Run `bin/start-brain.bat` (or equivalent for your OS)
- [ ] Check `AI_Employee_Vault/Dashboard.md` for active processes
- [ ] Verify social media posting works (Instagram, Facebook, LinkedIn)
- [ ] Check WhatsApp watcher operations
- [ ] Review `AI_Employee_Vault/Logs/` for errors

---

## Future Structure Improvements

1. **Add `config/defaults/`** - Default configuration files for all components
2. **Expand `scripts/`** - Move specialized deployment scripts here
3. **Create `tools/`** - Development tooling and utilities
4. **Add `examples/`** - Example configurations and workflows
5. **Expand `k8s/`** - More comprehensive Kubernetes manifests

---

## Questions or Issues?

Refer to the relevant documentation:
- Architecture: See `docs/architecture.md`
- Deployment: See `deployment/README.md` (if exists)
- Running the system: See `README.md`
- Contributing: See `.specify/memory/constitution.md`
