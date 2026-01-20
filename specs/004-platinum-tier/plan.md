# Implementation Plan: Platinum Tier Cloud + Local Executive

**Branch**: `004-platinum-tier` | **Date**: 2026-01-20 | **Spec**: [spec.md](spec.md)

**Input**: specs/004-platinum-tier/spec.md

## Summary
Deploy dual-agent architecture: Cloud (draft-only) + Local (approval/execution) with Syncthing vault sync. Odoo on cloud VM, PM2 orchestration, claim-by-move ownership.

## Technical Context

**Language/Version**: Python 3.13+, Node.js 20+
**Primary Dependencies**: PM2, Syncthing, xmlrpc.client, docker-py
**Storage**: Synced Markdown vault (Obsidian format)
**Testing**: pytest integration/E2E
**Target Platform**: Linux VM (Oracle Cloud), Mac/Win/Linux local
**Project Type**: Infrastructure/Deployment
**Performance Goals**: Sync <30s, 99.9% uptime, handover <5min
**Constraints**: No secret sync, HITL mandatory, ARM-compatible
**Scale/Scope**: 2 VMs, 10 agents concurrent

## Constitution Check
- [x] Local-First: Vault sync excludes secrets
- [x] HITL: Approval files for executions
- [x] Agent Skills: New skills for cloud/local
- [x] Security: PM2 secure mode, Docker isolation
- [x] Audit Logging: Sync logs in vault
- [x] Graceful Degradation: Fallback queues
- [x] Tiered Delivery: Builds on Gold Tier
- [x] Observability: /Cloud_Status.md dashboard
- [x] MCP Modular: Odoo/Syncthing MCPs

## Project Structure

```
specs/004-platinum-tier/
├── plan.md (this)
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/mcp-sync.yaml
└── tasks.md (next)

deployment/
├── cloud/ecosystem.config.js (PM2)
├── cloud/docker-compose.odoo.yml
├── local/syncthing-config
└── vault-sync/
    ├── claim-task.py
    └── status-mcp.js
```

**Structure Decision**: deployment/ subdir for infra-as-code, vault-sync/ for sync logic.

## Complexity Tracking
N/A - Constitution compliant

**Phase 0 Complete**: research.md resolved
**Phase 1 Complete**: data-model, contracts, quickstart created
**Agent Context Updated**

Ready for `/sp.tasks`.