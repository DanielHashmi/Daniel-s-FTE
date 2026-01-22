---
name: error-recovery
description: "WHAT: Handle errors gracefully with retry logic, automatic recovery, and graceful degradation. WHEN: User says 'check errors', 'recover system', 'retry failed'. Trigger on: system failures, API errors, transient issues, watchdog alerts."
---

# Error Recovery & Graceful Degradation

## When to Use
- Handling transient errors (network timeouts, rate limits)
- Recovering from authentication failures
- Managing component outages gracefully
- Retrying failed operations
- Quarantining corrupted data
- Running watchdog health checks

## Error Categories

| Category | Examples | Recovery Strategy |
|----------|----------|-------------------|
| Transient | Network timeout, rate limit | Exponential backoff retry |
| Authentication | Expired token, revoked access | Token refresh or human alert |
| Logic | Misinterpreted data | Human review queue |
| Data | Corrupted file, missing field | Quarantine + alert |
| System | Process crash, disk full | Watchdog + auto-restart |

## Instructions

1. **Retry Failed Operation**:
   ```bash
   python3 .claude/skills/error-recovery/scripts/main_operation.py --action retry \
     --operation-id OP_12345 \
     --max-attempts 3 \
     --backoff exponential
   ```

2. **Refresh Authentication Token**:
   ```bash
   python3 .claude/skills/error-recovery/scripts/main_operation.py --action refresh-token \
     --service xero
   ```
   *Services: `gmail|xero|linkedin|facebook|instagram|twitter`*

3. **Quarantine Corrupted File**:
   ```bash
   python3 .claude/skills/error-recovery/scripts/main_operation.py --action quarantine \
     --file "Needs_Action/corrupted_file.md" \
     --reason "JSON parse error"
   ```

4. **Check Component Health**:
   ```bash
   python3 .claude/skills/error-recovery/scripts/main_operation.py --action health-check
   ```

5. **Process Recovery Queue**:
   ```bash
   python3 .claude/skills/error-recovery/scripts/main_operation.py --action process-queue
   ```
   *Retries queued operations that failed earlier.*

6. **Run Watchdog Check**:
   ```bash
   python3 .claude/skills/error-recovery/scripts/main_operation.py --action watchdog
   ```
   *Checks and restarts crashed processes.*

7. **View Error Log**:
   ```bash
   python3 .claude/skills/error-recovery/scripts/main_operation.py --action errors --since 24h
   ```

## Retry Configuration
```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1,      # seconds
    "max_delay": 60,      # seconds
    "backoff": "exponential",  # or "linear"
    "jitter": True        # Add randomness to prevent thundering herd
}
```

## Graceful Degradation Rules

| Component Down | System Behavior |
|----------------|-----------------|
| Gmail API | Queue emails, process other watchers |
| Odoo API | Skip financial sync, use cached data |
| Social APIs | Queue posts, continue other operations |
| Orchestrator | Watchdog restarts within 30s |

## Queue Locations
- `AI_Employee_Vault/Recovery_Queue/` - Failed operations awaiting retry
- `AI_Employee_Vault/Quarantine/` - Corrupted files with timestamps
- `AI_Employee_Vault/Alerts/` - Human review requests

## Watchdog Configuration
```yaml
# ecosystem.config.js (PM2)
watch_restart_delay: 5000
max_restarts: 10
min_uptime: 30000
```

## Validation
- [ ] Retry logic executes correctly
- [ ] Token refresh works
- [ ] Quarantine isolates bad data
- [ ] Watchdog restarts processes
- [ ] Error logs are comprehensive

See [REFERENCE.md](./REFERENCE.md) for error handling patterns.
