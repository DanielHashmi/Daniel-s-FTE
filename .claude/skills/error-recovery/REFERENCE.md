# Error Recovery Reference

## Error Categories

| Category | Examples | Strategy |
|----------|----------|----------|
| Transient | Network timeout, rate limit | Exponential backoff retry |
| Authentication | Expired token, 401 error | Token refresh or human alert |
| Logic | Misinterpreted data | Human review queue |
| Data | Corrupted file, missing field | Quarantine + alert |
| System | Process crash, disk full | Watchdog + auto-restart |

## Retry Configuration

### Exponential Backoff
```python
# Delay calculation
delay = base_delay * (2 ** attempt)
delay = min(delay, max_delay)

# Example: base=1s, max=60s
# Attempt 0: 1s
# Attempt 1: 2s
# Attempt 2: 4s
# Attempt 3: 8s
# Attempt 4: 16s
# Attempt 5: 32s
# Attempt 6: 60s (capped)
```

### Jitter
Adding randomness prevents "thundering herd" when multiple processes retry simultaneously:
```python
jitter = delay * 0.25 * random.random()
final_delay = delay + jitter
```

## Recovery Queue

Failed operations are stored in `AI_Employee_Vault/Recovery_Queue/`:
```json
{
  "operation_id": "OP_20260119_abc123",
  "action": "email_send",
  "target": "client@example.com",
  "parameters": {"subject": "Invoice"},
  "error": "Connection timeout",
  "failed_at": "2026-01-19T10:30:00Z",
  "retry_count": 0
}
```

## Quarantine System

### File Structure
```
AI_Employee_Vault/Quarantine/
├── 20260119_103000_corrupted_file.md
├── 20260119_103000_corrupted_file.md.meta.json
└── ...
```

### Metadata Format
```json
{
  "original_path": "/path/to/original/file.md",
  "quarantined_at": "2026-01-19T10:30:00Z",
  "reason": "JSON parse error on line 15",
  "file_size": 1024
}
```

## Token Refresh

### OAuth 2.0 Services
- Gmail
- Xero
- LinkedIn
- Twitter (OAuth 2.0)

### Long-Lived Tokens
- Facebook (60-day tokens)
- Instagram (60-day tokens)

### Refresh Process
1. Load current tokens from file
2. Check expiration
3. Call refresh endpoint
4. Store new tokens
5. Log the refresh

## Watchdog Configuration

### PM2 (Recommended)
```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: "orchestrator",
    script: "python",
    args: "orchestrator.py",
    watch: false,
    autorestart: true,
    max_restarts: 10,
    restart_delay: 5000,
    min_uptime: 30000
  }]
}
```

### Systemd
```ini
[Unit]
Description=AI Employee Orchestrator
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 orchestrator.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Alert Priorities

| Priority | Response Time | Examples |
|----------|---------------|----------|
| Critical | Immediate | Security breach, data loss |
| High | < 1 hour | Process crash, auth failure |
| Medium | < 24 hours | Quarantined file, rate limit |
| Low | < 7 days | Optimization suggestion |

## Troubleshooting

### Recovery queue growing
- Check for persistent failures
- Review error patterns
- May need manual intervention

### Quarantine filling up
- Review quarantined files
- Fix root cause
- Clean old files (> 30 days)

### Too many alerts
- Adjust alert thresholds
- Group similar alerts
- Automate common fixes
