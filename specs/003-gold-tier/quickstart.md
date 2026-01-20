# Quick Start Guide: Gold Tier Autonomous Employee

## 1. Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** installed (for Claude Code)
- **Odoo 19 (Community Edition)** instance access (URL, DB, User, API Key/Password)
- **Facebook/Instagram/Twitter Developer Accounts** (for social media features)
- **Silver Tier** completed and operational

## 2. Installation

### 2.1 Install Dependencies

```bash
# Install required Python packages
pip install requests python-facebook-api tweepy psutil
```

### 2.2 Configure Environment Variables

Create or update your `.env` file with the following credentials:

```bash
# Odoo Accounting Configuration
echo "ODOO_URL=https://your-odoo-instance.com" >> .env
echo "ODOO_DB=your_database_name" >> .env
echo "ODOO_USER=your_username_or_email" >> .env
echo "ODOO_PASSWORD=your_api_key_or_password" >> .env

# Social Media Configuration
echo "FACEBOOK_ACCESS_TOKEN=your_token" >> .env
echo "INSTAGRAM_ACCESS_TOKEN=your_token" >> .env
echo "TWITTER_BEARER_TOKEN=your_token" >> .env
```

### 2.3 Verify Odoo Connection

Run the verification script to check Odoo connectivity:

```bash
python .claude/skills/odoo-accounting/scripts/verify_operation.py
```

## 3. Deployment

### 3.1 Create Odoo MCP Server

The Odoo MCP server handles accounting synchronization.

1. Create the server file:
   ```bash
   touch src/mcp/odoo_server.py
   ```

2. **Implementation Template** (`src/mcp/odoo_server.py`):
   ```python
   #!/usr/bin/env python3
   """Odoo MCP Server for accounting integration."""
   import os
   import json
   import xmlrpc.client
   # ... (Implementation details using XML-RPC or JSON-2)
   ```

### 3.2 Register MCP Servers

Add the new servers to your Claude Code configuration (`~/.config/claude-code/mcp.json`):

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python3",
      "args": ["/absolute/path/to/src/mcp/odoo_server.py"],
      "env": {
        "ODOO_URL": "${ODOO_URL}",
        "ODOO_DB": "${ODOO_DB}",
        "ODOO_USER": "${ODOO_USER}",
        "ODOO_PASSWORD": "${ODOO_PASSWORD}"
      }
    }
    // ... other servers
  }
}
```

## 4. Usage

### 4.1 Run Accounting Sync

Manually trigger the daily accounting sync:

```bash
# Using Agent Skill
/odoo-accounting action=sync

# Or direct script
python .claude/skills/odoo-accounting/scripts/main_operation.py --action sync
```

### 4.2 Generate CEO Briefing

Generate the weekly briefing manually:

```bash
/ceo-briefing action=generate
```

### 4.3 Monitor System Status

Check the dashboard and logs:

```bash
/view-dashboard
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

## 5. Troubleshooting

- **Odoo Connection Failed**: Check `.env` credentials. Ensure Odoo server is reachable. If using 2FA, use an API Key instead of password.
- **Social Media Errors**: Verify tokens are not expired. Check `Logs/errors/` for detailed error messages.
- **Ralph Loop Stuck**: Check `.claude/state/ralph-state-*.json` for stuck tasks. Remove lock file if necessary.