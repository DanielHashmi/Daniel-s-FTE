# Setup Troubleshooting Guide

This guide covers common issues encountered during setup and their solutions.

---

## Issue 1: PM2 Services Crash with "ModuleNotFoundError"

**Symptoms:**
```
ModuleNotFoundError: No module named 'google'
ModuleNotFoundError: No module named 'fastmcp'
ModuleNotFoundError: No module named 'playwright'
```

**Root Cause:** PM2 is using system Python instead of the virtual environment Python.

**Solution:**
The project uses wrapper scripts that activate the virtual environment before running Python. These are already configured in `ecosystem.config.js`:
- `run-orchestrator.sh`
- `run-mcp-email.sh`
- `run-mcp-social.sh`

**Verify wrapper scripts exist:**
```bash
ls -la run-*.sh
```

**If missing, recreate them:**
```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Create orchestrator wrapper
cat > run-orchestrator.sh << 'EOF'
#!/bin/bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
export PYTHONPATH="/mnt/c/Users/kk/Desktop/Daniel's FTE"
exec python3 src/orchestration/orchestrator.py
EOF

# Create email MCP wrapper
cat > run-mcp-email.sh << 'EOF'
#!/bin/bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
export PYTHONPATH="/mnt/c/Users/kk/Desktop/Daniel's FTE"
exec python3 src/mcp/email_server.py
EOF

# Create social MCP wrapper
cat > run-mcp-social.sh << 'EOF'
#!/bin/bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
export PYTHONPATH="/mnt/c/Users/kk/Desktop/Daniel's FTE"
exec python3 src/mcp/social_server.py
EOF

# Make executable
chmod +x run-*.sh

# Restart PM2
pm2 restart all
```

---

## Issue 2: "AttributeError: 'AuditLogger' object has no attribute 'warning'"

**Symptoms:**
```
AttributeError: 'AuditLogger' object has no attribute 'warning'
```

**Root Cause:** The AuditLogger class only has `info()` and `error()` methods, not `warning()`.

**Solution:**
This has been fixed in `src/watchers/gmail.py`. If you see this error, update the file:

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
# Edit src/watchers/gmail.py line 58
# Change: self.logger.warning("Gmail credentials not available...")
# To: self.logger.info("Gmail credentials not available...")
```

Or use sed:
```bash
sed -i 's/self.logger.warning/self.logger.info/g' src/watchers/gmail.py
pm2 restart ai-orchestrator
```

---

## Issue 3: "KeyError: 'root'" in dashboard_manager.py

**Symptoms:**
```
KeyError: 'root'
```

**Root Cause:** The vault object doesn't have a "root" key in its `dirs` dictionary. The root path is accessed via `vault.root` directly.

**Solution:**
This has been fixed in `src/orchestration/dashboard_manager.py`. If you see this error, update line 16:

```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
# Edit src/orchestration/dashboard_manager.py line 16
# Change: self.dashboard_path = vault.dirs["root"] / "Dashboard.md"
# To: self.dashboard_path = vault.root / "Dashboard.md"
```

Or use sed:
```bash
sed -i 's/vault.dirs\["root"\]/vault.root/g' src/orchestration/dashboard_manager.py
pm2 restart ai-orchestrator
```

---

## Issue 4: WhatsApp Watcher Fails with "libnspr4.so: cannot open shared object file"

**Symptoms:**
```
error while loading shared libraries: libnspr4.so: cannot open shared object file
```

**Root Cause:** Missing system library required by Playwright on WSL2/Linux.

**Solution:**
```bash
sudo apt-get update
sudo apt-get install libnspr4
pm2 restart ai-orchestrator
```

---

## Issue 5: Virtual Environment Not Found

**Symptoms:**
```
bash: venv/bin/activate: No such file or directory
```

**Root Cause:** Virtual environment hasn't been created.

**Solution:**
```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
python3 -m venv venv
source venv/bin/activate
pip install watchdog google-auth google-auth-oauthlib google-api-python-client pyyaml python-dotenv playwright fastmcp mcp
playwright install chromium
```

---

## Issue 6: PM2 Shows High Restart Count

**Symptoms:**
```
│ 0   │ ai-orchestrator  │ online  │ 15      │ 10s     │
```

**Root Cause:** Service is crashing and PM2 is auto-restarting it.

**Solution:**
```bash
# Check error logs
pm2 logs ai-orchestrator --err --lines 50

# Common causes:
# 1. Missing dependencies - see Issue 1
# 2. Code errors - see Issues 2 and 3
# 3. Permission issues - check file permissions
# 4. Path issues - verify PYTHONPATH in wrapper scripts

# After fixing, delete and restart fresh
pm2 delete all
pm2 start ecosystem.config.js
```

---

## Issue 7: "externally-managed-environment" Error

**Symptoms:**
```
error: externally-managed-environment
```

**Root Cause:** System Python is protected by PEP 668 on newer systems.

**Solution:**
Always use the virtual environment:
```bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
pip install [package]
```

Never use `sudo pip install` or system pip directly.

---

## Issue 8: Services Start but Don't Process Actions

**Symptoms:**
- PM2 shows all services "online"
- No action files are being processed
- No logs appearing

**Solution:**
```bash
# Check if orchestrator is actually running
pm2 logs ai-orchestrator --lines 50

# Verify vault structure exists
ls -la AI_Employee_Vault/

# Create a test action file
cat > AI_Employee_Vault/Needs_Action/test.md << 'EOF'
---
id: "test_001"
type: "email"
source: "manual"
priority: "high"
timestamp: "2026-01-15T12:00:00Z"
status: "pending"
---

Test action file
EOF

# Wait 10 seconds and check if plan was created
sleep 10
ls AI_Employee_Vault/Plans/
```

---

## Issue 9: Gmail Authentication Fails

**Symptoms:**
- Browser doesn't open during authentication
- "credentials.json not found" error

**Solution:**
```bash
# Verify credentials file exists
ls -la credentials.json

# If missing, download from Google Cloud Console
# Then copy to project root

# Run authentication with virtual environment
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
python3 -c "
from src.watchers.gmail import GmailWatcher
w = GmailWatcher()
w._authenticate()
"
```

---

## Issue 10: Slow Startup on WSL2

**Symptoms:**
- Services take 30+ seconds to start
- KeyboardInterrupt errors in logs during startup

**Root Cause:** WSL2 file system performance when accessing Windows files.

**Solution:**
This is normal on WSL2. The services will eventually start. Wait 30-60 seconds after `pm2 start` before checking status.

**Workaround for faster startup:**
Move the project to native Linux filesystem:
```bash
# Copy project to Linux home directory
cp -r "/mnt/c/Users/kk/Desktop/Daniel's FTE" ~/ai-employee
cd ~/ai-employee
# Update all paths in ecosystem.config.js and wrapper scripts
# Then start PM2
```

---

## Verification Checklist

After fixing issues, verify everything works:

```bash
# 1. Check PM2 status
pm2 status
# All services should show "online" with low restart count

# 2. Check logs for errors
pm2 logs --err --lines 20
# Should be minimal or no errors

# 3. Verify orchestrator is running
pm2 logs ai-orchestrator --lines 10
# Should see JSON log entries

# 4. Test with action file
cat > AI_Employee_Vault/Needs_Action/test_$(date +%s).md << 'EOF'
---
id: "test_001"
type: "email"
source: "manual"
priority: "high"
timestamp: "2026-01-15T12:00:00Z"
status: "pending"
---

Test action
EOF

# 5. Wait and check for plan
sleep 10
ls AI_Employee_Vault/Plans/
# Should see a new plan file

# 6. Check for approval request
ls AI_Employee_Vault/Pending_Approval/
# Should see an approval request file
```

---

## Getting Help

If issues persist:

1. **Check logs:**
   ```bash
   pm2 logs --err --lines 100 > error_log.txt
   ```

2. **Verify dependencies:**
   ```bash
   source venv/bin/activate
   pip list | grep -E "(google|playwright|fastmcp|mcp)"
   ```

3. **Check file permissions:**
   ```bash
   ls -la run-*.sh
   ls -la AI_Employee_Vault/
   ```

4. **Restart from scratch:**
   ```bash
   pm2 delete all
   pm2 start ecosystem.config.js
   sleep 30
   pm2 status
   ```
