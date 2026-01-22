---
name: audit-logger
description: "WHAT: Comprehensive audit logging for all actions with compliance tracking, log retention, and analysis. WHEN: User says 'check audit log', 'compliance report', 'action history'. Trigger on: compliance review, debugging, action tracking, security audit."
---

# Comprehensive Audit Logger

## When to Use
- Reviewing action history for compliance
- Debugging failed operations
- Tracking approval workflows
- Generating compliance reports
- Analyzing system behavior patterns
- Security audits and investigations

## Log Entry Structure
```json
{
  "timestamp": "2026-01-19T10:30:00Z",
  "action_type": "email_send",
  "actor": "email_ops_skill",
  "target": "client@example.com",
  "parameters": {"subject": "Invoice #123"},
  "approval_status": "approved",
  "approved_by": "human",
  "approval_timestamp": "2026-01-19T10:25:00Z",
  "result": "success",
  "duration_ms": 1250,
  "error": null
}
```

## Instructions

1. **Log an Action**:
   ```bash
   python3 .claude/skills/audit-logger/scripts/main_operation.py --action log \
     --type "email_send" \
     --actor "email_ops" \
     --target "client@example.com" \
     --result "success" \
     --params '{"subject": "Invoice"}'
   ```

2. **Query Logs**:
   ```bash
   python3 .claude/skills/audit-logger/scripts/main_operation.py --action query \
     --since "24h" \
     --type "email_send" \
     --result "failure"
   ```
   *Filters: `--since`, `--until`, `--type`, `--actor`, `--result`*

3. **Generate Daily Summary**:
   ```bash
   python3 .claude/skills/audit-logger/scripts/main_operation.py --action daily-summary \
     --date 2026-01-19
   ```

4. **Compliance Report**:
   ```bash
   python3 .claude/skills/audit-logger/scripts/main_operation.py --action compliance-report \
     --period monthly
   ```
   *Includes: approval rates, error rates, HITL compliance.*

5. **Consolidate Daily Logs**:
   ```bash
   python3 .claude/skills/audit-logger/scripts/main_operation.py --action consolidate
   ```
   *Runs at midnight, creates `YYYY-MM-DD.json`.*

6. **Archive Old Logs**:
   ```bash
   python3 .claude/skills/audit-logger/scripts/main_operation.py --action archive \
     --older-than 90d
   ```
   *Compresses and moves to `Logs/Archive/`.*

7. **Validate Log Integrity**:
   ```bash
   python3 .claude/skills/audit-logger/scripts/main_operation.py --action validate \
     --file "Logs/2026-01-19.json"
   ```

## Log Files
- `AI_Employee_Vault/Logs/YYYY-MM-DD.json` - Daily consolidated logs
- `AI_Employee_Vault/Logs/Archive/` - Compressed old logs (>90 days)
- `AI_Employee_Vault/Logs/audit_summary.md` - Rolling summary

## Retention Policy
| Age | Action |
|-----|--------|
| 0-90 days | Active (Logs/) |
| 90-365 days | Archived (compressed) |
| >365 days | Configurable (delete/keep) |

## Compliance Tracking
- **HITL Compliance**: % of sensitive actions with approval
- **Error Rate**: % of failed operations
- **Recovery Rate**: % of errors auto-recovered
- **Response Time**: Average approval turnaround

## Scheduled Tasks
```cron
# Daily log consolidation at midnight
0 0 * * * python3 .claude/skills/audit-logger/scripts/main_operation.py --action consolidate

# Weekly archive check
0 3 * * 0 python3 .claude/skills/audit-logger/scripts/main_operation.py --action archive --older-than 90d
```

## Validation
- [ ] All actions logged with required fields
- [ ] Secrets sanitized from parameters
- [ ] Daily consolidation runs
- [ ] Archive compresses correctly
- [ ] Integrity validation passes

See [REFERENCE.md](./REFERENCE.md) for log analysis queries.
