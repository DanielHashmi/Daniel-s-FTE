# Quickstart Guide: Gold Tier Autonomous Employee

**Feature**: Gold Tier Autonomous Employee
**Date**: 2026-01-19
**Audience**: Developers implementing Gold Tier capabilities

## Overview

This quickstart guide provides step-by-step instructions for implementing Gold Tier autonomous employee capabilities. Follow these steps in order to ensure proper setup and integration.

---

## Prerequisites

Before starting Gold Tier implementation, ensure:

- ✅ **Bronze Tier Complete**: Obsidian vault, one watcher, Claude Code integration
- ✅ **Silver Tier Complete**: Multiple watchers, MCP servers, HITL workflow, scheduling
- ✅ **Python 3.13+**: Installed and configured
- ✅ **Node.js v24+**: Installed for PM2 and Claude Code CLI
- ✅ **PM2**: Installed and configured (`ecosystem.config.js` exists)
- ✅ **Git**: Repository initialized with proper `.gitignore`

**Verify Prerequisites**:
```bash
python --version  # Should be 3.13+
node --version    # Should be v24+
pm2 --version     # Should be installed
git status        # Should show clean working tree
```

---

## Phase 1: Install Dependencies

### 1.1 Install Python SDKs

```bash
# Navigate to project root
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Install Xero SDK
pip install xero-python

# Install Facebook SDK
pip install --upgrade python-facebook-api

# Install Twitter SDK
pip install tweepy

# Install additional dependencies
pip install psutil  # For watchdog enhancements
```

### 1.2 Verify Installations

```bash
python -c "import xero_python; print('Xero SDK:', xero_python.__version__)"
python -c "import pyfacebook; print('Facebook SDK installed')"
python -c "import tweepy; print('Tweepy:', tweepy.__version__)"
python -c "import psutil; print('psutil:', psutil.__version__)"
```

---

## Phase 2: Configure External APIs

### 2.1 Xero API Setup

1. **Create Xero Developer Account**:
   - Visit https://developer.xero.com/
   - Create a new app
   - Note: Client ID, Client Secret, Redirect URI

2. **Configure Environment Variables**:
```bash
# Add to .env file (ensure .env is in .gitignore)
echo "XERO_CLIENT_ID=your_client_id" >> .env
echo "XERO_CLIENT_SECRET=your_client_secret" >> .env
echo "XERO_REDIRECT_URI=http://localhost:8080/callback" >> .env
```

3. **Obtain OAuth Tokens**:
```bash
# Run OAuth flow (implementation in src/mcp/xero_server.py)
python src/mcp/xero_server.py --auth
```

### 2.2 Facebook API Setup

1. **Create Facebook App**:
   - Visit https://developers.facebook.com/
   - Create a new app (Business type)
   - Add Facebook Login and Pages API products
   - Note: App ID, App Secret

2. **Configure Environment Variables**:
```bash
echo "FACEBOOK_APP_ID=your_app_id" >> .env
echo "FACEBOOK_APP_SECRET=your_app_secret" >> .env
echo "FACEBOOK_ACCESS_TOKEN=your_long_lived_token" >> .env
```

3. **Obtain Long-Lived Access Token**:
```bash
# Follow Facebook's token exchange process
# https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived
```

### 2.3 Instagram API Setup

1. **Convert to Business Account**:
   - Instagram account must be Business or Creator
   - Connect to Facebook Page

2. **Configure Environment Variables**:
```bash
echo "INSTAGRAM_ACCOUNT_ID=your_instagram_business_id" >> .env
# Uses same FACEBOOK_ACCESS_TOKEN from above
```

### 2.4 Twitter API Setup

1. **Create Twitter Developer Account**:
   - Visit https://developer.twitter.com/
   - Create a new project and app
   - Note: API Key, API Secret, Bearer Token, Access Token, Access Secret

2. **Configure Environment Variables**:
```bash
echo "TWITTER_API_KEY=your_api_key" >> .env
echo "TWITTER_API_SECRET=your_api_secret" >> .env
echo "TWITTER_BEARER_TOKEN=your_bearer_token" >> .env
echo "TWITTER_ACCESS_TOKEN=your_access_token" >> .env
echo "TWITTER_ACCESS_SECRET=your_access_secret" >> .env
```

3. **Verify API Access**:
```bash
python -c "
import tweepy
import os
client = tweepy.Client(bearer_token=os.getenv('TWITTER_BEARER_TOKEN'))
user = client.get_me()
print(f'Authenticated as: {user.data.username}')
"
```

---

## Phase 3: Implement MCP Servers

### 3.1 Create Xero MCP Server

```bash
# Create MCP server file
touch src/mcp/xero_server.py
```

**Implementation Template** (`src/mcp/xero_server.py`):
```python
#!/usr/bin/env python3
"""Xero MCP Server for accounting integration."""

import os
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.accounting import AccountingApi

class XeroMCPServer:
    def __init__(self):
        self.config = Configuration()
        self.api_client = ApiClient(
            oauth2_token=OAuth2Token(
                client_id=os.getenv("XERO_CLIENT_ID"),
                client_secret=os.getenv("XERO_CLIENT_SECRET")
            )
        )
        self.accounting_api = AccountingApi(self.api_client)

    def sync_transactions(self, period="last_30_days"):
        """Sync transactions from Xero."""
        # Implementation here
        pass

if __name__ == "__main__":
    server = XeroMCPServer()
    # MCP server loop
```

### 3.2 Create Social Media MCP Servers

```bash
# Create Facebook MCP server
touch src/mcp/facebook_server.py

# Create Instagram MCP server
touch src/mcp/instagram_server.py

# Create Twitter MCP server
touch src/mcp/twitter_server.py
```

**Twitter MCP Server Template** (`src/mcp/twitter_server.py`):
```python
#!/usr/bin/env python3
"""Twitter MCP Server for social media posting."""

import os
import tweepy

class TwitterMCPServer:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
            wait_on_rate_limit=True
        )

    def create_tweet(self, text):
        """Create a tweet."""
        response = self.client.create_tweet(text=text)
        return response.data

if __name__ == "__main__":
    server = TwitterMCPServer()
    # MCP server loop
```

### 3.3 Update MCP Configuration

Add new MCP servers to Claude Code configuration:

```bash
# Edit ~/.config/claude-code/mcp.json
nano ~/.config/claude-code/mcp.json
```

**Add to `mcp.json`**:
```json
{
  "servers": [
    {
      "name": "xero",
      "command": "python",
      "args": ["/mnt/c/Users/kk/Desktop/Daniel's FTE/src/mcp/xero_server.py"],
      "env": {
        "XERO_CLIENT_ID": "${XERO_CLIENT_ID}",
        "XERO_CLIENT_SECRET": "${XERO_CLIENT_SECRET}"
      }
    },
    {
      "name": "facebook",
      "command": "python",
      "args": ["/mnt/c/Users/kk/Desktop/Daniel's FTE/src/mcp/facebook_server.py"],
      "env": {
        "FACEBOOK_APP_ID": "${FACEBOOK_APP_ID}",
        "FACEBOOK_ACCESS_TOKEN": "${FACEBOOK_ACCESS_TOKEN}"
      }
    },
    {
      "name": "twitter",
      "command": "python",
      "args": ["/mnt/c/Users/kk/Desktop/Daniel's FTE/src/mcp/twitter_server.py"],
      "env": {
        "TWITTER_BEARER_TOKEN": "${TWITTER_BEARER_TOKEN}"
      }
    }
  ]
}
```

---

## Phase 4: Implement Ralph Wiggum Loop

### 4.1 Create Plugin Directory

```bash
mkdir -p .claude/plugins/ralph-wiggum
mkdir -p .claude/state
```

### 4.2 Create Stop Hook Script

```bash
touch .claude/plugins/ralph-wiggum/stop-hook.sh
chmod +x .claude/plugins/ralph-wiggum/stop-hook.sh
```

**Stop Hook Implementation** (`.claude/plugins/ralph-wiggum/stop-hook.sh`):
```bash
#!/bin/bash
# Ralph Wiggum Stop Hook - Persistent Task Execution

STATE_FILE=".claude/state/ralph-state.json"

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
    exit 0  # No active Ralph loop, allow exit
fi

# Read state
TASK_FILE=$(jq -r '.task_file' "$STATE_FILE")
ITERATION=$(jq -r '.iteration' "$STATE_FILE")
MAX_ITERATIONS=$(jq -r '.max_iterations' "$STATE_FILE")
COMPLETION_STRATEGY=$(jq -r '.completion_strategy' "$STATE_FILE")

# Check completion (file movement strategy)
if [ "$COMPLETION_STRATEGY" = "file_movement" ]; then
    TASK_BASENAME=$(basename "$TASK_FILE")
    if [ -f "AI_Employee_Vault/Done/$TASK_BASENAME" ]; then
        echo "✅ Task complete - file moved to Done/"
        rm "$STATE_FILE"
        exit 0
    fi
fi

# Check max iterations
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ]; then
    echo "⚠️ Max iterations reached - escalating to human"
    # Create human review request
    REVIEW_FILE="AI_Employee_Vault/Pending_Approval/REVIEW_$(date +%s).md"
    cat > "$REVIEW_FILE" <<EOF
---
type: human_review_request
reason: max_iterations_reached
task_file: $TASK_FILE
iterations_completed: $ITERATION
---

# Human Review Required

The Ralph Wiggum loop reached maximum iterations ($MAX_ITERATIONS) without completing the task.

**Task File**: $TASK_FILE
**Iterations Completed**: $ITERATION

Please review the task and determine next steps.
EOF
    rm "$STATE_FILE"
    exit 0
fi

# Increment iteration and continue
NEW_ITERATION=$((ITERATION + 1))
jq ".iteration = $NEW_ITERATION | .last_iteration_at = \"$(date -Iseconds)\"" "$STATE_FILE" > "$STATE_FILE.tmp"
mv "$STATE_FILE.tmp" "$STATE_FILE"

echo "🔄 Continuing Ralph loop - Iteration $NEW_ITERATION/$MAX_ITERATIONS"
exit 1  # Block exit, continue loop
```

### 4.3 Create Configuration File

```bash
touch .claude/plugins/ralph-wiggum/config.json
```

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

---

## Phase 5: Implement Agent Skills

### 5.1 Create Skills Directory Structure

```bash
mkdir -p .claude/skills/accounting-sync
mkdir -p .claude/skills/briefing-gen
mkdir -p .claude/skills/error-recovery
mkdir -p .claude/skills/audit-mgmt
```

### 5.2 Create Accounting Sync Skill

```bash
touch .claude/skills/accounting-sync/skill.json
touch .claude/skills/accounting-sync/skill.md
```

**Skill Definition** (`.claude/skills/accounting-sync/skill.json`):
```json
{
  "name": "accounting-sync",
  "description": "Sync financial transactions from Xero accounting system",
  "version": "1.0.0",
  "command": "python src/skills/accounting_sync/main.py",
  "parameters": {
    "period": {
      "type": "string",
      "description": "Time period to sync",
      "default": "last_30_days"
    },
    "dry_run": {
      "type": "boolean",
      "default": false
    }
  }
}
```

### 5.3 Create CEO Briefing Skill

```bash
touch .claude/skills/briefing-gen/skill.json
touch .claude/skills/briefing-gen/skill.md
```

**Skill Definition** (`.claude/skills/briefing-gen/skill.json`):
```json
{
  "name": "briefing-gen",
  "description": "Generate weekly CEO Briefing with business intelligence",
  "version": "1.0.0",
  "command": "python src/skills/briefing_gen/main.py",
  "parameters": {
    "period_start": {
      "type": "string",
      "default": "auto"
    },
    "period_end": {
      "type": "string",
      "default": "auto"
    }
  }
}
```

---

## Phase 6: Enhance Watchdog

### 6.1 Update Existing Watchdog

Edit `src/orchestration/watchdog.py` to add PM2 health checks:

```python
# Add to src/orchestration/watchdog.py

def check_pm2_health(self):
    """Check if PM2 daemon is running."""
    try:
        result = subprocess.run(["pm2", "ping"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False

def get_pm2_metrics(self):
    """Get CPU/memory metrics from PM2."""
    result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
    processes = json.loads(result.stdout)
    return {
        proc['name']: {
            'status': proc['pm2_env']['status'],
            'uptime': proc['pm2_env']['pm_uptime'],
            'restarts': proc['pm2_env']['restart_time'],
            'memory': proc['monit']['memory'],
            'cpu': proc['monit']['cpu']
        }
        for proc in processes
    }
```

### 6.2 Configure WSL2 Auto-Start

**Windows Task Scheduler** (for WSL2):

1. Open Task Scheduler
2. Create Basic Task
3. Name: "AI Employee Auto-Start"
4. Trigger: At log on
5. Action: Start a program
6. Program: `wsl`
7. Arguments: `-d Ubuntu -- bash -c "cd '/mnt/c/Users/kk/Desktop/Daniel'\''s FTE' && pm2 resurrect"`

---

## Phase 7: Create Vault Folders

```bash
# Create new Gold Tier folders
mkdir -p AI_Employee_Vault/Accounting/transactions
mkdir -p AI_Employee_Vault/Accounting/summaries
mkdir -p AI_Employee_Vault/Briefings
mkdir -p AI_Employee_Vault/Logs/errors
mkdir -p AI_Employee_Vault/Logs/Archive
mkdir -p AI_Employee_Vault/Quarantine
mkdir -p AI_Employee_Vault/Social_Media
```

---

## Phase 8: Testing

### 8.1 Test MCP Servers

```bash
# Test Xero connection
python src/mcp/xero_server.py --test

# Test Twitter posting (dry run)
python src/mcp/twitter_server.py --test --dry-run

# Test Facebook posting (dry run)
python src/mcp/facebook_server.py --test --dry-run
```

### 8.2 Test Ralph Wiggum Loop

```bash
# Create test task file
cat > AI_Employee_Vault/Needs_Action/TEST_TASK.md <<EOF
---
type: test
priority: low
---

# Test Task

This is a test task for Ralph Wiggum loop.

Steps:
1. Read this file
2. Create a response file
3. Move this file to Done/
EOF

# Start Ralph loop (manual test)
# The orchestrator will pick this up automatically
```

### 8.3 Test Agent Skills

```bash
# Test accounting sync (dry run)
/accounting-sync dry_run=true

# Test briefing generation (dry run)
/briefing-gen dry_run=true

# Test error recovery
/error-recovery action=status component=all
```

---

## Phase 9: Production Deployment

### 9.1 Update PM2 Configuration

Add new processes to `ecosystem.config.js`:

```javascript
{
  apps: [
    // Existing processes...
    {
      name: "xero-sync",
      script: "src/skills/accounting_sync/scheduler.py",
      cwd: "/mnt/c/Users/kk/Desktop/Daniel's FTE",
      interpreter: "python3",
      autorestart: true,
      max_memory_restart: "200M"
    },
    {
      name: "briefing-gen",
      script: "src/skills/briefing_gen/scheduler.py",
      cwd: "/mnt/c/Users/kk/Desktop/Daniel's FTE",
      interpreter: "python3",
      autorestart: true,
      max_memory_restart: "200M"
    }
  ]
}
```

### 9.2 Start All Processes

```bash
# Reload PM2 configuration
pm2 reload ecosystem.config.js

# Save process list
pm2 save

# Verify all processes running
pm2 list
```

### 9.3 Configure Scheduled Tasks

**CEO Briefing** (Monday 7 AM):
```bash
# Add to crontab
crontab -e

# Add line:
0 7 * * 1 cd '/mnt/c/Users/kk/Desktop/Daniel'\''s FTE' && /briefing-gen
```

**Xero Sync** (Daily 6 AM):
```bash
# Add to crontab
0 6 * * * cd '/mnt/c/Users/kk/Desktop/Daniel'\''s FTE' && /accounting-sync
```

---

## Troubleshooting

### Issue: OAuth Token Expired

**Symptom**: API calls fail with 401 Unauthorized

**Solution**:
```bash
# Re-authenticate with Xero
python src/mcp/xero_server.py --auth

# Re-authenticate with Facebook
# Follow token exchange process in Facebook Developer Console
```

### Issue: Ralph Loop Not Starting

**Symptom**: Tasks remain in Needs_Action/ folder

**Solution**:
```bash
# Check stop hook is executable
chmod +x .claude/plugins/ralph-wiggum/stop-hook.sh

# Check state file permissions
ls -la .claude/state/

# Check orchestrator logs
pm2 logs ai-orchestrator
```

### Issue: MCP Server Not Connecting

**Symptom**: Skills fail with "MCP server not available"

**Solution**:
```bash
# Verify MCP configuration
cat ~/.config/claude-code/mcp.json

# Test MCP server manually
python src/mcp/xero_server.py --test

# Check Claude Code logs
claude --debug
```

---

## Next Steps

After completing this quickstart:

1. **Monitor System**: Check Dashboard.md daily for system status
2. **Review Logs**: Check audit logs weekly for anomalies
3. **Test HITL Workflow**: Verify approval requests are created correctly
4. **Optimize Performance**: Monitor CEO Briefing generation time
5. **Document Lessons Learned**: Update architecture documentation

---

## Support & Resources

- **Specification**: `specs/003-gold-tier/spec.md`
- **Implementation Plan**: `specs/003-gold-tier/plan.md`
- **Research**: `specs/003-gold-tier/research.md`
- **Data Model**: `specs/003-gold-tier/data-model.md`
- **Contracts**: `specs/003-gold-tier/contracts/interfaces.md`
- **Hackathon Guide**: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`

---

**Congratulations!** You've completed the Gold Tier setup. Your AI Employee is now a fully autonomous business partner capable of managing complex multi-step operations, providing weekly business intelligence, and operating 24/7 with minimal human oversight.
