# Audit Logger Reference

## Log Entry Schema

```json
{
  "timestamp": "2026-01-19T10:30:00.000Z",
  "action_type": "email_send",
  "actor": "email_ops_skill",
  "target": "client@example.com",
  "parameters": {
    "subject": "Invoice #123",
    "attachment": "invoice.pdf"
  },
  "approval_status": "approved",
  "approved_by": "human",
  "approval_timestamp": "2026-01-19T10:25:00.000Z",
  "result": "success",
  "duration_ms": 1250,
  "error": null
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | ISO 8601 | Yes | When action occurred |
| action_type | string | Yes | Category of action |
| actor | string | Yes | Who/what performed action |
| target | string | Yes | What was affected |
| parameters | object | No | Action details (sanitized) |
| approval_status | string | No | approved/rejected/not_required |
| approved_by | string | No | Who approved (if applicable) |
| result | string | Yes | success/failure/error |
| duration_ms | number | No | Execution time |
| error | string | No | Error message if failed |

## Action Types

| Type | Description |
|------|-------------|
| email_send | Email sent via MCP |
| email_draft | Email drafted |
| social_post | Social media post |
| odoo_sync | Odoo data sync |
| odoo_invoice | Invoice created |"
| approval_request | HITL request created |
| approval_granted | HITL approval given |
| file_move | File operation |
| ralph_iteration | Ralph loop iteration |
| error_recovery | Error handled |

## Retention Policy

| Age | Status | Action |
|-----|--------|--------|
| 0-90 days | Active | In Logs/ |
| 90-365 days | Archived | Compressed in Archive/ |
| >365 days | Configurable | Delete or long-term storage |

## Compliance Metrics

### HITL Compliance
Percentage of sensitive actions that went through human approval.

Target: ≥95%

Calculation:
```
HITL Compliance = (Approved Actions / Actions Requiring Approval) × 100
```

### Error Rate
Percentage of actions that failed.

Target: ≤5%

Calculation:
```
Error Rate = (Failed Actions / Total Actions) × 100
```

### Recovery Rate
Percentage of errors that were automatically recovered.

Target: ≥80%

Calculation:
```
Recovery Rate = (Recovered Errors / Total Errors) × 100
```

## Sensitive Data Handling

### Fields Automatically Sanitized
- password
- token
- secret
- api_key
- credential
- auth

### Long Values
Strings >500 characters are truncated with `...[TRUNCATED]`

## Query Examples

### Find all failures today
```bash
python3 audit-logger/scripts/main_operation.py --action query --since 24h --result fail
```

### Find actions by specific skill
```bash
python3 audit-logger/scripts/main_operation.py --action query --actor email_ops_skill --since 7d
```

### Generate weekly compliance report
```bash
python3 audit-logger/scripts/main_operation.py --action compliance-report --period weekly
```

## Scheduling

### Daily Consolidation (midnight)
```cron
0 0 * * * python3 .claude/skills/audit-logger/scripts/main_operation.py --action consolidate
```

### Weekly Archive (Sunday 3 AM)
```cron
0 3 * * 0 python3 .claude/skills/audit-logger/scripts/main_operation.py --action archive --older-than 90
```

## Troubleshooting

### Log file growing too large
Run archive more frequently or reduce retention period.

### Missing log entries
Check if skill is calling audit_log() function.

### Invalid JSON in log file
Use validate action to identify issues, then manually fix or quarantine.
