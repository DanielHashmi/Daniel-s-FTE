---
title: Platinum Tier Tasks
short_name: platinum-tier
feature_number: 004
total_tasks: 28
mvp_tasks: 12
---

# Platinum Tier Task List

**Branch**: 004-platinum-tier | **Date**: 2026-01-20 | **Plan**: [plan.md](plan.md)

## Dependency Graph
```
Phase 1 (Setup) → Phase 2 (Foundational) → US1 → US2 → US3 → Polish
All phases independent except sequential dependencies shown
```

## Parallel Opportunities
- US1 models/services [P]
- US2 MCP contracts [P]
- US3 conflict scripts [P]

## Phase 1: Project Setup (4 tasks)
- [X] T001 Create deployment/cloud directory structure per plan
- [X] T002 Create deployment/local directory structure per plan
- [X] T003 Add ecosystem.config.js for PM2 in deployment/cloud/ecosystem.config.js
- [X] T004 Create .env.example with ODOO/SYNCTHING vars

## Phase 2: Foundational Infrastructure (8 tasks)
- [X] T005 Deploy Odoo Docker in deployment/cloud/docker-compose.odoo.yml
- [ ] T006 Install PM2 and test ecosystem in deployment/cloud/setup.sh
- [ ] T007 Configure Syncthing in deployment/local/syncthing-config.toml
- [ ] T008 Create vault-sync/claim-task.py logic
- [ ] T009 Create vault-sync/status-mcp.js endpoint
- [ ] T010 Add /In_Progress/cloud-agent and /In_Progress/local-agent folders to vault structure
- [ ] T011 Document exclusions in .gitignore-sync
- [ ] T012 Test vault sync latency locally

## Phase 3: US1 Offline Email Handover (6 tasks)
- [X] T013 [P] [US1] Create cloud-email watcher in src/watchers/cloud_email_watcher.py
- [X] T014 [P] [US1] Implement draft reply logic in deployment/cloud/draft_reply.py
- [X] T015 [P] [US1] Create local approval handler in src/handlers/local_approval.py
- [X] T016 [P] [US1] Add email MCP integration test in tests/integration/test_mcp_email.py
- [X] T017 [P] [US1] Test US1 end-to-end offline simulation in tests/integration/test_us1_offline_email.py
- [X] T018 [P] [US1] Update Dashboard.md template for handover status

## Phase 4: US2 Odoo Workflow (5 tasks)
- [X] T019 [P] [US2] Extend odoo-accounting skill for draft/live modes in .claude/skills/odoo-accounting/scripts/main_operation.py
- [X] T020 [P] [US2] Create odoo-mcp server in deployment/cloud/odoo-mcp.js
- [X] T021 [P] [US2] Add approval workflow for invoice posting
- [X] T022 [P] [US2] Test US2 sync → approval → post flow in tests/integration/odoo/test_odoo_workflow.py
- [X] T023 [P] [US2] Audit log Odoo actions (integrated in main_operation.py)

## Phase 5: US3 Conflict Resolution (3 tasks)
- [X] T024 [P] [US3] Implement claim-by-move validator in vault-sync/claim_task.py
- [X] T025 [P] [US3] Add conflict detection test cases in tests/integration/test_conflict_resolution.py
- [X] T026 [P] [US3] Simulate dual-agent conflict in e2e test in tests/integration/test_us3_e2e_conflict.py
- [X] T012 Test vault sync latency locally in tests/integration/test_vault_sync_latency.py

## Final Phase: Polish & Integration (2 tasks)
- [ ] T027 Integrate all US into orchestrator.py
- [ ] T028 Create demo video script and README updates

## Final Phase: Polish & Integration (2 tasks)
- [ ] T027 Integrate all US into orchestrator.py
- [ ] T028 Create demo video script and README updates

**MVP**: Phases 1-3 (US1 complete handover)

**Validation**: All tasks independently testable, file paths specific, constitution compliant.
- [ ] T007 Configure Syncthing in deployment/local/syncthing-config.toml
- [ ] T008 Create vault-sync/claim-task.py logic
- [ ] T009 Create vault-sync/status-mcp.js endpoint
- [ ] T010 Add /In_Progress/cloud-agent and /In_Progress/local-agent folders to vault structure
- [ ] T011 Document exclusions in .gitignore-sync
- [ ] T012 Test vault sync latency locally

## Phase 3: US1 Offline Email Handover (6 tasks)
- [ ] T013 [P] [US1] Create cloud-email watcher in src/watchers/cloud_email_watcher.py
- [ ] T014 [P] [US1] Implement draft reply logic in deployment/cloud/draft_reply.py
- [ ] T015 [US1] Create local approval handler in src/handlers/local_approval.py
- [ ] T016 [US1] Add email MCP integration test in tests/mcp_email_test.py
- [ ] T017 [US1] Test US1 end-to-end offline simulation
- [ ] T018 [US1] Update Dashboard.md template for handover status

## Phase 4: US2 Odoo Workflow (5 tasks)
- [ ] T019 [P] [US2] Extend odoo-accounting skill for draft/live modes in .claude/skills/odoo-accounting/scripts/main_operation.py
- [ ] T020 [US2] Create odoo-mcp server in deployment/cloud/odoo-mcp.js
- [ ] T021 [US2] Add approval workflow for invoice posting
- [ ] T022 [US2] Test US2 sync → approval → post flow
- [ ] T023 [US2] Audit log Odoo actions

## Phase 5: US3 Conflict Resolution (3 tasks)
- [ ] T024 [P] [US3] Implement claim-by-move validator in vault-sync/claim_validator.py
- [ ] T025 [US3] Add conflict detection test cases
- [ ] T026 [US3] Simulate dual-agent conflict in e2e test

## Final Phase: Polish & Integration (2 tasks)
- [ ] T027 Integrate all US into orchestrator.py
- [ ] T028 Create demo video script and README updates

**MVP**: Phases 1-3 (US1 complete handover)

**Validation**: All tasks independently testable, file paths specific, constitution compliant.