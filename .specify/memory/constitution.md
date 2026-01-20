<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0 (Added Platinum Tier section)
- Modified Principles: None
- Added Sections: Platinum Tier Requirements
- Removed Sections: None
- Templates Status:
  ✅ spec-template.md - No changes needed (tiered delivery already supported)
  ✅ plan-template.md - No changes needed (constitution check present)
  ✅ tasks-template.md - No changes needed (phase-based structure supports new tier)
  ✅ commands/*.md - No outdated references found
- Follow-up TODOs: None
-->

# Personal AI Employee Constitution

## Core Principles

### I. Local-First Architecture (NON-NEGOTIABLE)

All sensitive data MUST remain on the user's local machine by default. The Obsidian vault serves as the primary knowledge base and dashboard. External API calls are permitted only for necessary integrations (Gmail, WhatsApp, banking) and MUST use secure credential management.

**Rationale**: Privacy is paramount when handling personal communications, financial data, and business information. Local-first ensures user control and reduces attack surface.

### II. Human-in-the-Loop for Sensitive Actions (NON-NEGOTIABLE)

The AI Employee MUST NOT execute sensitive actions without explicit human approval. Sensitive actions include:
- Financial transactions (payments, transfers)
- Communications to new contacts
- Bulk operations (mass emails, social media posts)
- Irreversible actions (deletions, contract signing)

**Implementation**: Create approval request files in `/Pending_Approval/` folder. Actions execute only after human moves file to `/Approved/`.

**Rationale**: Autonomous systems require safeguards. HITL prevents costly mistakes while maintaining automation benefits.

### III. Agent Skills First

All AI functionality MUST be implemented as Agent Skills following the Claude Agent Skills framework. Skills provide:
- Reusable, composable capabilities
- Clear interfaces and documentation
- Version control and testing
- Discoverability and maintainability

**Rationale**: Skills transform ad-hoc automation into maintainable, professional-grade capabilities that can be shared and improved over time.

### IV. Security & Credential Management (NON-NEGOTIABLE)

Credentials and secrets MUST NEVER be stored in plain text or committed to version control:
- Use environment variables for API keys
- Store sensitive credentials in OS-native secure storage (Keychain, Credential Manager, 1Password CLI)
- Maintain `.env` files in `.gitignore`
- Rotate credentials monthly and after any suspected breach
- Implement dry-run mode for all external actions during development

**Rationale**: A compromised AI Employee could access email, banking, and communications. Defense-in-depth is essential.

### V. Comprehensive Audit Logging

Every action the AI Employee takes MUST be logged with:
- Timestamp (ISO 8601 format)
- Action type and target
- Actor (claude_code, human, watcher)
- Parameters and result
- Approval status and approver

Logs MUST be stored in `/Vault/Logs/YYYY-MM-DD.json` and retained for minimum 90 days.

**Rationale**: Audit trails enable debugging, accountability, and security incident response. They answer "what did my AI do while I was away?"

### VI. Graceful Degradation & Error Recovery

The system MUST continue operating when components fail:
- Watchers queue data when Claude Code unavailable
- Failed processes auto-restart via watchdog
- Transient errors trigger exponential backoff retry
- Authentication failures pause operations and alert human
- Banking/payment errors NEVER auto-retry

**Implementation**: Use retry decorators, watchdog processes, and error categorization (transient, authentication, logic, data, system).

**Rationale**: 24/7 autonomous operation requires resilience. Graceful degradation prevents cascading failures.

### VII. Tiered Delivery & Incremental Value

Features MUST be delivered in tiers to enable progressive enhancement:
- **Bronze Tier**: Minimum viable foundation (Obsidian vault, one watcher, basic Claude integration)
- **Silver Tier**: Functional assistant (multiple watchers, MCP servers, HITL workflows, scheduling)
- **Gold Tier**: Autonomous employee (cross-domain integration, accounting, social media, CEO briefings, Ralph Wiggum loop)

Each tier MUST be independently functional and testable before advancing.

**Rationale**: Tiered delivery reduces risk, enables early feedback, and provides clear milestones. Users can stop at any tier based on needs.

### VIII. Observability & Transparency

The system MUST provide visibility into its operations:
- Real-time dashboard (`Dashboard.md`) showing status, pending actions, recent activity
- Clear logging of all decisions and actions
- Human-readable file formats (Markdown, JSON)
- Disclosure of AI involvement in external communications

**Rationale**: Users must understand what their AI Employee is doing. Transparency builds trust and enables effective oversight.

### IX. Modular Integration via MCP

External integrations MUST use Model Context Protocol (MCP) servers:
- Each integration (email, browser, calendar) as separate MCP server
- MCP servers expose well-defined capabilities
- Configuration in `~/.config/claude-code/mcp.json`
- Servers support dry-run mode for testing

**Rationale**: MCP provides standardized, maintainable integration patterns. Modularity enables independent testing and replacement.

## Security Requirements

### Permission Boundaries

| Action Category | Auto-Approve Threshold | Always Require Approval |
|-----------------|------------------------|-------------------------|
| Email replies | To known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

### Sandboxing During Development

- `DEV_MODE` flag MUST prevent real external actions
- All action scripts MUST support `--dry-run` flag
- Use test/sandbox accounts during development
- Implement rate limiting (max 10 emails/hour, max 3 payments/hour)

### Encryption & Data Protection

- Consider encrypting Obsidian vault at rest
- Minimize data collection (only capture what's necessary)
- Understand what data leaves system via APIs
- Implement data retention policies per entity type

## Development Workflow

### Watcher Development

All Watchers MUST:
- Inherit from `BaseWatcher` abstract class
- Implement `check_for_updates()` and `create_action_file()` methods
- Create structured Markdown files in `/Needs_Action/` with YAML frontmatter
- Handle errors gracefully and log failures
- Support configurable check intervals
- Use process managers (PM2, supervisord) for production deployment

### MCP Server Development

All MCP servers MUST:
- Follow MCP specification and protocol
- Expose clear capability descriptions
- Support dry-run mode via environment variable
- Implement proper error handling and timeouts
- Log all actions for audit trail
- Be independently testable

### Orchestration Requirements

The master orchestrator MUST:
- Monitor folder changes (`/Needs_Action/`, `/Approved/`)
- Schedule periodic tasks (daily briefings, weekly audits)
- Manage process lifecycle (start, stop, restart watchers)
- Implement watchdog for failed processes
- Coordinate Claude Code invocations
- Handle Ralph Wiggum loop for multi-step tasks

### Testing Strategy

- **Bronze Tier**: Manual testing of core workflows
- **Silver Tier**: Integration tests for watcher → Claude → MCP flows
- **Gold Tier**: End-to-end tests for complete user journeys, error recovery tests

### Documentation Requirements

Each component MUST include:
- Setup instructions with prerequisites
- Configuration examples
- Security considerations
- Troubleshooting guide
- Example usage

## Tier-Specific Requirements

### Bronze Tier (Foundation)

**Mandatory Deliverables**:
- Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- Folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- One working Watcher (Gmail OR file system)
- Claude Code reading from and writing to vault
- All AI functionality as Agent Skills

**Success Criteria**: Can detect one input type and create actionable files for Claude.

### Silver Tier (Functional Assistant)

**Mandatory Deliverables** (Bronze + following):
- Two or more Watchers (Gmail + WhatsApp + LinkedIn)
- Automated LinkedIn posting for business/sales
- Claude reasoning loop creating `Plan.md` files
- One working MCP server (email sending)
- HITL approval workflow for sensitive actions
- Scheduling via cron or Task Scheduler
- All AI functionality as Agent Skills

**Success Criteria**: Can autonomously handle multiple input types, create plans, and execute approved actions.

### Gold Tier (Autonomous Employee)

**Mandatory Deliverables** (Silver + following):
- Full cross-domain integration (Personal + Business)
- Xero accounting integration via MCP server
- Facebook, Instagram, Twitter (X) integration with posting and summaries
- Multiple MCP servers for different action types
- Weekly Business and Accounting Audit with CEO Briefing
- Error recovery and graceful degradation
- Comprehensive audit logging
- Ralph Wiggum loop for autonomous multi-step completion
- Architecture documentation and lessons learned
- All AI functionality as Agent Skills

**Success Criteria**: Can operate autonomously for extended periods, generate proactive insights, and handle complex multi-step workflows.

### Platinum Tier (Enterprise Assistant)

**Mandatory Deliverables** (Gold + following):
- Enterprise governance and compliance tracking (`/enterprise-governance`)
- Multi-team coordination (`/multi-team-sync`)
- Automated compliance reporting (`/compliance-audit`)
- Advanced scalability for enterprise/team use
- All AI functionality as Agent Skills

**Success Criteria**: Can operate in enterprise environments with full compliance, multi-team synchronization, governance controls, and cross-domain orchestration.

## Ethics & Responsible Automation

### When AI MUST NOT Act Autonomously

- Emotional contexts (condolences, conflict resolution, sensitive negotiations)
- Legal matters (contract signing, legal advice, regulatory filings)
- Medical decisions affecting health
- Financial edge cases (unusual transactions, new recipients, large amounts)
- Irreversible actions that cannot be easily undone

### Transparency Principles

- Disclose AI involvement in external communications (email signatures)
- Maintain complete audit trails
- Provide opt-out mechanisms for contacts preferring human-only communication
- Schedule weekly reviews of AI decisions to catch drift

### Human Accountability

The human user remains fully responsible for all AI Employee actions. Required oversight schedule:
- **Daily**: 2-minute dashboard check
- **Weekly**: 15-minute action log review
- **Monthly**: 1-hour comprehensive audit
- **Quarterly**: Full security and access review

## Governance

This constitution supersedes all other development practices and guidelines. All features, code, and integrations MUST comply with these principles.

### Amendment Process

1. Proposed amendments MUST be documented with rationale
2. Impact analysis MUST identify affected components and templates
3. Version number MUST be incremented per semantic versioning:
   - **MAJOR**: Backward-incompatible changes, principle removals/redefinitions
   - **MINOR**: New principles, materially expanded guidance
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements
4. All dependent templates MUST be updated before amendment approval
5. Migration plan REQUIRED for breaking changes

### Compliance Verification

- All PRs and code reviews MUST verify constitutional compliance
- Complexity violations MUST be explicitly justified in `plan.md`
- Security requirements MUST be validated before production deployment
- Tier requirements MUST be met before advancing to next tier

### Version Control

This constitution is version-controlled alongside code. Changes MUST be committed with clear messages explaining the amendment and its impact.

**Version**: 1.1.0 | **Ratified**: 2026-01-14 | **Last Amended**: 2026-01-20
