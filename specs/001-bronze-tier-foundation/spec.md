# Feature Specification: Bronze Tier - Personal AI Employee Foundation

**Feature Branch**: `001-bronze-tier-foundation`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: "Bronze Tier: Personal AI Employee Foundation - Obsidian vault, one watcher, Claude Code integration, and Agent Skills"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Knowledge Base Setup (Priority: P1)

As a user building my first AI Employee, I need a local knowledge base where I can see what my AI is doing, what tasks are pending, and what rules it should follow, so that I have visibility and control over the autonomous system.

**Why this priority**: This is the foundational layer. Without a knowledge base, there's no way to communicate with the AI, see its work, or provide it with rules. This must exist before any other functionality.

**Independent Test**: Can be fully tested by opening Obsidian, navigating to the AI_Employee_Vault at the project root, and verifying that all required files and folders exist with proper structure and initial content.

**Acceptance Scenarios**:

1. **Given** I have Obsidian installed, **When** I set up the AI Employee vault, **Then** I see a structured vault at the project root (AI_Employee_Vault/) with /Inbox, /Needs_Action, /Done folders
2. **Given** the vault is initialized, **When** I open Dashboard.md, **Then** I see a real-time summary section showing system status, pending actions count, and recent activity log
3. **Given** the vault is initialized, **When** I open Company_Handbook.md, **Then** I see documented rules for how the AI should behave (politeness, approval thresholds, communication style)
4. **Given** I have the vault structure, **When** I manually create a test file in /Needs_Action, **Then** the file persists and is visible in Obsidian with proper formatting

---

### User Story 2 - Input Detection (Priority: P2)

As a user, I need my AI Employee to automatically detect when new work arrives (either from my email or from files I drop), so that I don't have to manually tell it what to do every time.

**Why this priority**: This gives the AI "eyes" to see when work arrives. Without input detection, the system is purely reactive and requires manual triggering. This is the first step toward autonomy.

**Independent Test**: Can be fully tested by triggering the chosen input source (sending a test email with a keyword, or dropping a file in a watched folder) and verifying that a properly formatted action file appears in AI_Employee_Vault/Needs_Action within the expected time window.

**Acceptance Scenarios**:

1. **Given** the Watcher is running, **When** a new input arrives (email with keyword OR file drop), **Then** a structured Markdown file is created in AI_Employee_Vault/Needs_Action within 2 minutes
2. **Given** a new input is detected, **When** the Watcher creates the action file, **Then** the file includes YAML frontmatter with type, source, timestamp, priority, and status fields
3. **Given** the Watcher is monitoring, **When** multiple inputs arrive simultaneously, **Then** each input creates a separate action file with unique identifiers
4. **Given** the Watcher encounters an error (network timeout, authentication failure), **When** the error occurs, **Then** the error is logged and the Watcher continues running without crashing
5. **Given** the Watcher has processed an input, **When** the same input appears again, **Then** the Watcher does not create a duplicate action file

---

### User Story 3 - AI Processing and Action Creation (Priority: P3)

As a user, I need Claude Code to read pending work from my vault, understand what needs to be done, and create clear action plans, so that I can review and approve the AI's proposed actions.

**Why this priority**: This is the "brain" of the system. It transforms raw inputs (emails, files) into structured action plans. Without this, the Watcher just creates files that sit unprocessed.

**Independent Test**: Can be fully tested by manually creating a test action file in AI_Employee_Vault/Needs_Action, running Claude Code pointed at the vault, and verifying that Claude reads the file, creates a Plan.md with checkboxes, and moves the original file to /Done.

**Acceptance Scenarios**:

1. **Given** there are files in AI_Employee_Vault/Needs_Action, **When** Claude Code runs, **Then** it reads all pending action files and identifies the work to be done
2. **Given** Claude has read an action file, **When** it processes the request, **Then** it creates a Plan.md file with a clear objective, numbered steps with checkboxes, and any required approvals
3. **Given** Claude has created a plan, **When** the plan is complete, **Then** the original action file is moved from /Needs_Action to /Done with a timestamp
4. **Given** Claude encounters an unclear request, **When** it cannot determine the action, **Then** it creates a clarification request file in /Needs_Action asking specific questions
5. **Given** Claude is processing multiple action files, **When** it runs, **Then** it processes them in priority order (high priority first)
6. **Given** Claude completes processing, **When** it finishes, **Then** Dashboard.md is updated with the latest activity summary

---

### User Story 4 - Agent Skills Implementation (Priority: P4)

As a user, I need all AI functionality packaged as reusable Agent Skills, so that I can easily invoke, test, and maintain the AI's capabilities over time.

**Why this priority**: This ensures the system is maintainable and professional-grade. Skills provide clear interfaces, documentation, and version control. This is required by the constitution but can be implemented after core functionality works.

**Independent Test**: Can be fully tested by running a skill command (e.g., `/setup-vault`) and verifying that it executes the expected workflow, produces the expected outputs, and can be invoked repeatedly with consistent results.

**Acceptance Scenarios**:

1. **Given** the Bronze Tier functionality is working, **When** I convert it to Agent Skills, **Then** each major capability (vault setup, watcher management, action processing) is available as a named skill
2. **Given** a skill is defined, **When** I invoke it, **Then** it executes the expected workflow and returns a clear success or failure message
3. **Given** a skill exists, **When** I view its documentation, **Then** I see clear descriptions of what it does, required inputs, expected outputs, and example usage
4. **Given** multiple skills exist, **When** I list available skills, **Then** I see all Bronze Tier skills with brief descriptions
5. **Given** a skill fails, **When** the error occurs, **Then** the skill provides a clear error message explaining what went wrong and how to fix it

---

### Edge Cases

- **What happens when the Obsidian vault is locked or inaccessible?** The Watcher should log an error and continue running. Claude Code should fail gracefully with a clear error message. No data should be lost.

- **What happens when the Watcher detects an input but cannot create the action file (disk full, permissions error)?** The Watcher should log the error, retry once after 30 seconds, and if still failing, alert the user via a notification file in a fallback location.

- **What happens when Claude Code is processing and the user manually edits files in the vault?** Claude should detect file changes, re-read the modified files, and adjust its processing accordingly. No conflicts or data loss should occur.

- **What happens when multiple instances of Claude Code try to process the same vault simultaneously?** The system should use file locking or timestamps to prevent race conditions. Only one instance should process a given action file.

- **What happens when the Watcher is stopped and restarted?** It should resume monitoring without losing track of what it has already processed. It should not create duplicate action files for inputs that were already handled.

- **What happens when an action file has malformed YAML frontmatter?** Claude Code should detect the malformed YAML, log a warning, attempt to extract what information it can, and create a clarification request if critical fields are missing.

- **What happens when the user deletes files from /Needs_Action while Claude is processing?** Claude should handle missing files gracefully, log the deletion, and continue processing remaining files without crashing.

## Requirements *(mandatory)*

### Functional Requirements

#### Obsidian Vault Structure

- **FR-001**: System MUST use the existing AI_Employee_Vault folder at the project root as the Obsidian vault
- **FR-002**: System MUST create the following folder structure within AI_Employee_Vault: /Inbox, /Needs_Action, /Done, /Plans, /Logs, /Pending_Approval, /Approved, /Rejected
- **FR-003**: System MUST create a Dashboard.md file with sections for: System Status, Pending Actions Count, Recent Activity (last 10 items), Quick Stats (files processed today/this week)
- **FR-004**: System MUST create a Company_Handbook.md file with documented rules including: communication style guidelines, approval thresholds for different action types, priority keywords, and error handling preferences
- **FR-005**: All files created in the vault MUST use Markdown format with proper YAML frontmatter for metadata
- **FR-006**: Folder names MUST use underscores (not spaces) for compatibility with command-line tools

#### Watcher Implementation

- **FR-007**: System MUST implement ONE Watcher (user chooses: Gmail Watcher OR File System Watcher)
- **FR-008**: Watcher MUST inherit from a BaseWatcher abstract class with methods: check_for_updates(), create_action_file()
- **FR-009**: Watcher MUST run continuously with a configurable check interval (default: 60 seconds for file system, 120 seconds for Gmail)
- **FR-010**: Watcher MUST create action files in AI_Employee_Vault/Needs_Action with YAML frontmatter including: type, source, timestamp (ISO 8601), priority (high/medium/low), status (pending)
- **FR-011**: Watcher MUST track processed items to prevent duplicate action file creation
- **FR-012**: Watcher MUST log all activities (checks performed, files created, errors encountered) to AI_Employee_Vault/Logs/watcher-YYYY-MM-DD.log
- **FR-013**: Watcher MUST handle errors gracefully (network timeouts, authentication failures) without crashing
- **FR-014**: Watcher MUST support dry-run mode for testing without creating actual action files

#### Gmail Watcher Specific Requirements (if chosen)

- **FR-015**: Gmail Watcher MUST authenticate using OAuth2 credentials stored securely (not in plain text)
- **FR-016**: Gmail Watcher MUST monitor for unread emails matching specific criteria (keywords: "urgent", "invoice", "payment", "help", "asap")
- **FR-017**: Gmail Watcher MUST extract email metadata: sender, subject, received date, snippet (first 200 characters)
- **FR-018**: Gmail Watcher MUST mark processed emails with a label (e.g., "AI_Processed") to track what has been handled

#### File System Watcher Specific Requirements (if chosen)

- **FR-019**: File System Watcher MUST monitor the AI_Employee_Vault/Inbox folder for new files
- **FR-020**: File System Watcher MUST detect new files within 10 seconds of creation
- **FR-021**: File System Watcher MUST move detected files to /Needs_Action and create corresponding metadata files
- **FR-022**: File System Watcher MUST support multiple file types: .txt, .md, .pdf, .docx, .csv

#### Claude Code Integration

- **FR-023**: System MUST configure Claude Code to use the AI_Employee_Vault as its working directory
- **FR-024**: Claude Code MUST read all files in AI_Employee_Vault/Needs_Action when invoked
- **FR-025**: Claude Code MUST read Company_Handbook.md to understand behavioral rules before processing
- **FR-026**: Claude Code MUST create Plan.md files with: clear objective statement, numbered action steps with checkboxes, required approvals section (if applicable), estimated completion time
- **FR-027**: Claude Code MUST move processed action files from /Needs_Action to /Done after creating plans
- **FR-028**: Claude Code MUST update Dashboard.md with latest activity after each processing run
- **FR-029**: Claude Code MUST log all processing activities to AI_Employee_Vault/Logs/claude-YYYY-MM-DD.log
- **FR-030**: Claude Code MUST handle missing or malformed files gracefully without crashing

#### Agent Skills

- **FR-031**: System MUST implement the following Agent Skills: setup-vault, start-watcher, stop-watcher, process-inbox, view-dashboard
- **FR-032**: Each Agent Skill MUST have a clear name, description, required inputs, expected outputs, and example usage
- **FR-033**: Agent Skills MUST be invocable via command-line interface (e.g., `/setup-vault`)
- **FR-034**: Agent Skills MUST return clear success or failure messages
- **FR-035**: Agent Skills MUST be independently testable

#### Security & Privacy

- **FR-036**: System MUST store all credentials in environment variables or OS-native secure storage (never in plain text files)
- **FR-037**: System MUST create a .env.example file showing required environment variables without actual values
- **FR-038**: System MUST add .env to .gitignore to prevent credential leakage
- **FR-039**: System MUST implement dry-run mode for all external actions (email access, file operations)
- **FR-040**: All logs MUST NOT contain sensitive information (passwords, API keys, email content beyond snippets)

#### Error Handling & Resilience

- **FR-041**: Watcher MUST auto-restart after crashes using a watchdog process or process manager
- **FR-042**: System MUST implement exponential backoff retry for transient errors (network timeouts, API rate limits)
- **FR-043**: System MUST create error notification files in AI_Employee_Vault/Needs_Action when critical failures occur
- **FR-044**: System MUST maintain operation even when individual components fail (e.g., Watcher fails but Claude can still process existing files)

### Key Entities

- **Action File**: Represents a detected input that needs processing. Contains metadata (type, source, timestamp, priority, status) and content (email snippet, file reference, or task description). Lives in AI_Employee_Vault/Needs_Action until processed, then moves to /Done.

- **Plan File**: Represents Claude's proposed actions for handling an Action File. Contains objective, numbered steps with checkboxes, approval requirements, and completion status. Lives in AI_Employee_Vault/Plans folder.

- **Dashboard**: Real-time summary view showing system status, pending work count, recent activity, and quick statistics. Single file (Dashboard.md) in AI_Employee_Vault root, updated by Claude after each processing run.

- **Company Handbook**: Rule book defining how the AI should behave. Contains communication guidelines, approval thresholds, priority keywords, and error handling preferences. Single file (Company_Handbook.md) in AI_Employee_Vault root, read by Claude before processing.

- **Watcher**: Background process that monitors an input source (Gmail or file system) and creates Action Files when new inputs are detected. Runs continuously with configurable check intervals.

- **Agent Skill**: Reusable, named capability that performs a specific function (setup vault, start watcher, process inbox). Has clear interface, documentation, and can be invoked via command-line.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can set up the complete Bronze Tier system (vault + watcher + Claude integration) in under 30 minutes following documentation
- **SC-002**: Watcher detects new inputs and creates action files within 2 minutes of input arrival
- **SC-003**: Claude Code successfully processes 95% of action files without errors or clarification requests
- **SC-004**: System runs continuously for 24 hours without crashes or manual intervention
- **SC-005**: User can view current system status and pending work by opening Dashboard.md in under 10 seconds
- **SC-006**: All Agent Skills execute successfully on first invocation with valid inputs
- **SC-007**: System handles 10 consecutive inputs without creating duplicate action files or losing data
- **SC-008**: Error recovery works correctly - system resumes normal operation within 5 minutes after transient failures (network timeout, API rate limit)
- **SC-009**: User can understand what the AI did by reading the activity log in Dashboard.md without needing to check multiple files
- **SC-010**: System operates entirely locally with no data sent to external services except for the chosen input source (Gmail API if Gmail Watcher selected)

### Assumptions

- User has Obsidian installed (v1.11.4 or higher)
- User has Python 3.13 or higher installed
- User has Claude Code installed and configured
- User has basic command-line familiarity
- The AI_Employee_Vault folder exists at the project root
- User has approximately 100MB free disk space for vault and logs
- If Gmail Watcher chosen: User has a Google account and can create OAuth2 credentials
- If File System Watcher chosen: User will use AI_Employee_Vault/Inbox as the drop folder
- User is running on Windows, macOS, or Linux (WSL supported)
- User has stable internet connection for Claude Code API calls (minimum 10 Mbps)

### Out of Scope (Bronze Tier)

- Multiple simultaneous Watchers (Silver Tier)
- MCP server integrations (Silver Tier)
- Human-in-the-loop approval workflows (Silver Tier)
- Automated scheduling via cron/Task Scheduler (Silver Tier)
- Social media integrations (Gold Tier)
- Accounting system integration (Gold Tier)
- CEO briefing generation (Gold Tier)
- Ralph Wiggum loop for multi-step autonomous completion (Gold Tier)
- Email sending capabilities (Silver Tier)
- WhatsApp monitoring (Silver Tier)
- Payment processing (Gold Tier)

### Dependencies

- Obsidian application (external, user-installed)
- Claude Code CLI (external, user-installed)
- Python runtime (external, user-installed)
- Python packages: watchdog (file system monitoring), google-auth + google-api-python-client (if Gmail Watcher chosen)
- Operating system: Windows 10+, macOS 12+, or Linux with kernel 5.0+
- AI_Employee_Vault folder at project root

### Constraints

- All data must remain local (privacy requirement from constitution)
- No external services except chosen input source API
- Must work offline except for input detection and Claude API calls
- Maximum 2-minute delay for input detection (user expectation for "real-time" feel)
- Logs must not exceed 100MB per month (disk space management)
- Watcher must use less than 50MB RAM (resource efficiency)
- Setup process must not require advanced technical skills (accessibility)
- Vault location is fixed at project root (AI_Employee_Vault/)
