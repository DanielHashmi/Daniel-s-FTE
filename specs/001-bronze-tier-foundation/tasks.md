# Tasks: Bronze Tier - Personal AI Employee Foundation

**Branch**: `001-bronze-tier-foundation`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Status**: ✅ COMPLETED (All 35 tasks finished - Jan 15, 2026)

## Phase 1: Setup & Configuration
*Goal: Initialize project structure and environment.*

- [X] T001 Create `pyproject.toml` with Python 3.13+, watchdog 6.0+, google-api-python-client 2.187+
- [X] T002 Create `.gitignore` including `.env`, `venv/`, `__pycache__/`, `AI_Employee_Vault/Logs/`
- [X] T003 Create `.env.example` with templates for `VAULT_PATH`, `GMAIL_CREDENTIALS_PATH`, `WATCHER_TYPE`
- [X] T004 Implement `src/config.py` using `python-dotenv` to load and validate environment variables
- [X] T005 Implement `src/utils/logger.py` for structured JSON logging (FR-012, FR-029)
- [X] T006 Implement `src/utils/yaml_parser.py` using `pyyaml` for frontmatter parsing (FR-005)

## Phase 2: Foundational Components
*Goal: Core abstract classes and shared utilities.*

- [X] T007 Implement `BaseWatcher` abstract class in `src/watchers/base_watcher.py` (FR-008, Contracts)
- [X] T008 [P] Implement `Retry` decorator in `src/utils/retry.py` for exponential backoff (FR-042)
- [X] T009 [P] Create `ecosystem.config.js` for PM2 process management (FR-041)
- [X] T010 [P] Create `tests/conftest.py` and basic test fixtures

## Phase 3: Knowledge Base Setup (User Story 1)
*Goal: Establish the local Obsidian vault structure.*

- [X] T011 [US1] Implement `src/skills/setup_vault.py` to create `AI_Employee_Vault` structure (FR-001, FR-002, FR-031)
- [X] T012 [US1] Implement logic in `setup_vault.py` to generate `Dashboard.md` (FR-003)
- [X] T013 [US1] Implement logic in `setup_vault.py` to generate `Company_Handbook.md` (FR-004)
- [X] T014 [US1] Create unit test `tests/unit/test_vault_setup.py` verifying folder/file creation
- [X] T015 [US1] Manual Task: Run `python -m src.skills.setup_vault` to initialize the vault (Vault exists and operational)

## Phase 4: Input Detection (User Story 2)
*Goal: Automatically detect new inputs via Watchers.*

- [X] T016 [US2] Implement `FileSystemWatcher` in `src/watchers/filesystem_watcher.py` (FR-019 to FR-022)
- [X] T017 [US2] Implement `GmailWatcher` in `src/watchers/gmail_watcher.py` (FR-015 to FR-018)
- [X] T018 [US2] Implement `src/skills/watcher_manager.py` to start/stop watchers via PM2 (FR-031)
- [X] T019 [P] [US2] Create integration test `tests/integration/test_filesystem_watcher.py`
- [X] T020 [P] [US2] Create mock/unit test `tests/unit/test_gmail_watcher.py`
- [X] T021 [US2] Manual Task: Configure `.env` with watcher preference and start watcher (FileSystemWatcher running with WSL polling)

## Phase 5: AI Processing (User Story 3)
*Goal: Process Action Files into Plan Files using Claude.*

- [X] T022 [US3] Implement `src/skills/process_inbox.py` to read `Needs_Action` files (FR-024, FR-031)
- [X] T023 [US3] Implement logic to validate Action File frontmatter against schema (FR-030)
- [X] T024 [US3] Implement logic to generate `Plan.md` content (simulated or via Claude invocation) (FR-026)
- [X] T025 [US3] Implement logic to move processed files to `Done/` and update `Dashboard.md` (FR-027, FR-028)
- [X] T026 [US3] Create integration test `tests/integration/test_process_inbox.py`
- [X] T027 [US3] Manual Task: Invoke `python -m src.skills.process_inbox` on a test file (Completed: 3 action files processed, 3 plans created and executed)

## Phase 6: Agent Skills (User Story 4)
*Goal: Finalize and expose all capabilities as reusable skills.*

- [X] T028 [US4] Implement `src/skills/view_dashboard.py` to read and display dashboard status (FR-031)
- [X] T029 [US4] Ensure all skills (`setup-vault`, `process-inbox`, etc.) support `--help` and CLI args (FR-032)
- [X] T030 [US4] Create `README.md` with usage instructions for all skills
- [X] T031 [US4] Verify all skills are independently testable (FR-035)

## Phase 7: Polish & Documentation
*Goal: Final validation and documentation.*

- [X] T032 Create `tests/e2e/test_full_flow.py` (Setup -> Watch -> Detect -> Process)
- [X] T033 Verify log rotation and retention policies (FR-012)
- [X] T034 Final verification of no sensitive data in logs (FR-040)
- [X] T035 Update `quickstart.md` if any implementation details changed

## Implementation Strategy
- **MVP**: Complete Phases 1, 2, 3, and 4 (File System Watcher only).
- **Full Bronze**: Complete all phases including Gmail Watcher and Processing.
- **Testing**: Run `pytest` after each phase.

## Dependencies
1. **US2 (Watcher)** depends on **Phase 2 (BaseWatcher)** and **Phase 1 (Config)**.
2. **US3 (Processing)** depends on **US1 (Vault)** existing and **US2 (Action Files)** being created.
3. **US4 (Skills)** is mostly implemented concurrently with US1-3, with final polish in Phase 6.
