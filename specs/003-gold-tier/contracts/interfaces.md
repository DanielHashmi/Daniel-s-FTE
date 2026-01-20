# Contracts & Interfaces: Gold Tier Autonomous Employee

**Feature**: Gold Tier Autonomous Employee
**Date**: 2026-01-19
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the interfaces for Agent Skills and MCP servers in the Gold Tier implementation. All interfaces follow the Claude Agent Skills framework and MCP specification for consistency and maintainability.

---

## Agent Skills Interfaces

### 1. Accounting Sync Skill (`/odoo-accounting`)

**Purpose**: Sync financial transactions from Odoo accounting system to local vault.

**Skill Definition** (`.claude/skills/odoo-accounting/skill.json`):
```json
{
  "name": "odoo-accounting",
  "description": "Sync financial transactions from Odoo accounting system",
  "version": "1.0.0",
  "parameters": {
    "period": {
      "type": "string",
      "description": "Time period to sync (e.g., 'last_30_days', 'current_month', 'YYYY-MM')",
      "default": "last_30_days"
    },
    "force_full_sync": {
      "type": "boolean",
      "description": "Force full sync instead of incremental",
      "default": false
    },
    "dry_run": {
      "type": "boolean",
      "description": "Simulate sync without writing data",
      "default": false
    }
  },
  "returns": {
    "transactions_synced": "integer",
    "duplicates_skipped": "integer",
    "errors": "array",
    "sync_duration_ms": "integer"
  }
}
```

**Usage**:
```bash
/odoo-accounting period=current_month
/odoo-accounting period=2026-01 force_full_sync=true
/odoo-accounting dry_run=true
```

**Implementation Contract**:
- MUST authenticate with Odoo using API Key
- MUST detect and skip duplicate transactions
- MUST store transactions in `AI_Employee_Vault/Accounting/transactions/{YYYY-MM}/`
- MUST log all API calls in audit log
- MUST handle rate limits with exponential backoff
- MUST refresh expired tokens automatically

---

### 2. CEO Briefing Generation Skill (`/briefing-gen`)

**Purpose**: Generate weekly CEO Briefing with business intelligence and proactive suggestions.

**Skill Definition** (`.claude/skills/briefing-gen/skill.json`):
```json
{
  "name": "briefing-gen",
  "description": "Generate weekly CEO Briefing with business intelligence",
  "version": "1.0.0",
  "parameters": {
    "period_start": {
      "type": "string",
      "description": "Start date (ISO 8601 format, default: last Monday)",
      "default": "auto"
    },
    "period_end": {
      "type": "string",
      "description": "End date (ISO 8601 format, default: last Sunday)",
      "default": "auto"
    },
    "include_social_summary": {
      "type": "boolean",
      "description": "Include social media summary section",
      "default": true
    },
    "dry_run": {
      "type": "boolean",
      "description": "Generate briefing without saving",
      "default": false
    }
  },
  "returns": {
    "briefing_file": "string (path to generated briefing)",
    "revenue_total": "number",
    "tasks_completed": "integer",
    "bottlenecks_identified": "integer",
    "cost_savings_identified": "number",
    "generation_duration_ms": "integer"
  }
}
```

**Usage**:
```bash
/briefing-gen
/briefing-gen period_start=2026-01-06 period_end=2026-01-12
/briefing-gen dry_run=true
```

**Implementation Contract**:
- MUST analyze financial data from `AI_Employee_Vault/Accounting/`
- MUST analyze completed tasks from `AI_Employee_Vault/Done/`
- MUST read goals from `AI_Employee_Vault/Business_Goals.md`
- MUST identify subscription patterns for cost optimization
- MUST calculate task durations and identify bottlenecks
- MUST generate briefing in < 5 minutes (performance goal)
- MUST store briefing in `AI_Employee_Vault/Briefings/{YYYY-MM-DD}_Monday_Briefing.md`

---

### 3. Social Media Operations Skill (`/social-ops`)

**Purpose**: Post business updates to multiple social media platforms (enhanced from Silver Tier).

**Skill Definition** (`.claude/skills/social-ops/skill.json`):
```json
{
  "name": "social-ops",
  "description": "Post business updates to social media platforms",
  "version": "2.0.0",
  "parameters": {
    "action": {
      "type": "string",
      "description": "Action to perform",
      "enum": ["post", "schedule", "status", "list_pending"],
      "required": true
    },
    "platforms": {
      "type": "array",
      "description": "Target platforms",
      "items": {
        "enum": ["linkedin", "facebook", "instagram", "twitter"]
      },
      "default": ["linkedin"]
    },
    "content": {
      "type": "string",
      "description": "Post content (required for post/schedule actions)"
    },
    "media": {
      "type": "array",
      "description": "Media attachments (URLs or file paths)",
      "items": {
        "type": "string"
      }
    },
    "hashtags": {
      "type": "array",
      "description": "Hashtags to include",
      "items": {
        "type": "string"
      }
    },
    "scheduled_time": {
      "type": "string",
      "description": "ISO 8601 timestamp for scheduled posts"
    },
    "dry_run": {
      "type": "boolean",
      "description": "Simulate posting without creating approval requests",
      "default": false
    }
  },
  "returns": {
    "action_performed": "string",
    "platforms_targeted": "array",
    "approval_requests_created": "array",
    "posts_published": "array",
    "errors": "array"
  }
}
```

**Usage**:
```bash
/social-ops action=post platforms=["linkedin","twitter"] content="New blog post published!"
/social-ops action=schedule platforms=["facebook","instagram"] content="Product launch!" scheduled_time="2026-01-20T09:00:00Z"
/social-ops action=status
/social-ops action=list_pending
```

**Implementation Contract**:
- MUST create approval requests in `AI_Employee_Vault/Pending_Approval/` for all posts
- MUST respect platform-specific character limits (Twitter: 280 chars)
- MUST handle platform-specific requirements (Instagram: requires image)
- MUST truncate content intelligently if exceeding limits
- MUST log all posting attempts in audit log
- MUST capture post URLs after publication
- MUST handle rate limits independently per platform

---

### 4. Error Recovery Skill (`/error-recovery`)

**Purpose**: Analyze and recover from system errors with graceful degradation.

**Skill Definition** (`.claude/skills/error-recovery/skill.json`):
```json
{
  "name": "error-recovery",
  "description": "Analyze and recover from system errors",
  "version": "1.0.0",
  "parameters": {
    "action": {
      "type": "string",
      "description": "Recovery action to perform",
      "enum": ["analyze", "retry", "escalate", "status"],
      "required": true
    },
    "error_id": {
      "type": "string",
      "description": "Error ID to recover from (required for retry/escalate)"
    },
    "component": {
      "type": "string",
      "description": "Component to analyze (for status action)",
      "enum": ["orchestrator", "watchers", "mcp_servers", "all"]
    }
  },
  "returns": {
    "action_performed": "string",
    "recovery_successful": "boolean",
    "errors_analyzed": "integer",
    "recovery_actions_taken": "array",
    "escalations_created": "integer"
  }
}
```

**Usage**:
```bash
/error-recovery action=analyze
/error-recovery action=retry error_id="abc-123"
/error-recovery action=escalate error_id="def-456"
/error-recovery action=status component=all
```

**Implementation Contract**:
- MUST implement exponential backoff for transient errors (1s, 2s, 4s)
- MUST attempt up to 3 retries before escalation
- MUST refresh expired authentication tokens automatically
- MUST quarantine corrupted files in `AI_Employee_Vault/Quarantine/`
- MUST create human review requests for unrecoverable errors
- MUST log all recovery attempts in error recovery records
- MUST update Dashboard.md with degraded state information

---

### 5. Audit Management Skill (`/audit-mgmt`)

**Purpose**: Manage audit logs with consolidation, retention, and integrity validation.

**Skill Definition** (`.claude/skills/audit-mgmt/skill.json`):
```json
{
  "name": "audit-mgmt",
  "description": "Manage audit logs with consolidation and retention",
  "version": "1.0.0",
  "parameters": {
    "action": {
      "type": "string",
      "description": "Management action to perform",
      "enum": ["consolidate", "archive", "validate", "query", "stats"],
      "required": true
    },
    "date": {
      "type": "string",
      "description": "Date for consolidate/archive actions (YYYY-MM-DD)"
    },
    "query": {
      "type": "object",
      "description": "Query parameters for query action",
      "properties": {
        "action_type": "string",
        "actor": "string",
        "date_range": "object"
      }
    }
  },
  "returns": {
    "action_performed": "string",
    "entries_processed": "integer",
    "files_archived": "integer",
    "validation_errors": "array",
    "query_results": "array"
  }
}
```

**Usage**:
```bash
/audit-mgmt action=consolidate date=2026-01-19
/audit-mgmt action=archive
/audit-mgmt action=validate
/audit-mgmt action=query query='{"action_type":"email_send","date_range":{"start":"2026-01-01","end":"2026-01-31"}}'
/audit-mgmt action=stats
```

**Implementation Contract**:
- MUST consolidate daily logs at midnight
- MUST validate JSON integrity on consolidation
- MUST archive logs older than 90 days
- MUST compress archived logs (gzip)
- MUST sanitize all log entries (no secrets)
- MUST maintain 90-day retention minimum
- MUST create backup before consolidation

---

## MCP Server Interfaces

### 1. Odoo MCP Server

**Server Name**: `odoo-mcp`

**Purpose**: Provides tool-use access to Odoo 19 accounting data for the AI Employee.

**Configuration**:
```json
{
  "odoo": {
    "command": "python3",
    "args": ["src/mcp/odoo_server.py"],
    "env": {
      "ODOO_URL": "...",
      "ODOO_DB": "...",
      "ODOO_USER": "...",
      "ODOO_PASSWORD": "..."
    }
  }
}
```

**Resources**:

- `odoo://transactions`
  - **Name**: Odoo Transactions
  - **Description**: Access Odoo accounting transactions (invoices, payments, expenses)
  - **MIME Type**: `application/json`

- `odoo://invoices`
  - **Name**: Odoo Invoices
  - **Description**: Access Odoo invoices
  - **MIME Type**: `application/json`

**Tools**:

- `sync_transactions`
  - **Description**: Sync transactions from Odoo
  - **Input Schema**:
    ```json
    {
      "type": "object",
      "properties": {
        "days": {
          "type": "integer",
          "description": "Number of days to sync (default: 30)"
        }
      }
    }
    ```

- `get_financial_summary`
  - **Description**: Get financial summary for a period
  - **Input Schema**:
    ```json
    {
      "type": "object",
      "properties": {
        "period": {
          "type": "string",
          "enum": ["daily", "weekly", "monthly"]
        }
      },
      "required": ["period"]
    }
    ```

**Rate Limits**: Dependent on Odoo server configuration (typically high for self-hosted).

---

### 2. Facebook MCP Server

**Server Name**: `facebook-mcp`

**Capabilities**:
```json
{
  "name": "facebook-mcp",
  "version": "1.0.0",
  "capabilities": {
    "tools": [
      {
        "name": "create_post",
        "description": "Create a Facebook post",
        "inputSchema": {
          "type": "object",
          "properties": {
            "message": {"type": "string"},
            "link": {"type": "string"},
            "published": {"type": "boolean"}
          },
          "required": ["message"]
        }
      },
      {
        "name": "get_post_status",
        "description": "Get status of a published post",
        "inputSchema": {
          "type": "object",
          "properties": {
            "post_id": {"type": "string"}
          },
          "required": ["post_id"]
        }
      }
    ]
  }
}
```

**Authentication**: OAuth 2.0 with long-lived access tokens

**Rate Limits**: Platform-specific, implement detection and backoff

---

### 3. Instagram MCP Server

**Server Name**: `instagram-mcp`

**Capabilities**:
```json
{
  "name": "instagram-mcp",
  "version": "1.0.0",
  "capabilities": {
    "tools": [
      {
        "name": "create_media_container",
        "description": "Create Instagram media container",
        "inputSchema": {
          "type": "object",
          "properties": {
            "image_url": {"type": "string"},
            "caption": {"type": "string"},
            "hashtags": {"type": "array"}
          },
          "required": ["image_url"]
        }
      },
      {
        "name": "publish_container",
        "description": "Publish Instagram media container",
        "inputSchema": {
          "type": "object",
          "properties": {
            "creation_id": {"type": "string"}
          },
          "required": ["creation_id"]
        }
      }
    ]
  }
}
```

**Authentication**: Facebook Graph API OAuth 2.0

**Requirements**: Business/Creator account, publicly accessible image URLs

---

### 4. Twitter MCP Server

**Server Name**: `twitter-mcp`

**Capabilities**:
```json
{
  "name": "twitter-mcp",
  "version": "1.0.0",
  "capabilities": {
    "tools": [
      {
        "name": "create_tweet",
        "description": "Create a tweet",
        "inputSchema": {
          "type": "object",
          "properties": {
            "text": {"type": "string"},
            "media_ids": {"type": "array"}
          },
          "required": ["text"]
        }
      },
      {
        "name": "get_tweet_metrics",
        "description": "Get engagement metrics for a tweet",
        "inputSchema": {
          "type": "object",
          "properties": {
            "tweet_id": {"type": "string"}
          },
          "required": ["tweet_id"]
        }
      }
    ]
  }
}
```

**Authentication**: OAuth 2.0 Bearer Token

**Rate Limits**:
- Free: 17 tweets/24 hours
- Basic: 100 tweets/24 hours
- Pro: 100 tweets/15 minutes

---

## Ralph Wiggum Stop Hook Interface

**Hook Type**: Stop Hook (intercepts Claude Code exit)

**Configuration** (`.claude/plugins/ralph-wiggum/config.json`):
```json
{
  "max_iterations": 10,
  "completion_strategy": "file_movement",
  "completion_promise": "TASK_COMPLETE",
  "timeout_per_iteration_seconds": 30,
  "state_file_path": ".claude/state/ralph-state.json",
  "watch_folders": {
    "needs_action": "AI_Employee_Vault/Needs_Action",
    "done": "AI_Employee_Vault/Done"
  },
  "logging": {
    "enabled": true,
    "log_file": "AI_Employee_Vault/Logs/ralph-loop.log"
  }
}
```

**Stop Hook Script Interface** (`stop-hook.sh`):
```bash
#!/bin/bash
# Input: None (reads from state file)
# Output: Exit code 0 (allow exit) or 1 (block exit and continue)
# Side Effects: Updates state file, creates human review requests

# Expected behavior:
# 1. Read state file
# 2. Check completion criteria (file movement OR promise)
# 3. Check iteration count < max_iterations
# 4. If complete: exit 0
# 5. If incomplete and under limit: increment iteration, exit 1
# 6. If max iterations reached: create human review request, exit 0
```

**State File Interface** (`.claude/state/ralph-state-{task_id}.json`):
```json
{
  "task_id": "string",
  "task_file": "string (path)",
  "prompt": "string",
  "iteration": "integer",
  "max_iterations": "integer",
  "completion_strategy": "enum",
  "status": "enum",
  "started_at": "string (ISO 8601)",
  "last_iteration_at": "string (ISO 8601)"
}
```

---

## Shared Interfaces

### Audit Logging Interface

All components MUST implement audit logging:

```python
def log_action(
    action_type: str,
    actor: str,
    target: str,
    parameters: dict,
    approval_status: str,
    result: str,
    error_details: dict = None,
    execution_duration_ms: int = 0,
    metadata: dict = None
) -> str:
    """
    Log an action to the audit log.

    Returns: log_entry_id (UUID)
    """
    pass
```

### Error Recovery Interface

All components MUST implement error recovery:

```python
def handle_error(
    error: Exception,
    operation: dict,
    max_retries: int = 3
) -> tuple[bool, dict]:
    """
    Handle an error with retry logic.

    Returns: (recovered: bool, recovery_details: dict)
    """
    pass
```

### HITL Approval Interface

All sensitive actions MUST create approval requests:

```python
def create_approval_request(
    action_type: str,
    target: str,
    parameters: dict,
    expires_in_hours: int = 24
) -> str:
    """
    Create an approval request file.

    Returns: approval_file_path
    """
    pass
```

---

## Testing Contracts

### Unit Test Requirements

All Agent Skills MUST have unit tests covering:
- Parameter validation
- Error handling
- Dry-run mode
- Return value structure

### Integration Test Requirements

All MCP servers MUST have integration tests covering:
- Authentication flow
- API call success
- Rate limit handling
- Error recovery

### Contract Test Requirements

All interfaces MUST have contract tests verifying:
- Input schema validation
- Output schema validation
- Error response format
- Timeout behavior

---

## Versioning & Compatibility

**Semantic Versioning**: All skills and MCP servers use semantic versioning (MAJOR.MINOR.PATCH)

**Breaking Changes**: MAJOR version increment required for:
- Parameter removal or rename
- Return value structure change
- Authentication method change

**Backward Compatibility**: MINOR version increments MUST maintain backward compatibility

**Deprecation Policy**: Deprecated features MUST be supported for at least 2 MINOR versions

---

## Conclusion

This contracts document defines clear interfaces for all Gold Tier Agent Skills and MCP servers. All interfaces follow the Claude Agent Skills framework and MCP specification, ensuring consistency, testability, and maintainability.

**Next Steps**: Proceed to quickstart.md for setup and usage instructions.