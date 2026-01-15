---
description: "Task list for Silver Tier implementation"
---

# Tasks: Silver Tier Functional Assistant

**Input**: Design documents from `/specs/002-silver-tier/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/interfaces.md

**Organization**: Tasks are grouped by user story priorities (P1, P2, P3).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure (`src/`, `tests/`, `src/watchers`, `src/mcp`, `src/orchestration`, `src/lib`) per plan.md
- [ ] T002 Initialize `pyproject.toml` with `playwright`, `mcp`, `google-api-python-client` dependencies
- [ ] T003 Generate `ecosystem.config.js` for PM2 management of watchers and orchestrator
- [ ] T004 Install Playwright browsers (`playwright install chromium`) for WhatsApp watcher

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create `src/lib/vault.py` for standard vault path management and file operations
- [ ] T006 Create `src/lib/logging.py` for structured JSON audit logging
- [ ] T007 Define `BaseWatcher` abstract class in `src/watchers/base.py` per contracts/interfaces.md
- [ ] T008 [P] Implement `src/orchestration/orchestrator.py` skeleton (main loop scaffolding)
- [ ] T009 [P] Create `tests/fixtures/` with sample Action Files and Plans

**Checkpoint**: Foundation ready - watcher and logic implementation can now begin

---

## Phase 3: User Story 1 - Multi-Channel Communication Monitoring (P1) 🎯 MVP

**Goal**: Monitor Gmail, WhatsApp, and LinkedIn for urgent messages and create Action Files.

**Independent Test**: Send test messages to each channel and verify `Needs_Action/*.md` file creation.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `GmailWatcher` in `src/watchers/gmail.py` using `google-api-python-client`
- [ ] T011 [P] [US1] Implement `WhatsAppWatcher` in `src/watchers/whatsapp.py` using `playwright`
- [ ] T012 [P] [US1] Implement `LinkedInWatcher` in `src/watchers/linkedin.py`
- [ ] T013 [US1] Update `src/orchestration/orchestrator.py` to register and run these watchers
- [ ] T014 [US1] Implement integration test `tests/integration/test_watchers.py` (mocking external APIs)

**Checkpoint**: Watchers are running and detecting inputs.

---

## Phase 4: User Story 2 - Intelligent Task Planning (P1)

**Goal**: Analyze incoming requests and create structured execution plans.

**Independent Test**: Drop an action file in `Needs_Action/` and verify a valid `Plan.md` is created in `Plans/`.

### Implementation for User Story 2

- [ ] T015 [P] [US2] Implement `src/orchestration/plan_manager.py` logic for plan creation
- [ ] T016 [US2] Update `orchestrator.py` to trigger `/process-inbox` or internal logic when `Needs_Action` is populated
- [ ] T017 [US2] Integrate `plan_manager.py` with `lib/vault.py` for reading/writing plan files
- [ ] T018 [US2] Add logic to identify "approval required" steps based on sensitive keywords

**Checkpoint**: Input -> Action File -> Plan File flow is working.

---

## Phase 5: User Story 3 - HITL Approval Workflow (P1)

**Goal**: Require and handle human approval for sensitive actions.

**Independent Test**: Trigger a sensitive action, verify `Pending_Approval` file, verify approval/rejection moves files correctly.

### Implementation for User Story 3

- [ ] T019 [P] [US3] Implement `ApprovalManager` in `src/orchestration/approval_manager.py`
- [ ] T020 [US3] Connect `orchestrator.py` to monitor `Pending_Approval` folder state changes
- [ ] T021 [US3] Ensure `manage-approval` skill works correctly with the generated approval files
- [ ] T022 [US3] Add audit logging for approval/rejection events in `src/lib/logging.py`

**Checkpoint**: Core safety loop (Plan -> Approval -> Execution) is complete.

---

## Phase 6: User Story 4 - Email Sending via MCP (P2)

**Goal**: Send approved emails using MCP server.

**Independent Test**: Verify `email-ops` skill can send emails (via Dry Run or real API) when invoked by orchestrator.

### Implementation for User Story 4

- [ ] T023 [P] [US4] Implement `EmailServer` in `src/mcp/email_server.py` using `mcp` library
- [ ] T024 [US4] Update `email-ops` skill to optionally connect to this MCP server or use shared logic
- [ ] T025 [US4] Add support for handling attachments in `email_server.py`
- [ ] T026 [US4] Register email server in PM2 config

**Checkpoint**: Email capability active.

---

## Phase 7: User Story 5 - Automated LinkedIn Posting (P2)

**Goal**: Post updates to LinkedIn via MCP.

**Independent Test**: Verify `social-ops` skill can post updates.

### Implementation for User Story 5

- [ ] T027 [P] [US5] Implement `SocialServer` in `src/mcp/social_server.py`
- [ ] T028 [US5] Implement duplicate content detection logic in `social_server.py`
- [ ] T029 [US5] Register social server in PM2 config

**Checkpoint**: Social capability active.

---

## Phase 8: User Story 6 & 7 - Scheduling & Health (P3)

**Goal**: Process routine tasks and self-heal.

**Independent Test**: Verify watchdog restarts crashed process; verify scheduled task runs.

### Implementation for User Stories 6 & 7

- [ ] T030 [P] [US6] Integrate `scheduler` skill with `orchestrator.py` (read `Config/schedules.json`)
- [ ] T031 [P] [US7] Implement `Watchdog` class in `src/orchestration/watchdog.py`
- [ ] T032 [US7] Add health check loop to `orchestrator.py` (checking PM2 status)
- [ ] T033 [US7] Add dashboard status update logic to `orchestrator.py`

**Checkpoint**: System is robust and automated.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Security, documentation, and cleanup

- [ ] T034 Update `quickstart.md` with verified steps
- [ ] T035 Ensure all sensitive actions have Audit Log coverage
- [ ] T036 Refactor any shared credentials loading to `lib/config.py`
- [ ] T037 Final integration test of full flow: Email In -> Plan -> Approval -> Email Out

---

## Dependencies & Execution Order

1. **Setup & Foundational** (T001-T009) must represent the first PR/commit.
2. **US1 (Watchers)** can be built in parallel with **US2 (Planning)** if multiple engineers were available, but sequential is safer for solo dev.
3. **US3 (HITL)** blocks the execution part of US4/US5.
4. **US4 & US5 (MCP)** can be built in parallel.
5. **US6 & US7** are independent enhancements.

### MVP Scope
Complete Phases 1, 2, 3, 4, and 5. This provides a functional system that monitors, plans, and asks for permission, even if the "action" part is manual (User moves file to "Approved" -> AI logs "Executed" via dry run).
