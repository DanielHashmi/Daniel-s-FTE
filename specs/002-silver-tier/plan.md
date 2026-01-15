# Implementation Plan: Silver Tier Functional Assistant

**Branch**: `002-silver-tier` | **Date**: 2026-01-15 | **Spec**: [specs/002-silver-tier/spec.md](./spec.md)
**Input**: Feature specification from `specs/002-silver-tier/spec.md`

## Summary

Implement the Silver Tier "Functional Assistant" capabilities, transforming the foundational AI Employee into an active agent. This includes building three multi-channel watchers (Gmail, WhatsApp, LinkedIn), a centralized Orchestrator to manage the reasoning loop, and Human-in-the-Loop (HITL) safeguards. We will also integrate MCP servers for Email and LinkedIn actions, ensuring all AI functionality is exposed as reusable Agent Skills.

## Technical Context

**Language/Version**: Python 3.13+ (Watchers/Orchestrator), Node.js v24+ (PM2, MCP)
**Primary Dependencies**: `playwright` (WhatsApp), `google-api-python-client` (Gmail), `mcp` (Servers), `pm2` (Process Mgmt)
**Storage**: Local Filesystem (JSON Logs, Markdown Vault)
**Testing**: `pytest` for unit/integration tests
**Target Platform**: Local OS (Linux/WSL/Mac)
**Project Type**: Autonomous Agent System
**Performance Goals**: Watcher latency < 2m, Action execution < 1m
**Constraints**: strictly local-first logic, zero plain-text secrets
**Scale/Scope**: ~2k LOC, 3 interacting processes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Local-First**: All data stored in `AI_Employee_Vault`.
- [x] **HITL**: `Pending_Approval` workflow implemented for all sensitive actions.
- [x] **Skills First**: All actions wrapped in Agent Skills (`manage-approval`, `email-ops`).
- [x] **Security**: Credentials via `.env`, Dry-Run mode supported.
- [x] **Audit Logging**: JSON structured logs in `Logs/`.
- [x] **Graceful Degradation**: Watchers use exponential backoff; Watchdog monitors health.
- [x] **Tiered Delivery**: Builds strictly on Bronze Tier foundation.

## Project Structure

### Documentation (this feature)

```text
specs/002-silver-tier/
├── plan.md              # This file
├── research.md          # Architecture decisions
├── data-model.md        # Action/Plan/Log schemas
├── quickstart.md        # Setup guide
├── contracts/           # API/Class definitions
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
src/
├── watchers/
│   ├── base.py          # Abstract Base Class
│   ├── gmail.py         # Gmail implementation
│   ├── whatsapp.py      # WhatsApp implementation
│   └── linkedin.py      # LinkedIn implementation
├── mcp/
│   ├── email_server.py  # Email MCP
│   └── social_server.py # LinkedIn MCP
├── orchestration/
│   ├── orchestrator.py  # Main event loop / watchdog
│   └── plan_manager.py  # Logic for creating/updating plans
└── lib/
    ├── vault.py         # Vault access helpers
    └── logging.py       # Structured logging
```

**Structure Decision**: Modular Python package structure `src/` organized by component type to separate concerns (Watchers vs MCP vs Logic).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple Processes (PM2) | Concurrent monitoring of 3 channels | Single loop blocks on one channel's latency/failure |
| Explicit MCP Servers | Constitution specific requirement (FR-027) | Direct function calls reduce compatibility with future tiers |
