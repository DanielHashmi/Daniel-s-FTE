# Feature Specification: Gold Tier Autonomous Employee

**Feature Branch**: `003-gold-tier`
**Created**: 2026-01-19
**Status**: Draft
**Input**: User description: "Implement Gold Tier Autonomous Employee with full cross-domain integration, accounting (Xero), social media (Facebook/Instagram/Twitter), weekly business audit, CEO briefing, error recovery, comprehensive audit logging, and Ralph Wiggum loop for autonomous multi-step task completion"

## Overview

The Gold Tier represents the evolution from a functional assistant (Silver Tier) into a fully autonomous employee capable of managing complex, multi-step business operations without human intervention. This tier introduces true autonomy through persistent task execution, comprehensive business intelligence through accounting integration, expanded social media presence, and proactive business insights through weekly audits and CEO briefings. The system operates as a trusted business partner that not only executes tasks but provides strategic insights and recommendations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Autonomous Multi-Step Task Completion (Priority: P1)

As a business owner, I need the AI Employee to autonomously complete complex multi-step tasks from start to finish without stopping after each step, so that I can delegate entire workflows rather than individual actions and trust that tasks will be completed even when I'm unavailable.

**Why this priority**: Autonomous task completion is the defining capability that transforms the system from an assistant into a true employee. Without this, the AI requires constant human supervision and cannot operate independently. This is the foundation that enables all other Gold Tier capabilities to deliver value.

**Independent Test**: Can be fully tested by assigning a multi-step task (e.g., "Process all pending invoices: generate PDFs, send emails, log transactions, update dashboard"), verifying the system continues working through all steps without stopping, and confirming completion only when all steps are done. Delivers immediate value by eliminating the need for human intervention between task steps.

**Acceptance Scenarios**:

1. **Given** a task file exists in Needs_Action/ with 5 sequential steps (read data, generate document, send email, log transaction, update dashboard), **When** the Ralph Wiggum loop processes the task, **Then** the system executes all 5 steps sequentially, updates progress after each step, and only exits when the task file is moved to Done/ or outputs the completion promise
2. **Given** the AI Employee is executing step 3 of a 5-step task and encounters a transient error (network timeout), **When** the error occurs, **Then** the system retries the failed step up to 3 times with exponential backoff, logs the retry attempts, and continues to the next step if successful or pauses for human review if all retries fail
3. **Given** a multi-step task requires human approval at step 4, **When** the system reaches that step, **Then** it creates an approval request, pauses execution at that step, and automatically resumes from step 4 once approval is granted without requiring manual restart
4. **Given** the Ralph Wiggum loop is executing a task with a maximum of 10 iterations configured, **When** the system completes the task in 7 iterations, **Then** it exits successfully with completion status and logs the number of iterations used
5. **Given** the Ralph Wiggum loop reaches the maximum iteration limit (10) without completing the task, **When** the limit is reached, **Then** the system stops execution, logs the incomplete state, creates a human review request with detailed progress information, and does not attempt automatic restart

---

### User Story 2 - Accounting Integration and Financial Intelligence (Priority: P1)

As a business owner, I need the AI Employee to integrate with my Xero accounting system to automatically track revenue, expenses, and financial transactions, so that I have real-time visibility into business finances and can make data-driven decisions without manual bookkeeping.

**Why this priority**: Financial intelligence is critical for business operations and decision-making. Accounting integration provides the data foundation for the CEO Briefing feature and enables automated financial tracking. This is P1 because it's a prerequisite for the weekly business audit and delivers immediate value through automated bookkeeping.

**Independent Test**: Can be tested by configuring Xero API credentials, triggering a transaction sync, verifying that revenue and expense data is retrieved and stored in the vault, and confirming that financial summaries are generated accurately. Delivers value by eliminating manual financial data entry and providing real-time financial visibility.

**Acceptance Scenarios**:

1. **Given** Xero API credentials are configured in environment variables, **When** the accounting sync process runs, **Then** the system authenticates with Xero, retrieves all transactions from the past 30 days, and stores them in structured format in the vault's Accounting/ folder
2. **Given** new transactions exist in Xero since the last sync, **When** the scheduled sync runs (daily at 6 AM), **Then** only new transactions are retrieved, duplicate detection prevents re-importing existing transactions, and the sync completes in under 2 minutes for up to 1000 transactions
3. **Given** transaction data includes invoices, payments, and expenses, **When** the system categorizes transactions, **Then** each transaction is tagged with type (revenue/expense), category (based on Xero chart of accounts), client/vendor name, amount, and date
4. **Given** a Xero API call fails due to rate limiting, **When** the error occurs, **Then** the system logs the rate limit error, waits for the specified retry-after period, and automatically retries the request without losing data or requiring manual intervention
5. **Given** financial data exists in the vault for the current month, **When** a financial summary is requested, **Then** the system calculates total revenue, total expenses, net profit, top clients by revenue, and largest expense categories, presenting results in a structured markdown report

---

### User Story 3 - Weekly Business Audit and CEO Briefing (Priority: P1)

As a business owner, I need the AI Employee to automatically generate a comprehensive weekly business briefing every Monday morning that analyzes revenue, completed tasks, bottlenecks, and proactive suggestions, so that I start each week with clear visibility into business performance and actionable insights without manual reporting.

**Why this priority**: The CEO Briefing is the signature feature that demonstrates true business partnership. It transforms the AI from a task executor into a strategic advisor. This is P1 because it delivers the highest perceived value and differentiates the Gold Tier from all other automation tools.

**Independent Test**: Can be tested by scheduling the briefing generation for a specific time, verifying it runs automatically, and confirming the generated briefing includes all required sections (revenue summary, completed tasks, bottlenecks, proactive suggestions) with accurate data from accounting and task tracking systems. Delivers immediate value by providing weekly business intelligence without manual effort.

**Acceptance Scenarios**:

1. **Given** the system is configured to generate CEO Briefings every Monday at 7 AM, **When** Monday 7 AM arrives, **Then** the briefing generation process runs automatically, analyzes data from the past 7 days, and creates a briefing file in the Briefings/ folder within 5 minutes
2. **Given** financial data exists in Xero for the past week, **When** the briefing is generated, **Then** the revenue section includes total weekly revenue, month-to-date revenue, progress toward monthly goal (percentage), and trend indicator (on track/behind/ahead)
3. **Given** task files exist in the Done/ folder from the past week, **When** the briefing analyzes completed tasks, **Then** it lists all completed tasks with completion dates, identifies tasks that took longer than expected (based on historical averages), and highlights any tasks that missed deadlines
4. **Given** subscription transactions exist in the accounting data, **When** the briefing analyzes costs, **Then** it identifies recurring subscriptions, flags subscriptions with no recent usage activity (based on login tracking or transaction patterns), and suggests cancellation candidates with cost savings estimates
5. **Given** upcoming deadlines exist in the Business_Goals.md file, **When** the briefing is generated, **Then** it includes a section listing deadlines in the next 14 days, calculates days remaining for each, and flags any deadlines at risk based on current progress

---

### User Story 4 - Comprehensive Error Recovery and Graceful Degradation (Priority: P1)

As a business owner relying on autonomous operations, I need the AI Employee to handle errors gracefully, recover from failures automatically when possible, and degrade functionality safely when recovery isn't possible, so that the system remains reliable and doesn't require constant monitoring or manual intervention.

**Why this priority**: Error recovery is non-negotiable for autonomous operations. Without robust error handling, the system cannot be trusted to operate independently. This is P1 because it's a prerequisite for true autonomy and prevents the system from becoming a liability.

**Independent Test**: Can be tested by simulating various failure scenarios (network outages, API rate limits, authentication failures, corrupted data), verifying the system detects each error type, attempts appropriate recovery actions, and degrades gracefully when recovery fails. Delivers value by ensuring system reliability and reducing operational overhead.

**Acceptance Scenarios**:

1. **Given** an API call fails with a transient network error (timeout, connection refused), **When** the error is detected, **Then** the system logs the error with full context, waits for an exponentially increasing delay (1s, 2s, 4s), retries up to 3 times, and only escalates to human review if all retries fail
2. **Given** an authentication token expires during operation, **When** the system detects an authentication error (401 Unauthorized), **Then** it attempts to refresh the token using stored refresh credentials, retries the original request with the new token, and only alerts the human if token refresh fails
3. **Given** a critical component (Gmail API) becomes unavailable, **When** the system detects the outage, **Then** it continues operating other components (WhatsApp watcher, LinkedIn watcher, orchestrator), queues any Gmail-dependent actions for later processing, and logs the degraded state in the Dashboard
4. **Given** a data file becomes corrupted or unreadable, **When** the system attempts to read the file, **Then** it detects the corruption, moves the corrupted file to a Quarantine/ folder with timestamp, logs the error with file details, creates a human review request, and continues processing other files
5. **Given** the orchestrator process crashes unexpectedly, **When** the watchdog process detects the crash (missing heartbeat or PID check), **Then** it automatically restarts the orchestrator within 30 seconds, logs the crash with stack trace if available, and sends an alert notification to the human

---

### User Story 5 - Expanded Social Media Presence (Facebook, Instagram, Twitter) (Priority: P2)

As a business owner focused on lead generation and brand visibility, I need the AI Employee to automatically post business updates to Facebook, Instagram, and Twitter in addition to LinkedIn, so that I maintain consistent multi-platform social media presence without managing each platform individually.

**Why this priority**: Multi-platform social media presence amplifies brand visibility and lead generation. This is P2 because it builds on the LinkedIn posting capability from Silver Tier and delivers incremental value, but isn't critical for core business operations.

**Independent Test**: Can be tested by scheduling posts for each platform, verifying approval requests are created with platform-specific formatting, approving the posts, and confirming they publish successfully to Facebook, Instagram, and Twitter with correct content and formatting. Delivers value by expanding social media reach with minimal additional effort.

**Acceptance Scenarios**:

1. **Given** a social media post schedule is configured for Facebook, Instagram, and Twitter, **When** the scheduled time arrives, **Then** the system generates platform-appropriate content (respecting character limits and formatting rules for each platform), creates separate approval requests for each platform, and waits for human approval before posting
2. **Given** an approved post exists for Instagram, **When** the Instagram MCP executes the post, **Then** the post is published with the specified image, caption, and hashtags, the post URL is captured, and the result is logged in the audit trail with platform identifier
3. **Given** a Twitter post exceeds the character limit (280 characters), **When** the system prepares the post, **Then** it automatically truncates the content intelligently (preserving key message and hashtags), adds an ellipsis indicator, and flags the truncation in the approval request for human review
4. **Given** Facebook API rate limits are reached, **When** additional post attempts occur, **Then** the system queues the posts, respects the rate limit window, schedules retries at appropriate intervals, and logs the rate limit event without losing queued posts
5. **Given** posts are published across multiple platforms (LinkedIn, Facebook, Instagram, Twitter), **When** the weekly CEO Briefing is generated, **Then** it includes a social media summary section showing total posts per platform, engagement metrics if available, and posting consistency (posts per week vs target)

---

### User Story 6 - Comprehensive Audit Logging and Compliance (Priority: P2)

As a business owner concerned about accountability and compliance, I need the AI Employee to log every action, decision, and approval with complete context and timestamps, so that I can audit system behavior, investigate issues, and demonstrate compliance with business policies.

**Why this priority**: Comprehensive audit logging is essential for accountability, debugging, and compliance. This is P2 because it enhances the existing logging from Silver Tier but isn't blocking for core functionality. It becomes critical as the system handles more sensitive operations.

**Independent Test**: Can be tested by executing various actions (emails, posts, financial transactions, approvals), verifying each action generates a detailed log entry with all required fields, and confirming logs are stored in structured format with proper retention. Delivers value by providing complete visibility into system operations.

**Acceptance Scenarios**:

1. **Given** the AI Employee executes any external action (email send, social post, API call), **When** the action completes, **Then** a log entry is created with timestamp (ISO 8601), action type, actor (AI or human), target (recipient/platform), parameters (sanitized to exclude secrets), approval status, result (success/failure), and execution duration
2. **Given** log entries are created throughout the day, **When** midnight arrives, **Then** all logs from the previous day are consolidated into a single JSON file named YYYY-MM-DD.json in the Logs/ folder, the file is validated for proper JSON structure, and a backup is created
3. **Given** log files exist for more than 90 days, **When** the log retention process runs (weekly), **Then** logs older than 90 days are moved to an Archive/ subfolder, compressed to save space, and a retention summary is logged
4. **Given** a human reviews an approval request and approves it, **When** the approval is processed, **Then** the log entry includes the approval timestamp, the human's identifier (username or email), the approval method (file move to Approved/), and links to both the approval request and the executed action
5. **Given** an error occurs during any operation, **When** the error is logged, **Then** the log entry includes error type, error message, stack trace (if available), the operation that failed, retry attempts made, and whether the error was recovered or escalated

---

### User Story 7 - Architecture Documentation and Knowledge Transfer (Priority: P3)

As a developer or business owner, I need comprehensive documentation of the AI Employee architecture, design decisions, lessons learned, and operational procedures, so that I can understand how the system works, troubleshoot issues, onboard new team members, and make informed decisions about future enhancements.

**Why this priority**: Documentation is essential for long-term maintainability and knowledge transfer. This is P3 because it doesn't add functional capabilities but is critical for sustainability. It can be completed after core functionality is working.

**Independent Test**: Can be tested by reviewing the generated documentation for completeness (architecture diagrams, component descriptions, setup instructions, troubleshooting guides, lessons learned), verifying all sections are present and accurate, and confirming a new user can set up the system following the documentation. Delivers value by reducing onboarding time and operational overhead.

**Acceptance Scenarios**:

1. **Given** the Gold Tier implementation is complete, **When** the architecture documentation is generated, **Then** it includes system architecture diagram, component descriptions, data flow diagrams, integration points, security model, and deployment architecture
2. **Given** the system has been operating for at least 30 days, **When** the lessons learned document is created, **Then** it includes challenges encountered, solutions implemented, design decisions and rationale, performance optimizations, and recommendations for future improvements
3. **Given** a new user wants to set up the AI Employee, **When** they follow the setup documentation, **Then** they can complete the installation, configuration, and initial testing in under 4 hours without external assistance, and the system operates correctly on first run
4. **Given** an operational issue occurs, **When** the operator consults the troubleshooting guide, **Then** they find the issue category (setup, runtime, integration, performance), diagnostic steps, common causes, and resolution procedures
5. **Given** the documentation is complete, **When** it's reviewed for quality, **Then** all code examples are tested and working, all configuration examples are valid, all links are functional, and all screenshots are current and accurate

---

### Edge Cases

- What happens when the Ralph Wiggum loop encounters a step that requires human approval but the approval expires before being granted?
- How does the system handle Xero API authentication when the OAuth token expires during a sync operation?
- What happens when the CEO Briefing generation runs but no financial data is available (Xero not configured or sync failed)?
- How does the system handle posting to social media when one platform is down but others are operational?
- What happens when audit log files become corrupted or the Logs/ folder runs out of disk space?
- How does the system handle conflicting scheduled tasks (e.g., CEO Briefing generation and accounting sync both scheduled for 7 AM)?
- What happens when a multi-step task includes a step that permanently fails (e.g., invalid email address) and cannot be retried?
- How does the system handle timezone differences when scheduling tasks and generating time-based reports?
- What happens when the watchdog process itself crashes or becomes unresponsive?
- How does the system handle partial data corruption where some fields in a file are readable but others are not?

## Requirements *(mandatory)*

### Functional Requirements

#### Autonomous Task Completion (Ralph Wiggum Loop)

- **FR-001**: System MUST implement a persistent task execution loop that continues processing a task until completion or maximum iteration limit is reached
- **FR-002**: System MUST support configurable maximum iteration limits (default 10) to prevent infinite loops
- **FR-003**: System MUST detect task completion through two methods: file movement to Done/ folder OR explicit completion promise output
- **FR-004**: System MUST preserve full execution context between iterations, including previous outputs, errors, and state
- **FR-005**: System MUST log each iteration with timestamp, iteration number, actions taken, and current state
- **FR-006**: System MUST pause execution when human approval is required and automatically resume after approval is granted
- **FR-007**: System MUST create detailed human review requests when maximum iterations are reached without completion

#### Accounting Integration (Xero)

- **FR-008**: System MUST integrate with Xero accounting system via official Xero MCP Server
- **FR-009**: System MUST authenticate with Xero using OAuth 2.0 with token refresh capability
- **FR-010**: System MUST sync transactions from Xero on a configurable schedule (default: daily at 6 AM)
- **FR-011**: System MUST retrieve invoices, payments, expenses, and bank transactions from Xero
- **FR-012**: System MUST store financial data in structured format in vault's Accounting/ folder
- **FR-013**: System MUST detect and prevent duplicate transaction imports
- **FR-014**: System MUST categorize transactions by type (revenue/expense), category, client/vendor, amount, and date
- **FR-015**: System MUST calculate financial summaries including total revenue, total expenses, net profit, and category breakdowns
- **FR-016**: System MUST handle Xero API rate limits with automatic retry and backoff

#### Weekly CEO Briefing

- **FR-017**: System MUST generate CEO Briefing automatically on a configurable schedule (default: Monday 7 AM)
- **FR-018**: CEO Briefing MUST include revenue summary with weekly total, month-to-date, goal progress, and trend
- **FR-019**: CEO Briefing MUST include completed tasks list with completion dates and duration analysis
- **FR-020**: CEO Briefing MUST identify bottlenecks by comparing actual task duration to expected duration
- **FR-021**: CEO Briefing MUST analyze subscription costs and flag unused subscriptions for review
- **FR-022**: CEO Briefing MUST include upcoming deadlines from Business_Goals.md with days remaining
- **FR-023**: CEO Briefing MUST provide proactive suggestions based on data analysis (cost optimization, deadline risks, revenue trends)
- **FR-024**: CEO Briefing MUST be stored in Briefings/ folder with filename format YYYY-MM-DD_Monday_Briefing.md

#### Error Recovery and Graceful Degradation

- **FR-025**: System MUST implement exponential backoff retry logic for transient errors (network timeouts, temporary API failures)
- **FR-026**: System MUST attempt up to 3 retries for transient errors before escalating to human review
- **FR-027**: System MUST automatically refresh expired authentication tokens when possible
- **FR-028**: System MUST continue operating non-affected components when one component fails
- **FR-029**: System MUST queue actions for failed components and process them when component recovers
- **FR-030**: System MUST quarantine corrupted files and create human review requests
- **FR-031**: System MUST implement watchdog process that monitors critical processes and restarts them on failure
- **FR-032**: System MUST send alert notifications when critical failures occur
- **FR-033**: System MUST log all errors with full context including error type, message, stack trace, and recovery actions taken

#### Social Media Expansion

- **FR-034**: System MUST integrate with Facebook API for posting business updates
- **FR-035**: System MUST integrate with Instagram API for posting images with captions and hashtags
- **FR-036**: System MUST integrate with Twitter API for posting tweets
- **FR-037**: System MUST generate platform-appropriate content respecting character limits and formatting rules
- **FR-038**: System MUST create separate approval requests for each social media platform
- **FR-039**: System MUST handle platform-specific rate limits independently
- **FR-040**: System MUST capture post URLs and engagement metrics when available
- **FR-041**: System MUST include social media summary in CEO Briefing showing posts per platform and consistency

#### Comprehensive Audit Logging

- **FR-042**: System MUST log every external action with timestamp, action type, actor, target, parameters, approval status, result, and duration
- **FR-043**: System MUST sanitize log entries to exclude secrets and credentials
- **FR-044**: System MUST consolidate daily logs into single JSON file at midnight
- **FR-045**: System MUST retain logs for minimum 90 days before archiving
- **FR-046**: System MUST compress archived logs to save disk space
- **FR-047**: System MUST validate log file integrity and alert on corruption
- **FR-048**: System MUST include approval audit trail with approver identity and timestamp

#### Documentation

- **FR-049**: System MUST include architecture documentation with diagrams, component descriptions, and data flows
- **FR-050**: System MUST include setup documentation with step-by-step installation and configuration instructions
- **FR-051**: System MUST include troubleshooting guide with common issues and resolutions
- **FR-052**: System MUST include lessons learned document with challenges, solutions, and recommendations
- **FR-053**: System MUST include operational procedures for monitoring, maintenance, and updates

#### Agent Skills

- **FR-054**: All AI functionality MUST be implemented as Agent Skills following the MCP Code Execution pattern
- **FR-055**: System MUST include skills for: accounting sync, briefing generation, social media posting, error recovery, and audit log management

### Key Entities

- **Task Execution State**: Represents the current state of a multi-step task including iteration count, completed steps, pending steps, errors encountered, and completion status
- **Financial Transaction**: Represents a business transaction from Xero including transaction ID, type (invoice/payment/expense), amount, date, client/vendor, category, and reconciliation status
- **CEO Briefing**: Represents a weekly business intelligence report including revenue summary, task analysis, bottleneck identification, cost optimization suggestions, and deadline tracking
- **Audit Log Entry**: Represents a single logged action including timestamp, action type, actor, target, parameters, approval status, result, duration, and error details if applicable
- **Social Media Post**: Represents a scheduled or published social media update including platform, content, media attachments, post URL, publication timestamp, and engagement metrics
- **Error Recovery Record**: Represents an error event and recovery attempt including error type, original operation, retry attempts, recovery actions taken, and final outcome
- **Subscription Analysis**: Represents a recurring subscription identified in financial data including service name, cost, frequency, last usage date, and cancellation recommendation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI Employee completes multi-step tasks (5+ steps) autonomously without human intervention between steps in 95% of cases
- **SC-002**: System recovers automatically from transient errors (network timeouts, rate limits) in 90% of cases without human intervention
- **SC-003**: CEO Briefing is generated automatically every Monday morning within 5 minutes of scheduled time with 100% reliability
- **SC-004**: Financial data syncs from Xero daily with 99% success rate and zero duplicate transactions
- **SC-005**: Social media posts are published to all configured platforms (LinkedIn, Facebook, Instagram, Twitter) with 95% success rate
- **SC-006**: System operates continuously for 7 days without requiring manual intervention or restart
- **SC-007**: All external actions are logged with complete audit trail achieving 100% logging coverage
- **SC-008**: New users can set up and configure the system in under 4 hours following documentation
- **SC-009**: System identifies cost optimization opportunities (unused subscriptions) with 80% accuracy
- **SC-010**: Task completion time improves by 60% compared to Silver Tier due to autonomous multi-step execution
- **SC-011**: Business owner spends less than 30 minutes per week reviewing approvals and briefings (down from 2+ hours of manual work)
- **SC-012**: System handles component failures gracefully, maintaining 80% functionality when one component is down

## Assumptions

- Xero account is already set up with business financial data
- Social media accounts (Facebook, Instagram, Twitter) are created and API access is approved
- Business_Goals.md file is maintained with current goals, targets, and deadlines
- Historical task data exists to establish baseline durations for bottleneck detection
- Subscription patterns can be identified through transaction descriptions and merchant names
- System has sufficient disk space for 90 days of audit logs (estimated 1-5 GB depending on activity)
- Network connectivity is generally reliable with occasional transient failures
- OAuth tokens can be refreshed programmatically without manual re-authentication
- Process manager (PM2 or supervisord) is configured for production deployment
- System timezone is configured correctly for scheduled task execution

## Dependencies

- **Silver Tier Completion**: All Silver Tier capabilities must be fully operational (multi-channel monitoring, planning, HITL approval, email/LinkedIn MCP)
- **Xero MCP Server**: Official Xero MCP Server must be installed and configured
- **Social Media APIs**: Facebook Graph API, Instagram Graph API, and Twitter API v2 access must be approved
- **Process Manager**: PM2 or supervisord must be installed for watchdog functionality
- **OAuth 2.0 Libraries**: Libraries for handling OAuth token refresh must be available
- **Disk Space**: Sufficient storage for audit logs, financial data, and briefing archives
- **Scheduled Task System**: Cron (Linux/Mac) or Task Scheduler (Windows) for scheduled operations

## Out of Scope

- Real-time financial analytics dashboard (beyond weekly briefing)
- Integration with accounting systems other than Xero
- Social media engagement tracking and analytics (beyond basic post metrics)
- Multi-user access control and permissions
- Mobile app or web interface for system management
- Integration with project management tools (Asana, Jira, etc.)
- Customer relationship management (CRM) integration
- Automated tax preparation and filing
- Multi-currency support for international transactions
- Advanced AI training or model fine-tuning
- Integration with communication platforms beyond those specified (Slack, Teams, etc.)

## Security Considerations

- OAuth tokens for Xero and social media platforms must be stored securely using OS-native credential storage
- Audit logs must sanitize sensitive data (passwords, tokens, API keys) before writing
- Financial data must be encrypted at rest in the vault
- Social media posting must require human approval for all posts to prevent unauthorized brand communications
- Error recovery must not expose sensitive information in error messages or logs
- Watchdog process must run with minimal privileges to prevent security escalation
- API rate limiting must be respected to prevent account suspension
- All external API calls must use HTTPS with certificate validation
- Backup credentials must be stored separately from primary credentials
- System must implement rate limiting on approval requests to prevent approval fatigue

## Notes

- The Ralph Wiggum loop is named after the Simpsons character and refers to the persistent, iterative execution pattern
- CEO Briefing feature is the signature capability that demonstrates business partnership value
- Error recovery is critical for autonomous operations and must be thoroughly tested
- Social media expansion builds on LinkedIn capability from Silver Tier
- Documentation is essential for long-term sustainability but can be completed after core functionality
- All AI functionality must follow Agent Skills pattern for consistency and maintainability
- System should be designed for 24/7 operation with minimal human oversight
- Weekly briefing schedule can be customized but Monday morning is recommended for weekly planning
