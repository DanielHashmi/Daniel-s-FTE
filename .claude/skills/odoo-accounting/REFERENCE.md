# Odoo Accounting Reference

## JSON-RPC API Setup

### 1. Configure Odoo Server

Ensure your Odoo Community instance has the following:
- REST API enabled (default in Odoo 14+)
- Accounting module installed
- Users or Contacts module installed
- External API access enabled

### 2. Create API User

1. Login to Odoo as administrator
2. Navigate to Settings → Users & Companies → Users
3. Create/Edit user for API access
4. Enable "Portal" or "Internal User" access
5. Create API key: Preferences → Account Security → API Keys → Generate Key
6. Copy and securely store the API key (shown only once)

### 3. Environment Variables

```bash
export ODOO_URL="http://localhost:8069"  # Your Odoo instance URL
export ODOO_DB="your_database_name"      # Database name
export ODOO_USER="api_user@company.com"  # User login/email
export ODOO_PASSWORD="your_api_key"      # Generated API key (preferred)
```

### 4. Configure Python Environment

Install odoo-api-client for easier integration:
```bash
pip install odoo-api-client
```

Or use built-in xmlrpc.client (Python standard library).

## Odoo MCP Server

For full integration, use the Odoo MCP Server:
```bash
git clone https://github.com/OCA/mcp-odoo-server
cd mcp-odoo-server
pip install -r requirements.txt
```

Configure in `~/.config/claude-code/mcp.json`:
```json
{
  "servers": [
    {
      "name": "odoo",
      "command": "python",
      "args": ["/path/to/mcp-odoo-server/server.py"],
      "env": {
        "ODOO_URL": "${ODOO_URL}",
        "ODOO_DB": "${ODOO_DB}",
        "ODOO_USER": "${ODOO_USER}",
        "ODOO_PASSWORD": "${ODOO_PASSWORD}"
      }
    }
  ]
}
```

## API Rate Limits

Odoo doesn't enforce strict rate limits by default, but consider:

| Operation | Recommended Limit |
|-----------|-------------------|
| Read operations | 100/minute |
| Write operations | 50/minute |
| Large queries | Use pagination (limit/offset) |

The skill implements connection pooling and efficient queries.

## Core Odoo Models

### Accounting Models
- **account.move** - Invoices, bills, journal entries
- **account.payment** - Customer/vendor payments
- **account.journal** - Journals (sales, purchases, bank, etc.)
- **account.account** - Chart of accounts

### Contact Models
- **res.partner** - Customers, vendors, contacts

### Product Models (for invoicing)
- **product.template** - Product catalog
- **product.product** - Product variants

## Default Chart of Accounts

Common Odoo account types (customize in your Odoo instance):
- 400000 - Income/Revenue
- 500000 - Cost of Revenue
- 600000 - Expenses
- 101000 - Bank and Cash
- 121000 - Accounts Receivable
- 211000 - Accounts Payable

## Troubleshooting

### "Authentication failed"
- Verify API key is still active
- Check user has appropriate permissions
- Confirm database name is correct

### "Access denied" on specific models
- User needs appropriate Odoo security groups:
  - Accounting & Finance
  - Contacts/Vendors
  - Sales/Purchases

### Connection timeout
- Check Odoo server is running: `netstat -tln | grep 8069`
- Verify firewall allows connection
- Test with `curl http://localhost:8069`

### Missing transactions
- Check Odoo user timezone settings
- Verify Odoo company fiscal year settings
- Default query range: last 30 days

## Common Workflows

### Create Invoice
```python
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
invoice = models.execute_kw(
    db, uid, password, 'account.move', 'create',
    [{'partner_id': partner_id, 'move_type': 'out_invoice', 'invoice_line_ids': [...]}]
)
```

### Record Payment
```python
payment = models.execute_kw(
    db, uid, password, 'account.payment', 'create',
    [{'payment_type': 'inbound', 'partner_type': 'customer', 'amount': 1000.0}]
)
```

### Query Account Balance
```python
accounts = models.execute_kw(
    db, uid, password, 'account.account', 'search_read',
    [[('code', '=', '400000')]],
    {'fields': ['code', 'name', 'balance']}
)
```

See the Odoo official documentation for complete API reference.
