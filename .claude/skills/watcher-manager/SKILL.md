---
name: watcher-manager
description: "WHAT: Manage watcher processes (start, stop, restart, status) using PM2 for AI Employee input detection. WHEN: User says 'start watcher', 'stop watcher', 'check watcher status', 'restart watcher'. Trigger on: watcher management, process control, monitoring."
---

# Watcher Manager

## When to Use
- Starting watcher for first time or after system restart
- Stopping watcher for maintenance or troubleshooting
- Checking if watcher is running and healthy
- Restarting watcher after configuration changes

## Instructions
1. Execute watcher command: `python3 scripts/main_operation.py --action [start|stop|restart|status] [--watcher-type filesystem|gmail] [--vault-path AI_Employee_Vault]`
2. Verify watcher state: `python3 scripts/verify_operation.py`
3. Check Dashboard.md for updated watcher status.

## Validation
- [ ] Watcher process started/stopped successfully
- [ ] PM2 shows correct process status
- [ ] Dashboard.md updated with watcher status
- [ ] No errors in watcher logs

See [REFERENCE.md](./REFERENCE.md) for PM2 configuration and troubleshooting.
