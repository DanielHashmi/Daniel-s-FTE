# Xero Accounting Reference

## OAuth 2.0 Setup

### 1. Create Xero App
1. Go to https://developer.xero.com/app/manage
2. Create new app (Web App)
3. Note Client ID and Client Secret
4. Set redirect URI: `http://localhost:8080/callback`

### 2. Environment Variables
```bash
export XERO_CLIENT_ID="your_client_id"
export XERO_CLIENT_SECRET="your_client_secret"
export XERO_TENANT_ID="your_tenant_id"
```

### 3. Token Refresh
Tokens expire after 30 minutes. The skill handles refresh automatically using the refresh token stored in:
`AI_Employee_Vault/Config/.xero_tokens.json`

## Xero MCP Server

For full integration, install the official Xero MCP Server:
```bash
git clone https://github.com/XeroAPI/xero-mcp-server
cd xero-mcp-server
npm install
```

Configure in `~/.config/claude-code/mcp.json`:
```json
{
  "servers": [
    {
      "name": "xero",
      "command": "node",
      "args": ["/path/to/xero-mcp-server/index.js"],
      "env": {
        "XERO_CLIENT_ID": "${XERO_CLIENT_ID}",
        "XERO_CLIENT_SECRET": "${XERO_CLIENT_SECRET}"
      }
    }
  ]
}
```

## API Rate Limits

| Endpoint | Limit |
|----------|-------|
| GET requests | 60/minute |
| POST/PUT requests | 60/minute |
| Daily limit | 5000/day |

The skill implements exponential backoff for rate limit handling.

## Transaction Categories

Default mapping from Xero chart of accounts:
- 200: Revenue
- 400: Cost of Sales
- 460: Rent/Utilities
- 470: Software Subscriptions
- 480: Professional Services

## Troubleshooting

### "Invalid tenant" error
Re-authenticate and select the correct organization.

### "Token expired" error
Delete `.xero_tokens.json` and re-authenticate.

### Missing transactions
Check date range - default is last 30 days.
