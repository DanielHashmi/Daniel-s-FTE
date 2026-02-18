---
name: odoo-accounting
description: "WHAT: Sync transactions, invoices, and financial data from Odoo accounting system. Generate financial summaries and reports. WHEN: User says 'sync odoo', 'check revenue', 'financial summary', 'accounting report'. Trigger on: financial tracking, invoice management, expense analysis, weekly audit prep."
---

# Odoo Accounting Operations

## When to Use
- Syncing transactions from Odoo (daily at 6 AM recommended)
- Generating financial summaries (revenue, expenses, net profit)
- Retrieving invoices and payment status
- Preparing data for CEO Briefing
- Analyzing expense categories and trends

## Instructions

1. **Sync Transactions** (retrieves last 30 days):
   ```bash
   python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft sync
   ```
   *Syncs invoices, payments, expenses from Odoo. Prevents duplicates.*

2. **Financial Summary**:
   ```bash
   python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft summary --limit 100
   ```
   *Use `--limit` to control returned invoice rows.*

3. **List Invoices**:
   ```bash
   python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft summary
   ```
   *Returns draft-invoice summary suitable for cloud review.*

4. **Validate Invoice**:
   ```bash
   python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft validate 15
   ```
   *Validates invoice fields before posting.*

5. **Post Invoice (Live Mode, HITL by default)**:
   ```bash
   python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode live post 15
   ```

6. **Verify Connection**:
   ```bash
   python3 .claude/skills/odoo-accounting/scripts/verify_operation.py
   ```

## Environment Variables Required
```bash
ODOO_URL=http://localhost:8069
ODOO_DB=your_database_name
ODOO_USERNAME=your_user_login
ODOO_PASSWORD=your_api_key_or_password
# API key allows secure access without main password
```

## Output Files
- `AI_Employee_Vault/Accounting/transactions_YYYY-MM.json` - Monthly transaction data
- `AI_Employee_Vault/Accounting/summary_YYYY-MM-DD.md` - Financial summaries
- `AI_Employee_Vault/Accounting/invoices_current.json` - Active invoices

## Validation
- [ ] Odoo API authenticated successfully
- [ ] Transactions synced without duplicates
- [ ] Financial calculations accurate
- [ ] Audit log entry created

See [REFERENCE.md](./REFERENCE.md) for JSON-RPC setup and API details.
