# Cross-Domain Orchestrator Reference

## Domain Architecture

### Personal Domain
Components focused on individual productivity:
- **Gmail**: Email communication
- **WhatsApp**: Messaging (via Playwright automation)
- **Calendar**: Scheduling and reminders

### Business Domain
Components for business operations:
- **Xero**: Accounting and financial management
- **LinkedIn**: Professional networking and content
- **Facebook/Instagram/Twitter**: Social media marketing

## Workflow Definitions

### Creating Custom Workflows

Add to `AI_Employee_Vault/Config/workflows.yaml`:

```yaml
my-custom-workflow:
  description: "My custom business workflow"
  steps:
    - action: xero-accounting
      command: "--action sync"
      on_error: continue

    - action: email-ops
      command: "--action send"
      requires_approval: true

    - action: audit-log
      event: workflow_completed
```

### Workflow Step Options

| Option | Description |
|--------|-------------|
| `action` | Skill name to execute |
| `command` | Command arguments |
| `on_error` | `stop` (default) or `continue` |
| `requires_approval` | Pause for HITL approval |
| `timeout` | Max execution time (seconds) |
| `depends_on` | Previous step that must succeed |

## Scheduling

### Cron Configuration

```cron
# Daily sync at 6 AM
0 6 * * * python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action run-schedule --schedule daily

# Weekly audit every Monday at 7 AM
0 7 * * 1 python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action run-schedule --schedule weekly

# Monthly reports on 1st at 8 AM
0 8 1 * * python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action run-schedule --schedule monthly
```

## Configuration File

`AI_Employee_Vault/Config/orchestrator_config.yaml`:

```yaml
domains:
  personal:
    gmail:
      enabled: true
      check_interval: 120  # seconds
    whatsapp:
      enabled: true
      keywords: ["urgent", "invoice", "payment"]

  business:
    xero:
      enabled: true
      sync_schedule: "0 6 * * *"
    linkedin:
      enabled: true
    social:
      enabled: true
      platforms: ["facebook", "instagram", "twitter"]

schedules:
  daily_sync: "06:00"
  weekly_audit: "monday 07:00"
  social_posting: "09:00,15:00"

workflows:
  default_invoice_flow: client-invoice-flow
  default_audit: weekly-business-audit
```

## Error Handling

### Component Failures
When a component fails, the orchestrator:
1. Logs the error
2. Continues with other components
3. Queues failed operations for retry
4. Creates alert if critical

### Recovery Strategy
```python
RECOVERY_STRATEGY = {
    "gmail": "retry_with_backoff",
    "xero": "use_cached_data",
    "social": "queue_for_later",
    "critical": "alert_human"
}
```

## Troubleshooting

### "Component unconfigured"
Set required environment variables for the component.

### "Workflow step failed"
Check skill-specific logs in `AI_Employee_Vault/Logs/`.

### "Schedule not running"
Verify cron/Task Scheduler configuration.
