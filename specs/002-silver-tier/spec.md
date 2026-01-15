# Feature Specification: Silver Tier Functional Assistant

**Feature Branch**: `002-silver-tier`
**Created**: 2026-01-15
**Status**: Draft
**Input**: User description: "Implement Silver Tier Functional Assistant with multiple watchers, MCP integration, and HITL approval workflow"

## Overview

The Silver Tier represents the transformation from a foundational AI Employee system (Bronze Tier) into a fully functional autonomous assistant capable of monitoring multiple communication channels, taking intelligent actions via external integrations, and requiring human approval for sensitive operations. This tier focuses on practical, real-world automation that delivers measurable business value while maintaining strict security and human oversight requirements.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Channel Communication Monitoring (Priority: P1)

As a business owner, I need my AI Employee to monitor Gmail, WhatsApp, and LinkedIn simultaneously so that I never miss urgent messages requiring immediate attention across any channel.

**Why this priority**: Multi-channel monitoring is the foundational capability that enables all other Silver Tier features. Without reliable monitoring across communication channels, the AI Employee cannot detect actionable events or provide value beyond Bronze Tier capabilities.

**Independent Test**: Can be fully tested by sending test messages to Gmail, WhatsApp, and LinkedIn containing urgent keywords, then verifying that structured action files are created in the Needs_Action folder within expected timeframes (2-5 minutes). Delivers immediate value by consolidating monitoring across platforms.

**Acceptance Scenarios**:

1. **Given** the Gmail watcher is running with a 2-minute check interval, **When** an important unread email arrives with the subject "URGENT: Client Invoice Request", **Then** an action file is created in Needs_Action/ within 2 minutes containing sender details, subject, snippet, and suggested actions
2. **Given** the WhatsApp watcher is monitoring with a 30-second interval, **When** a message arrives containing the keyword "urgent", "asap", "invoice", "payment", or "help", **Then** an action file is created in Needs_Action/ within 60 seconds with message text, sender, timestamp, and priority flag
3. **Given** the LinkedIn watcher is monitoring with a 5-minute interval, **When** a new connection request or message arrives from a potential client, **Then** an action file is created in Needs_Action/ within 5 minutes with profile information, message content, and recommended response options
4. **Given** multiple watchers are running concurrently, **When** messages arrive simultaneously on different channels, **Then** separate action files are created for each message without conflicts or data loss
5. **Given** a watcher encounters a transient network error, **When** the error occurs during monitoring, **Then** the watcher logs the error, waits for the configured retry interval, and resumes monitoring without requiring manual intervention

---

### User Story 2 - Intelligent Task Planning and Execution (Priority: P1)

As a busy professional, I need the AI Employee to analyze incoming requests, create structured execution plans with clear steps, and track completion status so that I can review what actions were taken and ensure nothing is overlooked.

**Why this priority**: Intelligent planning is what differentiates a reactive notification system from an autonomous assistant. This capability enables the AI to understand context, break down complex requests, and maintain visibility into its decision-making process.

**Independent Test**: Can be tested by creating a test action file in Needs_Action/ with a multi-step request (e.g., "Client requests invoice and wants to schedule a call"), then verifying that a Plan.md file is generated with structured steps, dependencies, approval requirements, and completion checkboxes. Delivers value by providing transparency and structure to automation.

**Acceptance Scenarios**:

1. **Given** an action file exists in Needs_Action/ requesting an invoice, **When** Claude Code processes the folder via /process-inbox, **Then** a Plan.md file is created identifying the client, calculating the amount from rates, outlining steps (generate PDF, send email, log transaction), and flagging email send for human approval
2. **Given** a Plan.md file has been created with 5 steps, **When** Claude completes steps 1-3, **Then** the plan file is updated with checkboxes marked complete for those steps, timestamps for each completion, and clear indication of which step is currently in progress
3. **Given** a plan requires human approval for step 4, **When** Claude reaches that step, **Then** processing pauses, an approval request file is created in Pending_Approval/, and the plan status is updated to "pending_approval" with clear instructions for the human
4. **Given** multiple action files exist in Needs_Action/, **When** /process-inbox is triggered, **Then** separate plan files are created for each action, prioritized by urgency flags, with no cross-contamination of information
5. **Given** a plan encounters an error during execution, **When** the error occurs, **Then** the plan status is updated to "error", error details are logged, and the plan remains in the current state for human review rather than attempting automatic recovery

---

### User Story 3 - Human-in-the-Loop Approval Workflow (Priority: P1)

As a business owner concerned about security, I need all sensitive actions (sending emails to new contacts, making payments, posting publicly) to require my explicit approval before execution so that the AI never takes risky actions autonomously.

**Why this priority**: HITL approval is a non-negotiable security requirement for Silver Tier. Without this capability, the system cannot be trusted to operate autonomously on real business communications and transactions.

**Independent Test**: Can be tested by triggering an action that requires approval (e.g., email to new contact), verifying an approval request file is created in Pending_Approval/, manually moving it to Approved/, then confirming the action executes. Delivers immediate value by providing safety guardrails.

**Acceptance Scenarios**:

1. **Given** Claude determines an email needs to be sent to a new contact, **When** the email action is prepared, **Then** an approval request file is created in Pending_Approval/ with recipient, subject, body preview, attachments list, and clear approval instructions instead of sending immediately
2. **Given** an approval request file exists in Pending_Approval/, **When** the human reviews it and moves the file to the Approved/ folder, **Then** the requested action executes within 60 seconds and the approval file is moved to Done/ with execution timestamp and result status
3. **Given** an approval request file exists in Pending_Approval/, **When** the human reviews it and moves the file to the Rejected/ folder, **Then** the action is cancelled, the rejection is logged in the audit log with timestamp, and no further automatic attempts are made
4. **Given** an approval request has been pending for 24 hours, **When** the expiration time is reached, **Then** the request is automatically moved to Rejected/ with reason "expired", the Dashboard.md is updated with an alert, and the human is notified
5. **Given** multiple approval requests exist simultaneously, **When** the human processes them in any order, **Then** each approval/rejection is handled independently without affecting other pending requests

---

### User Story 4 - Email Sending via MCP Integration (Priority: P2)

As a professional managing client communications, I need the AI Employee to send emails on my behalf (after approval) so that routine communications like invoices, confirmations, and updates can be automated while maintaining my professional voice.

**Why this priority**: Email sending is the first critical external action capability that demonstrates real automation value. While P2 because it depends on P1 capabilities (monitoring, planning, approval), it's essential for practical business use.

**Independent Test**: Can be tested by creating an approved email action file, verifying the Email MCP server receives the request, confirming Gmail API sends the email, and checking that the sent email appears in Gmail's Sent folder with correct recipient, subject, and body. Delivers value by automating routine email tasks.

**Acceptance Scenarios**:

1. **Given** an approved email action exists with recipient, subject, body, and PDF attachment, **When** the Email MCP processes the action, **Then** the email is sent via Gmail API, the sent message ID is captured, and the action result is logged with success status
2. **Given** an email send action fails due to invalid recipient address, **When** the Gmail API returns an error, **Then** the error is captured in the audit log, the approval file is moved to a Failed/ subfolder with error details, and the Dashboard.md is updated with failure notification
3. **Given** an email template includes dynamic variables (client name, amount, date), **When** the email is prepared for sending, **Then** all variables are correctly replaced with actual values from the business context before sending
4. **Given** an email includes a large attachment (>5MB), **When** the send action is attempted, **Then** the system validates attachment size, warns if it exceeds limits, and suggests alternatives (cloud link) if necessary
5. **Given** the Gmail API rate limit is reached, **When** additional send attempts occur, **Then** the system queues the emails, implements exponential backoff, and retries automatically without losing messages

---

### User Story 5 - Automated LinkedIn Business Posting (Priority: P2)

As a business owner focused on lead generation, I need the AI Employee to automatically post business updates and insights to LinkedIn on a regular schedule so that I maintain consistent social media presence without manual effort.

**Why this priority**: LinkedIn automation provides direct business value through lead generation and brand visibility. Ranked P2 because it's valuable but not critical for core operations, and depends on foundational monitoring and approval workflows.

**Independent Test**: Can be tested by scheduling a test post, verifying it appears in the Pending_Approval/ queue, approving it, and confirming it publishes to LinkedIn with correct content, timing, and formatting. Delivers value by automating social media presence.

**Acceptance Scenarios**:

1. **Given** a LinkedIn post schedule is configured for Mondays, Wednesdays, and Fridays at 9 AM, **When** the scheduled time arrives, **Then** Claude generates a relevant business post based on recent work, creates an approval request with post content and preview, and waits for human approval
2. **Given** an approved LinkedIn post exists, **When** the LinkedIn MCP executes the post action, **Then** the post is published to the user's LinkedIn profile, the post URL is captured, and the result is logged in the audit trail
3. **Given** a LinkedIn post fails to publish due to API error, **When** the error occurs, **Then** the system logs the error details, retries up to 3 times with exponential backoff, and alerts the human if all retries fail
4. **Given** a LinkedIn post is about to publish duplicate content, **When** the system detects similarity to a recent post (within 7 days), **Then** the post is flagged for human review with a warning about potential duplication
5. **Given** LinkedIn API rate limits are reached, **When** additional post attempts occur, **Then** the system queues posts, respects API limits, and schedules retries at appropriate intervals

---

### User Story 6 - Scheduled and On-Demand Task Processing (Priority: P3)

As a business owner with predictable routines, I need the AI Employee to process tasks on a schedule (daily morning briefing, weekly reports) and also respond to on-demand triggers (file drops, urgent messages) so that both routine and urgent work is handled appropriately.

**Why this priority**: Scheduling is important for routine operations but not critical for core functionality. Ranked P3 because the system can provide significant value with manual triggering before automated scheduling is implemented.

**Independent Test**: Can be tested by configuring a cron job to run /process-inbox daily at 8 AM, verifying it executes at the correct time, processes all pending actions, and updates the Dashboard.md with morning briefing. Delivers value by creating predictable routines.

**Acceptance Scenarios**:

1. **Given** a cron job is configured to run /process-inbox daily at 8:00 AM, **When** the scheduled time arrives, **Then** all Needs_Action/ files are processed, plans are created, the Dashboard.md is updated with a morning summary, and completion status is logged
2. **Given** a file is dropped into a monitored "drop folder", **When** the file system watcher detects the new file, **Then** it is immediately copied to Needs_Action/ with metadata (filename, size, timestamp), and Claude is triggered to process it within 2 minutes
3. **Given** multiple scheduled tasks overlap (8 AM briefing + 8:05 AM report), **When** both schedules trigger, **Then** tasks are queued and processed sequentially without conflicts or duplicate processing
4. **Given** a scheduled task fails to complete within expected time (>10 minutes), **When** the timeout is reached, **Then** the watchdog process logs the timeout, attempts graceful termination, and alerts the human via Dashboard.md notification
5. **Given** the system has been offline during a scheduled task window, **When** the system comes back online, **Then** missed tasks are identified, logged as missed (not retroactively executed), and the next scheduled occurrence proceeds normally

---

### User Story 7 - System Health Monitoring and Error Recovery (Priority: P3)

As a system operator, I need the AI Employee to monitor its own health (watcher processes, disk space, API connectivity) and recover gracefully from transient errors so that the system remains reliable without constant manual intervention.

**Why this priority**: Health monitoring and error recovery improve reliability but are ranked P3 because basic functionality can operate without automated recovery. Important for production use but not required for initial Silver Tier validation.

**Independent Test**: Can be tested by intentionally stopping a watcher process, verifying the watchdog detects the failure within 60 seconds, restarts the process automatically, and logs the recovery action. Delivers value by improving system uptime.

**Acceptance Scenarios**:

1. **Given** the Gmail watcher process crashes due to an unhandled exception, **When** the watchdog process runs its 60-second health check, **Then** the crashed watcher is detected, automatically restarted, the restart is logged, and the Dashboard.md is updated with a recovery notification
2. **Given** disk space drops below 10% available, **When** the system health check runs, **Then** old log files are automatically archived or compressed, a warning is logged, and the human is notified via Dashboard.md alert if space remains critically low
3. **Given** the Gmail API becomes temporarily unavailable (500 error), **When** the Gmail watcher encounters the error, **Then** it implements exponential backoff (30s, 60s, 120s), retries automatically, logs each attempt, and only alerts the human if failures persist beyond 10 minutes
4. **Given** the Obsidian vault becomes locked by another process, **When** Claude attempts to write a file, **Then** the system detects the lock, waits up to 30 seconds for the lock to clear, writes to a temporary backup location if the lock persists, and syncs later when the vault becomes available
5. **Given** all watcher processes are healthy but Claude Code becomes unresponsive, **When** the watchdog detects no Claude activity for 5 minutes despite pending actions, **Then** the watchdog logs the unresponsive state, attempts a graceful restart of Claude via the orchestrator, and alerts the human if restart fails

---

### Edge Cases

- **What happens when a watcher receives malformed data from an API?** The watcher logs the malformed response, skips processing that specific message, continues monitoring subsequent messages, and alerts the human via Dashboard.md with details of the parsing failure.

- **What happens when the same message is detected multiple times due to watcher restart?** Each watcher maintains a processed message ID cache (persisted to disk), checks incoming message IDs against the cache, and skips creating duplicate action files for previously processed messages.

- **What happens when an approval request file is manually edited while pending?** The system detects file modification timestamps, validates the file structure before processing approval, and rejects approvals with invalid structure or missing required fields.

- **What happens when a human moves a file to both Approved/ and Rejected/?** The system processes moves in timestamp order, takes the first valid action, logs a conflict warning, and ignores the second contradictory move.

- **What happens when the Email MCP server is not running when an approved email action is ready?** The system detects MCP unavailability, logs the failure, moves the approval back to Pending_Approval/ with a "MCP unavailable" note, and retries when MCP connectivity is restored.

- **What happens when a watcher's API credentials expire mid-operation?** The watcher detects authentication errors, pauses all monitoring for that service, logs the credential failure, alerts the human via Dashboard.md with instructions to refresh credentials, and resumes automatically once credentials are updated.

- **What happens when Claude creates a plan that requires more information than available in the action file?** Claude identifies missing information, creates a "clarification needed" flag in the plan, moves the action file to a Clarification_Needed/ subfolder with specific questions, and alerts the human to provide additional context.

- **What happens when multiple instances of Claude Code are started simultaneously?** The system implements file-based locking using PID files, detects concurrent instances, allows only one active instance, and logs warnings for blocked instances to prevent conflicting operations.

## Requirements *(mandatory)*

### Functional Requirements

#### Watcher Infrastructure

- **FR-001**: System MUST provide a BaseWatcher abstract class that all watchers inherit from, defining standard lifecycle methods (check_for_updates, create_action_file, run, handle_error)
- **FR-002**: Gmail watcher MUST monitor Gmail inbox using Gmail API with OAuth2 authentication, checking for unread important messages at configurable intervals (default: 120 seconds)
- **FR-003**: WhatsApp watcher MUST monitor WhatsApp Web using Playwright browser automation, detecting messages containing urgent keywords (urgent, asap, invoice, payment, help) at configurable intervals (default: 30 seconds)
- **FR-004**: LinkedIn watcher MUST monitor LinkedIn messages and connection requests using LinkedIn API, checking at configurable intervals (default: 300 seconds)
- **FR-005**: Each watcher MUST maintain a persistent cache of processed message IDs to prevent duplicate action file creation across restarts
- **FR-006**: Watchers MUST create structured Markdown files in Needs_Action/ with YAML frontmatter containing type, source, priority, timestamp, and status fields
- **FR-007**: Watchers MUST implement exponential backoff retry logic for transient errors (network timeouts, rate limits) with configurable max retry attempts (default: 3)
- **FR-008**: Watchers MUST log all errors, retries, and state changes to dated log files in Logs/ using structured JSON format

#### Process Management

- **FR-009**: System MUST provide process management for all watcher scripts using PM2, supervisord, or equivalent process manager
- **FR-010**: Process manager MUST automatically restart crashed watcher processes within 60 seconds of failure detection
- **FR-011**: Process manager MUST persist watcher configurations to survive system reboots, auto-starting watchers on boot
- **FR-012**: System MUST provide a /watcher-manager skill for starting, stopping, restarting, and checking status of watcher processes
- **FR-013**: Watchdog process MUST run every 60 seconds, checking health of all critical processes (orchestrator, watchers) and restarting failed processes

#### Intelligent Planning

- **FR-014**: System MUST provide a /process-inbox skill that processes all files in Needs_Action/, creating Plan.md files in Plans/ for each action
- **FR-015**: Plan files MUST include structured sections: Objective, Steps (with checkboxes), Required Approvals, Dependencies, Risk Assessment, and Completion Status
- **FR-016**: Claude MUST read Company_Handbook.md and Business_Goals.md to inform planning decisions and maintain consistency with business policies
- **FR-017**: Claude MUST identify when an action requires human approval based on approval thresholds defined in Company_Handbook.md (email to new contact, payment >$100, public posting)
- **FR-018**: Plan files MUST update in real-time as steps are completed, with timestamps for each step and clear indication of current progress
- **FR-019**: System MUST detect and flag plan failures, updating plan status to "error" and alerting human via Dashboard.md when errors occur

#### Claude Code Reasoning Engine (Hackathon Requirement)

- **FR-047**: System MUST invoke Claude Code CLI (`claude` command) as the reasoning engine for plan generation, NOT use hardcoded templates
- **FR-048**: Claude Code invocation MUST pass action file content and context (Company_Handbook.md, Business_Goals.md) as prompt input
- **FR-049**: System MUST capture Claude Code's output and write it as structured Plan.md files in Plans/ folder
- **FR-050**: System MUST implement graceful fallback to template-based planning if Claude Code CLI is unavailable
- **FR-051**: System MUST implement rate limiting to prevent excessive Claude Code invocations (configurable, default: max 10 per minute)
- **FR-052**: System MUST log all Claude Code invocations with prompt, response, and duration for debugging and cost tracking

#### Human-in-the-Loop Approval

- **FR-020**: System MUST create approval request files in Pending_Approval/ for all sensitive actions, including full details of the proposed action
- **FR-021**: Approval request files MUST include YAML frontmatter with action type, parameters, reason, created timestamp, expiration timestamp, and status
- **FR-022**: System MUST monitor Pending_Approval/ for file moves to Approved/ or Rejected/ folders, processing approvals within 60 seconds of detection
- **FR-023**: Approved actions MUST execute immediately, with results logged to audit log and approval file moved to Done/ with execution details
- **FR-024**: Rejected actions MUST be cancelled permanently, logged to audit log, and approval file moved to Rejected/ with rejection timestamp
- **FR-025**: Approval requests MUST expire after 24 hours by default, automatically moving to Rejected/ with "expired" reason
- **FR-026**: System MUST support dry-run mode via DRY_RUN environment variable, logging intended actions without executing them

#### MCP Server Integration

- **FR-027**: System MUST provide an Email MCP server exposing send_email, draft_email, and read_sent capabilities via MCP protocol
- **FR-028**: Email MCP MUST use Gmail API with OAuth2 authentication, supporting attachments up to 25MB and HTML/plain text formatting
- **FR-029**: Email MCP MUST validate recipient addresses, check against spam lists, and enforce rate limits (configurable, default: 50 emails/hour)
- **FR-030**: System MUST provide a LinkedIn MCP server exposing post_update, schedule_post, and read_post_stats capabilities
- **FR-031**: LinkedIn MCP MUST detect duplicate content by comparing new post text to posts from the last 7 days, flagging similarities >80%
- **FR-032**: All MCP servers MUST implement timeout handling (default: 30 seconds), graceful degradation, and detailed error responses
- **FR-033**: MCP servers MUST log all actions to audit log with full request/response details for debugging and compliance

#### Scheduling and Orchestration

- **FR-034**: System MUST support scheduled task execution using cron (Linux/Mac) or Task Scheduler (Windows) for routine operations
- **FR-035**: System MUST provide a master orchestrator script that coordinates watcher triggers, Claude invocations, approval processing, and MCP actions
- **FR-036**: Orchestrator MUST implement file-based locking using PID files to prevent concurrent instances from conflicting
- **FR-037**: Orchestrator MUST queue overlapping scheduled tasks, processing them sequentially with priority ordering
- **FR-038**: System MUST support on-demand triggering via file drop monitoring, creating action files immediately when new files are detected in monitored folders

#### Audit and Monitoring

- **FR-039**: System MUST log all actions to dated JSON files in Logs/ with timestamp, action_type, actor, target, parameters, approval_status, approved_by, and result fields
- **FR-040**: System MUST retain audit logs for minimum 90 days, with automatic archival and compression for older logs
- **FR-041**: Dashboard.md MUST display real-time system status including: active watchers, pending actions count, recent activity (last 10 actions), and any error alerts
- **FR-042**: System MUST update Dashboard.md automatically whenever significant events occur (actions completed, errors encountered, approvals pending)
- **FR-043**: System MUST provide a /view-dashboard skill that displays formatted Dashboard.md content with color-coded status indicators

#### Agent Skills Requirement

- **FR-044**: ALL AI functionality MUST be implemented as Claude Agent Skills following the MCP Code Execution pattern for token efficiency and reusability
- **FR-045**: System MUST provide /setup-vault, /watcher-manager, /process-inbox, /view-dashboard, and /create-claude-skill as executable skills
- **FR-046**: New skills MUST be created using /create-claude-skill, which generates properly structured skill files with MCP integration

### Key Entities *(include if feature involves data)*

- **Action File**: Structured Markdown document in Needs_Action/ representing a detected event requiring AI processing. Contains YAML frontmatter with type, source, priority, timestamp, and status, and body with event details and suggested actions.

- **Plan File**: Structured Markdown document in Plans/ representing Claude's execution plan for an action. Contains objective, steps with checkboxes, approval requirements, dependencies, risk assessment, and completion status.

- **Approval Request**: Structured Markdown document in Pending_Approval/ representing a sensitive action requiring human approval. Contains action type, parameters (recipient, amount, etc.), reason, expiration timestamp, and approval instructions.

- **Watcher Process**: Long-running background service monitoring an external system (Gmail, WhatsApp, LinkedIn). Maintains processed message cache, implements retry logic, creates action files, and logs all activity.

- **MCP Server**: External integration server following Model Context Protocol, exposing capabilities (send_email, post_update) that Claude can invoke. Handles authentication, rate limiting, error handling, and action execution.

- **Audit Log Entry**: Structured JSON record documenting a system action. Contains timestamp, action_type, actor (Claude or human), target (recipient, system), parameters, approval_status, approved_by, result (success/failure), and error details if applicable.

- **Dashboard**: Living document (Dashboard.md) providing real-time system visibility. Shows active watchers, pending action count, recent activity list, error alerts, and system health indicators.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System monitors three communication channels (Gmail, WhatsApp, LinkedIn) concurrently with 99% uptime over 7 days
- **SC-002**: Urgent messages across all channels are detected and converted to action files within 5 minutes of arrival
- **SC-003**: Claude creates structured execution plans for 100% of action files, with clear steps and approval requirements identified
- **SC-004**: 100% of sensitive actions (new contact emails, payments >$100, public posts) require and receive human approval before execution
- **SC-005**: Approved email actions execute successfully within 60 seconds of approval with 95% success rate
- **SC-006**: Crashed watcher processes are automatically detected and restarted within 60 seconds with 100% recovery rate
- **SC-007**: All system actions are logged to audit trail with complete details (timestamp, actor, parameters, result) for 100% of executions
- **SC-008**: Dashboard provides accurate real-time status updates within 30 seconds of any significant system event
- **SC-009**: System processes scheduled daily briefings successfully 7 days per week without manual intervention
- **SC-010**: User can complete a full workflow (message detected → plan created → approval granted → action executed → result logged) in under 5 minutes for routine tasks
- **SC-011**: System reduces time spent on routine communication tasks by 60% compared to manual processing
- **SC-012**: 90% of action files are processed successfully without errors requiring human troubleshooting

## Dependencies and Assumptions *(mandatory)*

### Dependencies

- **Bronze Tier Completion**: All Bronze Tier deliverables must be fully functional (Obsidian vault, basic watcher, Claude integration, Skills infrastructure)
- **Gmail API Access**: Valid Gmail API credentials with OAuth2 consent screen approved for production use
- **WhatsApp Web Access**: Stable WhatsApp Web session with Playwright browser automation configured
- **LinkedIn API Access**: Valid LinkedIn API credentials with appropriate permissions for posting and messaging
- **Node.js and Python**: Node.js v24+ for MCP servers, Python 3.13+ for watcher scripts and orchestration
- **Process Manager**: PM2, supervisord, or equivalent process management tool installed and configured
- **Obsidian Vault**: Obsidian vault accessible via file system with proper read/write permissions for Claude Code
- **Stable Internet**: Reliable internet connectivity for API calls and webhook monitoring

### Assumptions

- User has valid accounts and API access for Gmail, WhatsApp Web, and LinkedIn
- User will configure OAuth2 credentials and API tokens according to security best practices
- Obsidian vault is stored locally (not on network drive) for reliable file system access
- User's machine has sufficient resources (8GB RAM minimum, 16GB recommended) for concurrent watchers
- User will review and approve pending actions at least once per day during business operations
- Company_Handbook.md contains clear approval thresholds and business rules for automated decision-making
- User accepts that WhatsApp Web automation may require periodic re-authentication (session expiry)
- LinkedIn API rate limits and terms of service permit automated posting at planned frequency
- User understands that dry-run mode must be used for testing before enabling production automation
- All credentials will be stored in .env files (excluded from version control) or OS-native secure storage
- User will monitor Dashboard.md daily for system health and error alerts during initial deployment
- Process manager will be configured to start watchers on system boot for 24/7 operation
- User's email and LinkedIn accounts have appropriate permissions for sending/posting on their behalf

## Scope *(mandatory)*

### In Scope

- Implementation of three watcher scripts (Gmail, WhatsApp, LinkedIn) with BaseWatcher inheritance
- Process management configuration using PM2 for all watcher processes
- /process-inbox skill for intelligent plan creation from action files
- /watcher-manager skill for process lifecycle management (start, stop, restart, status)
- Human-in-the-loop approval workflow with Pending_Approval/, Approved/, and Rejected/ folders
- Email MCP server with Gmail API integration for sending emails after approval
- LinkedIn MCP server with LinkedIn API integration for posting updates after approval
- Scheduling infrastructure using cron/Task Scheduler for routine operations (daily briefing)
- Watchdog process for automatic recovery of crashed watcher processes
- Comprehensive audit logging in structured JSON format
- Dashboard.md real-time updates for system monitoring
- All functionality implemented as Claude Agent Skills
- Dry-run mode support for safe testing of external actions
- Documentation for setup, configuration, and troubleshooting

### Out of Scope (Future Tiers)

- Facebook and Instagram integration (Gold Tier)
- Twitter/X integration (Gold Tier)
- Accounting system integration (Xero MCP) (Gold Tier)
- Weekly Business Audit and CEO Briefing generation (Gold Tier)
- Ralph Wiggum loop for fully autonomous multi-step completion (Gold Tier)
- Advanced error recovery and graceful degradation beyond basic retry logic
- Multi-user support or team collaboration features
- Mobile app or web interface for approval management
- Advanced analytics or reporting beyond basic audit logs
- Integration with CRM systems or project management tools
- Custom notification channels (SMS, Slack, etc.) beyond Dashboard.md
- Advanced natural language understanding for complex intent detection
- Machine learning for improving response suggestions over time

## Open Questions

*No open questions remain after specification creation. All reasonable defaults have been applied for unspecified details:*

- **Authentication methods**: Gmail API with OAuth2, WhatsApp Web with Playwright session persistence, LinkedIn API with OAuth2
- **Retry logic**: Exponential backoff with 3 max retries for transient errors
- **Approval expiration**: 24 hours default timeout for pending approvals
- **Rate limits**: 50 emails/hour default, LinkedIn API standard limits
- **Check intervals**: Gmail 120s, WhatsApp 30s, LinkedIn 300s (all configurable)
- **Process management**: PM2 recommended for cross-platform compatibility
- **Log retention**: 90 days minimum with automatic compression
- **Attachment limits**: 25MB for emails (Gmail API standard)
- **Error thresholds**: Alert human after 10 minutes of persistent API failures
