# Data Model: Gold Tier Autonomous Employee

**Feature**: Gold Tier Autonomous Employee
**Date**: 2026-01-19
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the data entities for Gold Tier implementation. All entities are stored in file-based format (Markdown with YAML frontmatter, JSON) in the Obsidian vault, maintaining the local-first architecture principle.

---

## Core Entities

### 1. Task Execution State

**Purpose**: Represents the current state of a multi-step task being executed by the Ralph Wiggum loop.

**Storage Location**: `.claude/state/ralph-state-{task_id}.json`

**Schema**:
```json
{
  "task_id": "string (UUID)",
  "task_file": "string (path to original task file)",
  "prompt": "string (initial task prompt)",
  "iteration": "integer (current iteration count)",
  "max_iterations": "integer (maximum allowed iterations)",
  "completion_strategy": "enum (file_movement | promise_based)",
  "completion_promise": "string (promise marker to detect)",
  "status": "enum (running | paused_approval | completed | failed | max_iterations)",
  "started_at": "string (ISO 8601 timestamp)",
  "last_iteration_at": "string (ISO 8601 timestamp)",
  "completed_steps": ["array of strings (step descriptions)"],
  "pending_steps": ["array of strings (remaining steps)"],
  "errors_encountered": [
    {
      "iteration": "integer",
      "error_type": "string",
      "error_message": "string",
      "recovery_attempted": "boolean",
      "recovery_successful": "boolean"
    }
  ],
  "approval_requests": [
    {
      "step": "string",
      "approval_file": "string (path to approval request)",
      "status": "enum (pending | approved | rejected)"
    }
  ]
}
```

**Validation Rules**:
- `iteration` must be <= `max_iterations`
- `max_iterations` must be >= 1 and <= 50
- `status` transitions: running → paused_approval → running → completed/failed/max_iterations
- `started_at` and `last_iteration_at` must be valid ISO 8601 timestamps

**State Transitions**:
```
running → paused_approval (when HITL approval required)
paused_approval → running (when approval granted)
running → completed (when task file moves to Done/)
running → failed (when unrecoverable error occurs)
running → max_iterations (when iteration limit reached)
```

---

### 2. Financial Transaction

**Purpose**: Represents a business transaction from Xero accounting system.

**Storage Location**: `AI_Employee_Vault/Accounting/transactions/{YYYY-MM}/transactions.json`

**Schema**:
```json
{
  "transaction_id": "string (Xero transaction ID)",
  "type": "enum (invoice | payment | expense | bank_transaction)",
  "date": "string (ISO 8601 date)",
  "amount": "number (decimal, 2 places)",
  "currency": "string (ISO 4217 currency code, default USD)",
  "category": "string (Xero chart of accounts category)",
  "client_vendor": {
    "id": "string (Xero contact ID)",
    "name": "string",
    "type": "enum (client | vendor)"
  },
  "description": "string",
  "status": "enum (draft | submitted | authorised | paid | voided)",
  "reconciliation_status": "enum (unreconciled | reconciled)",
  "invoice_number": "string (optional, for invoices)",
  "reference": "string (optional, payment reference)",
  "line_items": [
    {
      "description": "string",
      "quantity": "number",
      "unit_amount": "number",
      "account_code": "string",
      "tax_type": "string"
    }
  ],
  "synced_at": "string (ISO 8601 timestamp)",
  "last_modified": "string (ISO 8601 timestamp from Xero)"
}
```

**Validation Rules**:
- `amount` must be > 0
- `date` must be valid ISO 8601 date
- `type` determines required fields (e.g., invoices require `invoice_number`)
- `currency` must be valid ISO 4217 code
- Duplicate detection: same `transaction_id` cannot be imported twice

**Relationships**:
- Links to CEO Briefing (aggregated for revenue/expense analysis)
- Links to Subscription Analysis (recurring transactions identified by pattern matching)

---

### 3. CEO Briefing

**Purpose**: Represents a weekly business intelligence report with revenue analysis, task completion, bottlenecks, and proactive suggestions.

**Storage Location**: `AI_Employee_Vault/Briefings/{YYYY-MM-DD}_Monday_Briefing.md`

**Schema** (Markdown with YAML frontmatter):
```yaml
---
generated: "2026-01-13T07:00:00Z"
period_start: "2026-01-06"
period_end: "2026-01-12"
briefing_type: "weekly"
status: "generated"
---

# Monday Morning CEO Briefing

## Executive Summary
[1-2 sentence overview of week]

## Revenue Summary
- **Weekly Revenue**: $X,XXX
- **Month-to-Date**: $X,XXX (XX% of $XX,XXX goal)
- **Trend**: [on_track | behind | ahead]
- **Top Clients**: [List with revenue amounts]

## Completed Tasks
- [Task 1] - Completed [date] (Duration: X days)
- [Task 2] - Completed [date] (Duration: X days)

## Bottlenecks Identified
| Task | Expected Duration | Actual Duration | Delay |
|------|-------------------|-----------------|-------|
| [Task] | X days | Y days | +Z days |

## Cost Optimization Opportunities
### Unused Subscriptions
- **[Service Name]**: $XX/month - No activity in XX days
  - **Recommendation**: Cancel subscription
  - **Estimated Savings**: $XXX/year

## Upcoming Deadlines
- [Deadline 1]: X days remaining [Status: on_track | at_risk]
- [Deadline 2]: X days remaining [Status: on_track | at_risk]

## Social Media Summary
| Platform | Posts This Week | Target | Consistency |
|----------|----------------|--------|-------------|
| LinkedIn | X | Y | XX% |
| Facebook | X | Y | XX% |
| Instagram | X | Y | XX% |
| Twitter | X | Y | XX% |

## Proactive Suggestions
1. [Suggestion based on data analysis]
2. [Suggestion based on trends]
3. [Suggestion based on upcoming deadlines]

---
*Generated by AI Employee v1.0 (Gold Tier)*
```

**Validation Rules**:
- `generated` timestamp must be Monday 7 AM (configurable)
- `period_start` and `period_end` must span exactly 7 days
- Revenue calculations must match sum of transactions in period
- Task durations calculated from Done/ folder timestamps
- Subscription analysis based on transaction patterns

**Data Sources**:
- Financial data: `AI_Employee_Vault/Accounting/transactions/`
- Task data: `AI_Employee_Vault/Done/`
- Goals: `AI_Employee_Vault/Business_Goals.md`
- Social media: Audit logs from social media MCP servers

---

### 4. Audit Log Entry

**Purpose**: Represents a single logged action with complete context for accountability and debugging.

**Storage Location**: `AI_Employee_Vault/Logs/{YYYY-MM-DD}.json`

**Schema**:
```json
{
  "entries": [
    {
      "id": "string (UUID)",
      "timestamp": "string (ISO 8601 with timezone)",
      "action_type": "enum (email_send | social_post | api_call | file_operation | approval_granted | approval_rejected | error | system_event)",
      "actor": "enum (claude_code | human | watcher | orchestrator | mcp_server)",
      "target": "string (recipient, platform, file path, etc.)",
      "parameters": {
        "key": "value (sanitized - no secrets)"
      },
      "approval_status": "enum (not_required | pending | approved | rejected)",
      "approver": "string (optional, human identifier)",
      "approval_timestamp": "string (optional, ISO 8601)",
      "result": "enum (success | failure | partial)",
      "error_details": {
        "error_type": "string",
        "error_message": "string",
        "stack_trace": "string (optional)",
        "retry_attempts": "integer",
        "recovered": "boolean"
      },
      "execution_duration_ms": "integer",
      "metadata": {
        "process": "string (orchestrator, watcher name, etc.)",
        "iteration": "integer (optional, for Ralph loop)",
        "task_id": "string (optional, links to Task Execution State)"
      }
    }
  ],
  "date": "string (YYYY-MM-DD)",
  "entry_count": "integer",
  "consolidated_at": "string (ISO 8601 timestamp)"
}
```

**Validation Rules**:
- `timestamp` must be valid ISO 8601 with timezone
- `parameters` must be sanitized (no passwords, tokens, API keys)
- `approval_status` = "approved" requires `approver` and `approval_timestamp`
- `result` = "failure" requires `error_details`
- Daily consolidation at midnight (FR-044)

**Retention Policy**:
- Minimum 90 days in `Logs/` folder (FR-045)
- After 90 days, move to `Logs/Archive/` and compress (FR-046)
- Validate JSON integrity on consolidation (FR-047)

---

### 5. Social Media Post

**Purpose**: Represents a scheduled or published social media update across multiple platforms.

**Storage Location**:
- Pending: `AI_Employee_Vault/Pending_Approval/SOCIAL_POST_{platform}_{timestamp}.md`
- Published: Audit log entry + metadata in `AI_Employee_Vault/Social_Media/posts.json`

**Schema**:
```json
{
  "post_id": "string (UUID)",
  "platform": "enum (linkedin | facebook | instagram | twitter)",
  "content": "string (post text)",
  "media_attachments": [
    {
      "type": "enum (image | video | link)",
      "url": "string",
      "alt_text": "string (optional)"
    }
  ],
  "hashtags": ["array of strings"],
  "scheduled_time": "string (ISO 8601 timestamp)",
  "status": "enum (draft | pending_approval | approved | published | failed)",
  "approval_request_file": "string (path to approval request)",
  "approved_by": "string (optional, human identifier)",
  "approved_at": "string (optional, ISO 8601 timestamp)",
  "published_at": "string (optional, ISO 8601 timestamp)",
  "post_url": "string (optional, URL of published post)",
  "engagement_metrics": {
    "likes": "integer (optional)",
    "comments": "integer (optional)",
    "shares": "integer (optional)",
    "impressions": "integer (optional)",
    "last_updated": "string (ISO 8601 timestamp)"
  },
  "platform_specific": {
    "twitter": {
      "character_count": "integer",
      "truncated": "boolean"
    },
    "instagram": {
      "container_id": "string (media container ID)",
      "image_url": "string (publicly accessible URL)"
    }
  }
}
```

**Validation Rules**:
- `content` length must respect platform limits (Twitter: 280 chars)
- `platform` = "instagram" requires at least one image in `media_attachments`
- `status` = "published" requires `post_url` and `published_at`
- `status` = "approved" requires `approved_by` and `approved_at`

**State Transitions**:
```
draft → pending_approval (when scheduled time approaches)
pending_approval → approved (when human approves)
pending_approval → rejected (when human rejects)
approved → published (when MCP server posts successfully)
approved → failed (when posting fails)
```

---

### 6. Error Recovery Record

**Purpose**: Represents an error event and recovery attempt with full context for debugging and reliability analysis.

**Storage Location**: `AI_Employee_Vault/Logs/errors/{YYYY-MM-DD}_errors.json`

**Schema**:
```json
{
  "error_id": "string (UUID)",
  "timestamp": "string (ISO 8601 timestamp)",
  "error_type": "enum (transient | authentication | logic | data | system)",
  "error_category": "enum (network_timeout | rate_limit | token_expired | corrupted_file | process_crash | api_error)",
  "original_operation": {
    "action_type": "string",
    "target": "string",
    "parameters": "object (sanitized)"
  },
  "error_message": "string",
  "stack_trace": "string (optional)",
  "retry_attempts": [
    {
      "attempt_number": "integer",
      "timestamp": "string (ISO 8601)",
      "delay_seconds": "integer",
      "result": "enum (success | failure)"
    }
  ],
  "recovery_actions_taken": ["array of strings"],
  "final_outcome": "enum (recovered | escalated_to_human | failed_permanently)",
  "escalation_details": {
    "escalated_at": "string (ISO 8601 timestamp)",
    "escalation_file": "string (path to human review request)",
    "resolution": "string (optional, how human resolved)"
  },
  "impact": {
    "component_affected": "string (orchestrator, watcher, mcp_server)",
    "degraded_functionality": ["array of strings"],
    "recovery_time_seconds": "integer"
  }
}
```

**Validation Rules**:
- `error_type` = "transient" should have `retry_attempts` with exponential backoff
- `retry_attempts` must not exceed 3 (FR-026)
- `final_outcome` = "escalated_to_human" requires `escalation_details`
- Delay between retries must follow exponential backoff (1s, 2s, 4s)

**Relationships**:
- Links to Audit Log Entry (same `error_id`)
- Links to Task Execution State (if error occurred during Ralph loop)
- Aggregated in CEO Briefing (system reliability metrics)

---

### 7. Subscription Analysis

**Purpose**: Represents a recurring subscription identified in financial data with usage tracking and cancellation recommendations.

**Storage Location**: `AI_Employee_Vault/Accounting/subscriptions.json`

**Schema**:
```json
{
  "subscription_id": "string (UUID)",
  "service_name": "string (identified from transaction description)",
  "merchant_name": "string (from transaction)",
  "cost": "number (monthly cost)",
  "frequency": "enum (monthly | quarterly | annual)",
  "first_detected": "string (ISO 8601 date)",
  "last_transaction_date": "string (ISO 8601 date)",
  "transaction_ids": ["array of Xero transaction IDs"],
  "usage_tracking": {
    "last_login_date": "string (optional, ISO 8601 date)",
    "activity_count_30d": "integer (optional)",
    "usage_source": "enum (manual | api | inferred)"
  },
  "cancellation_recommendation": {
    "recommended": "boolean",
    "reason": "string (e.g., 'No activity in 45 days')",
    "estimated_annual_savings": "number",
    "confidence": "enum (high | medium | low)"
  },
  "status": "enum (active | flagged_for_review | cancelled)",
  "notes": "string (optional, human notes)"
}
```

**Validation Rules**:
- `cost` must be > 0
- `frequency` determines expected transaction interval
- `cancellation_recommendation.recommended` = true requires `reason` and `estimated_annual_savings`
- Pattern matching on `merchant_name` to identify subscription services

**Pattern Matching Rules**:
```python
SUBSCRIPTION_PATTERNS = {
    'netflix.com': 'Netflix',
    'spotify.com': 'Spotify',
    'adobe.com': 'Adobe Creative Cloud',
    'notion.so': 'Notion',
    'slack.com': 'Slack',
    'github.com': 'GitHub',
    'xero.com': 'Xero'
}
```

**Relationships**:
- Links to Financial Transactions (via `transaction_ids`)
- Included in CEO Briefing (cost optimization section)

---

## Entity Relationships

```
Task Execution State
  ├─→ Audit Log Entries (via task_id)
  ├─→ Error Recovery Records (via task_id)
  └─→ Social Media Posts (if task involves posting)

Financial Transaction
  ├─→ CEO Briefing (aggregated for revenue analysis)
  └─→ Subscription Analysis (recurring transactions)

CEO Briefing
  ├─→ Financial Transactions (data source)
  ├─→ Task Execution States (completed tasks)
  ├─→ Subscription Analysis (cost optimization)
  └─→ Social Media Posts (social media summary)

Audit Log Entry
  ├─→ Task Execution State (via task_id)
  ├─→ Error Recovery Record (via error_id)
  └─→ Social Media Post (via post_id)

Social Media Post
  ├─→ Audit Log Entry (publication logged)
  └─→ CEO Briefing (aggregated for social media summary)

Error Recovery Record
  ├─→ Audit Log Entry (same error_id)
  └─→ Task Execution State (if error during Ralph loop)

Subscription Analysis
  ├─→ Financial Transactions (via transaction_ids)
  └─→ CEO Briefing (cost optimization section)
```

---

## File Organization

```
AI_Employee_Vault/
├── Accounting/
│   ├── transactions/
│   │   ├── 2026-01/
│   │   │   └── transactions.json (Financial Transactions)
│   │   └── 2026-02/
│   │       └── transactions.json
│   ├── summaries/
│   │   └── 2026-01_summary.md
│   └── subscriptions.json (Subscription Analysis)
├── Briefings/
│   ├── 2026-01-13_Monday_Briefing.md (CEO Briefing)
│   └── 2026-01-20_Monday_Briefing.md
├── Logs/
│   ├── 2026-01-19.json (Audit Log Entries)
│   ├── errors/
│   │   └── 2026-01-19_errors.json (Error Recovery Records)
│   └── Archive/
│       └── 2025-10-19.json.gz (compressed logs > 90 days)
├── Social_Media/
│   └── posts.json (Social Media Posts)
└── .claude/
    └── state/
        └── ralph-state-{task_id}.json (Task Execution State)
```

---

## Data Migration & Compatibility

**Bronze/Silver Tier Compatibility**:
- All existing entities (Action Files, Plan Files, Approval Requests) remain unchanged
- Gold Tier adds new entities without breaking existing workflows
- Audit logging enhanced but maintains backward compatibility

**Version Control**:
- All JSON files include schema version field for future migrations
- Markdown files use YAML frontmatter for metadata versioning

**Backup Strategy**:
- Daily backup of entire `AI_Employee_Vault/` folder
- Audit logs backed up before consolidation
- State files backed up before Ralph loop execution

---

## Performance Considerations

**File Size Limits**:
- Individual JSON files should not exceed 10 MB
- Monthly transaction files split if > 5000 transactions
- Audit logs consolidated daily to prevent unbounded growth

**Query Optimization**:
- CEO Briefing generation reads only last 7 days of data
- Subscription analysis caches results, updates weekly
- Error recovery records indexed by date for fast retrieval

**Concurrency**:
- File-based storage uses file locking for concurrent access
- Atomic writes with temp file + rename pattern
- Retry logic for file lock contention

---

## Conclusion

This data model provides a complete schema for all Gold Tier entities while maintaining the local-first, file-based architecture. All entities include validation rules, state transitions, and relationships to support autonomous operation with full audit trails.

**Next Steps**: Proceed to contracts/interfaces.md to define Agent Skills and MCP server interfaces.
