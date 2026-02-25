---
name: watcher-manager
description: "WHAT: Manage watcher processes (start, stop, restart, status) using PM2 for AI Employee input detection. WHEN: User says 'start watcher', 'stop watcher', 'check watcher status', 'restart watcher'. Trigger on: watcher management, process control, monitoring."
---

# Watcher Manager

## Production Architecture Note

In the production deployment, all watchers (Gmail, WhatsApp, LinkedIn) run as threads inside the **ai-orchestrator** process. There are no separate watcher processes. The orchestrator manages all watchers internally.

## When to Use
- Starting the orchestrator (which starts all watchers)
- Stopping the orchestrator for maintenance
- Checking if the orchestrator and watchers are running
- Restarting the orchestrator after configuration changes

## Instructions

### Check Status
```bash
python .claude/skills/watcher-manager/scripts/main_operation.py --action status --target all
```
Look for `daniel-fte-orchestrator-local` and `daniel-fte-orchestrator-cloud` status `online`.

### Start Orchestrator (starts all watchers)
```bash
python .claude/skills/watcher-manager/scripts/main_operation.py --action start --target all
```

### Stop Orchestrator (stops all watchers)
```bash
python .claude/skills/watcher-manager/scripts/main_operation.py --action stop --target all
```

### Restart Orchestrator (restarts all watchers)
```bash
python .claude/skills/watcher-manager/scripts/main_operation.py --action restart --target all
```

### View Orchestrator Logs
```bash
python .claude/skills/watcher-manager/scripts/main_operation.py --action logs --target all --lines 50
```

### Check Watcher Status in Dashboard
```bash
cat AI_Employee_Vault/Dashboard.md
```

## Validation
- [ ] ai-orchestrator process shows "online" in PM2
- [ ] Dashboard.md shows watchers as "running"
- [ ] No errors in orchestrator logs
- [ ] Orchestrator uptime is stable (not restarting repeatedly)

## Troubleshooting

If orchestrator is crashing:
```bash
# Check error logs
python .claude/skills/watcher-manager/scripts/main_operation.py --action logs --target all --lines 50

# Restart fresh
python .claude/skills/watcher-manager/scripts/main_operation.py --action restart --target all

# If still failing, see SETUP_TROUBLESHOOTING.md
```

See [REFERENCE.md](./REFERENCE.md) for PM2 configuration and detailed troubleshooting.
