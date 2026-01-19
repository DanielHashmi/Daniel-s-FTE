---
name: xero-accounting
description: "WHAT: Sync transactions, invoices, and financial data from Xero accounting system. Generate financial summaries and reports. WHEN: User says 'sync xero', 'check revenue', 'financial summary', 'accounting report'. Trigger on: financial tracking, invoice management, expense analysis, weekly audit prep."
---

# Xero Accounting Operations

## When to Use
- Syncing transactions from Xero (daily at 6 AM recommended)
- Generating financial summaries (revenue, expenses, net profit)
- Retrieving invoices and payment status
- Preparing data for CEO Briefing
- Analyzing expense categories and trends

## Instructions

1. **Sync Transactions** (retrieves last 30 days):
   ```bash
   python3 .claude/skills/xero-accounting/scripts/main_operation.py --action sync
   ```
   *Syncs invoices, payments, expenses from Xero. Prevents duplicates.*

2. **Financial Summary**:
   ```bash
   python3 .claude/skills/xero-accounting/scripts/main_operation.py --action summary --period monthly
   ```
   *Options: `--period daily|weekly|monthly|custom --start YYYY-MM-DD --end YYYY-MM-DD`*

3. **List Invoices**:
   ```bash
   python3 .claude/skills/xero-accounting/scripts/main_operation.py --action invoices --status unpaid
   ```
   *Options: `--status all|paid|unpaid|overdue`*

4. **Expense Analysis**:
   ```bash
   python3 .claude/skills/xero-accounting/scripts/main_operation.py --action expenses --top 10
   ```
   *Categorizes expenses and shows top spending areas.*

5. **Check Status**:
   ```bash
   python3 .claude/skills/xero-accounting/scripts/main_operation.py --action status
   ```

## Environment Variables Required
```bash
XERO_CLIENT_ID=your_client_id
XERO_CLIENT_SECRET=your_client_secret
XERO_TENANT_ID=your_tenant_id
# Token refresh handled automatically
```

## Output Files
- `AI_Employee_Vault/Accounting/transactions_YYYY-MM.json` - Monthly transaction data
- `AI_Employee_Vault/Accounting/summary_YYYY-MM-DD.md` - Financial summaries
- `AI_Employee_Vault/Accounting/invoices_current.json` - Active invoices

## Validation
- [ ] Xero API authenticated successfully
- [ ] Transactions synced without duplicates
- [ ] Financial calculations accurate
- [ ] Audit log entry created

See [REFERENCE.md](./REFERENCE.md) for OAuth setup and API details.
