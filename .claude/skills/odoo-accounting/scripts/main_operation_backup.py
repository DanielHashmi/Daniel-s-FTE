#!/usr/bin/env python3
"""Odoo Accounting Operations - Gold Tier Skill

Syncs transactions, invoices, and financial data from Odoo 19 (Community Edition).
Generates financial summaries and reports for CEO Briefing.

NOTE: This script currently uses XML-RPC for compatibility with standard Python libraries.
Odoo 19 has deprecated XML-RPC/JSON-RPC in favor of the JSON-2 API (to be enforced in Odoo 20).
This implementation remains functional for Odoo 19 but should be migrated to JSON-2
before Odoo 20 (Fall 2026).
"""
import argparse
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import xmlrpc.client

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"
LOGS_DIR = VAULT_ROOT / "Logs"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"


def setup_dirs():
    ACCOUNTING_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "odoo_accounting",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "odoo_accounting_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


def check_odoo_credentials() -> bool:
    """Check if Odoo credentials are configured."""
    required = ["ODOO_URL", "ODOO_DB", "ODOO_USER", "ODOO_PASSWORD"]
    return all(os.getenv(var) for var in required)


def get_odoo_connection():
    """Establish connection to Odoo via XML-RPC."""
    url = os.getenv("ODOO_URL", "http://localhost:8069")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USER")
    password = os.getenv("ODOO_PASSWORD")

    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        if not uid:
            raise Exception("Authentication failed")

        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        return db, uid, password, models
    except Exception as e:
        print(f"Odoo connection error: {e}", file=sys.stderr)
        return None, None, None, None


def sync_transactions():
    """Sync transactions from Odoo via JSON-RPC."""
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if not check_odoo_credentials() or dry_run:
        # Use sample data in dry-run mode (same format as Xero skill)
        month = datetime.now().strftime("%Y-%m")
        output_file = ACCOUNTING_DIR / f"transactions_{month}.json"

        SAMPLE_TRANSACTIONS = [
            {"id": "INV-001", "type": "invoice", "amount": 1500.00, "client": "Acme Corp", "date": "2026-01-15", "status": "paid"},
            {"id": "INV-002", "type": "invoice", "amount": 2500.00, "client": "TechStart Inc", "date": "2026-01-16", "status": "unpaid"},
            {"id": "EXP-001", "type": "expense", "amount": -99.00, "vendor": "Adobe", "category": "Software", "date": "2026-01-10"},
            {"id": "EXP-002", "type": "expense", "amount": -49.00, "vendor": "Notion", "category": "Software", "date": "2026-01-12"},
            {"id": "PAY-001", "type": "payment", "amount": 1500.00, "from": "Acme Corp", "date": "2026-01-17", "invoice": "INV-001"},
        ]

        # Load existing or start fresh
        existing = json.loads(output_file.read_text()) if output_file.exists() else []
        existing_ids = {t["id"] for t in existing}

        # Add new transactions (prevent duplicates)
        new_count = 0
        for tx in SAMPLE_TRANSACTIONS:
            if tx["id"] not in existing_ids:
                existing.append(tx)
                new_count += 1

        output_file.write_text(json.dumps(existing, indent=2))

        print(f"✓ Synced {new_count} new transactions (DRY RUN)")
        print(f"  Total: {len(existing)} transactions in {output_file.name}")
        audit_log("sync", str(output_file), "success (dry_run)", {"new": new_count, "total": len(existing)})
        return True

    # Real Odoo API integration via XML-RPC
    try:
        db, uid, password, models = get_odoo_connection()
        if not uid:
            return False

        # Sync invoices (account.move)
        # Get invoices from last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        invoices = models.execute_kw(
            db, uid, password,
            'account.move', 'search_read',
            [[['move_type', 'in', ['out_invoice', 'in_invoice']],
              ['invoice_date', '>=', thirty_days_ago]]],
            {'fields': ['name', 'amount_total', 'partner_id', 'invoice_date', 'payment_state', 'state']}
        )

        # Sync payments (account.payment)
        payments = models.execute_kw(
            db, uid, password,
            'account.payment', 'search_read',
            [[['payment_date', '>=', thirty_days_ago]]],
            {'fields': ['name', 'amount', 'partner_id', 'payment_date', 'payment_type']}
        )

        # Process and save data
        month = datetime.now().strftime("%Y-%m")
        output_file = ACCOUNTING_DIR / f"transactions_{month}.json"

        existing = json.loads(output_file.read_text()) if output_file.exists() else []
        existing_ids = {t["id"] for t in existing}

        new_count = 0

        # Add invoices to transaction list
        for inv in invoices:
            tx_id = f"INV-{inv['id']}"
            if tx_id not in existing_ids:
                tx = {
                    "id": tx_id,
                    "type": "invoice",
                    "amount": float(inv['amount_total']),
                    "client": inv.get('partner_id', [None, 'Unknown'])[1] if inv.get('partner_id') else 'Unknown',
                    "date": inv['invoice_date'],
                    "status": inv.get('payment_state', 'unknown')
                }
                existing.append(tx)
                new_count += 1

        # Add payments to transaction list
        for pay in payments:
            tx_id = f"PAY-{pay['id']}"
            if tx_id not in existing_ids:
                tx = {
                    "id": tx_id,
                    "type": "payment",
                    "amount": float(pay['amount']),
                    "from": pay.get('partner_id', [None, 'Unknown'])[1] if pay.get('partner_id') else 'Unknown',
                    "date": pay['payment_date'],
                    "invoice": None  # Link to invoice when available
                }
                existing.append(tx)
                new_count += 1

        output_file.write_text(json.dumps(existing, indent=2))

        print(f"✓ Synced {new_count} new transactions from Odoo")
        print(f"  Total: {len(existing)} transactions in {output_file.name}")
        audit_log("sync", str(output_file), "success", {"new": new_count, "total": len(existing)})
        return True

    except Exception as e:
        print(f"✗ Odoo sync failed: {e}", file=sys.stderr)
        audit_log("sync", "odoo_server", "error", {"error": str(e)})
        return False


def generate_summary(period: str, start: Optional[str] = None, end: Optional[str] = None):
    """Generate financial summary for the specified period."""
    month = datetime.now().strftime("%Y-%m")
    tx_file = ACCOUNTING_DIR / f"transactions_{month}.json"

    if not tx_file.exists():
        print("✗ No transaction data. Run sync first.")
        return False

    transactions = json.loads(tx_file.read_text())

    # Calculate totals
    revenue = sum(t["amount"] for t in transactions if t.get("type") in ["invoice", "payment"] and t["amount"] > 0)
    expenses = sum(abs(t["amount"]) for t in transactions if t.get("type") == "expense")
    net_profit = revenue - expenses

    # Category breakdown
    expense_categories = {}
    for t in transactions:
        if t.get("type") == "expense":
            cat = t.get("category", "Other")
            expense_categories[cat] = expense_categories.get(cat, 0) + abs(t["amount"])

    # Unpaid invoices
    unpaid = [t for t in transactions if t.get("type") == "invoice" and t.get("status") != "paid"]
    unpaid_total = sum(t["amount"] for t in unpaid)

    # Generate summary markdown
    summary_date = datetime.now().strftime("%Y-%m-%d")
    summary = f"""# Financial Summary - {period.capitalize()}Generated: {summary_date}

## Overview| Metric | Amount ||--------|--------|| Total Revenue | ${revenue:,.2f} || Total Expenses | ${expenses:,.2f} || Net Profit | ${net_profit:,.2f} || Unpaid Invoices | ${unpaid_total:,.2f} |

## Expense Breakdown| Category | Amount ||----------|--------|"""
    for cat, amount in sorted(expense_categories.items(), key=lambda x: -x[1]):
        summary += f"| {cat} | ${amount:,.2f} |\n"

    if unpaid:
        summary += "\n## Unpaid Invoices\n"
        for inv in unpaid:
            summary += f"- {inv['id']}: ${inv['amount']:,.2f} from {inv.get('client', 'Unknown')}\n"

    summary += f"\n---\n*Generated by odoo-accounting skill*\n"

    output_file = ACCOUNTING_DIR / f"summary_{summary_date}.md"
    output_file.write_text(summary)

    print(f"✓ Financial summary generated")
    print(f"  Revenue: ${revenue:,.2f} | Expenses: ${expenses:,.2f} | Net: ${net_profit:,.2f}")
    audit_log("summary", str(output_file), "success", {"revenue": revenue, "expenses": expenses, "net": net_profit})
    return True


def list_invoices(status: str = "all"):
    """List invoices filtered by status."""
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        # In dry-run mode, use local transaction file
        month = datetime.now().strftime("%Y-%m")
        tx_file = ACCOUNTING_DIR / f"transactions_{month}.json"

        if not tx_file.exists():
            print("✗ No transaction data. Run sync first.")
            return False

        transactions = json.loads(tx_file.read_text())
        invoices = [t for t in transactions if t.get("type") == "invoice"]

        if status != "all":
            invoices = [i for i in invoices if i.get("status") == status]

        print(f"Invoices ({status}):")
        print("-" * 60)
        for inv in invoices:
            status_emoji = "✅" if inv.get("status") == "paid" else "⏳"
            print(f"{status_emoji} {inv['id']}: ${inv['amount']:,.2f} - {inv.get('client', 'Unknown')} [{inv.get('status', 'unknown')}]")

        print(f"\nTotal: {len(invoices)} invoice(s)")
        return True

    # Real Odoo integration - query invoices
    try:
        db, uid, password, models = get_odoo_connection()
        if not uid:
            return False

        domain = [['move_type', 'in', ['out_invoice', 'in_invoice']]]
        if status != "all":
            domain.append(['payment_state', '=', status])

        invoices = models.execute_kw(
            db, uid, password,
            'account.move', 'search_read',
            [domain],
            {'fields': ['name', 'amount_total', 'amount_residual', 'partner_id',
                       'invoice_date', 'invoice_date_due', 'payment_state', 'state'],
             'limit': 100, 'order': 'invoice_date desc'}
        )

        print(f"Invoices from Odoo ({status}):")
        print("-" * 80)
        for inv in invoices:
            status_emoji = "✅" if inv.get('payment_state') == 'paid' else "⏳"
            partner = inv.get('partner_id', [None, 'Unknown'])[1] if inv.get('partner_id') else 'Unknown'
            due_date = inv.get('invoice_date_due', 'N/A')
            print(f"{status_emoji} {inv['name']}: ${inv['amount_total']:,.2f}")
            print(f"    Client: {partner} | Due: {due_date} | Status: {inv.get('payment_state')}")
            print(f"    Outstanding: ${inv.get('amount_residual', 0):,.2f}")
            print()

        print(f"Total: {len(invoices)} invoice(s)")
        audit_log("list_invoices", "odoo", "success", {"count": len(invoices), "status": status})
        return True

    except Exception as e:
        print(f"✗ Odoo invoice listing failed: {e}", file=sys.stderr)
        audit_log("list_invoices", "odoo", "error", {"error": str(e)})
        return False


def analyze_expenses(top: int = 10):
    """Analyze top expense categories."""
    month = datetime.now().strftime("%Y-%m")
    tx_file = ACCOUNTING_DIR / f"transactions_{month}.json"

    if not tx_file.exists():
        print("✗ No transaction data. Run sync first.")
        return False

    transactions = json.loads(tx_file.read_text())
    expenses = [t for t in transactions if t.get("type") == "expense"]

    # Group by category
    categories = {}
    for exp in expenses:
        cat = exp.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + abs(exp["amount"])

    print(f"Top {top} Expense Categories:")
    print("-" * 40)
    for cat, amount in sorted(categories.items(), key=lambda x: -x[1])[:top]:
        print(f"  ${amount:,.2f} - {cat}")

    total = sum(categories.values())
    print(f"\nTotal Expenses: ${total:,.2f}")
    audit_log("expense_analysis", "local_data", "success", {"total": total, "categories": len(categories)})
    return True


def list_accounts():
    """List accounts from Odoo chart of accounts."""
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        print("Account listing requires Odoo connection (DRY RUN mode active)")
        print("\nSample Accounts:")
        print("400000 - Income")
        print("500000 - Cost of Revenue")
        print("600000 - Expenses")
        return True

    try:
        db, uid, password, models = get_odoo_connection()
        if not uid:
            return False

        accounts = models.execute_kw(
            db, uid, password,
            'account.account', 'search_read',
            [[]],
            {'fields': ['code', 'name', 'account_type', 'balance'],
             'limit': 50, 'order': 'code'}
        )

        print("Chart of Accounts from Odoo:")
        print("-" * 70)
        for acc in accounts:
            balance = acc.get('balance', 0)
            print(f"{acc['code']} - {acc['name']:30s} | ${balance:,.2f} | {acc.get('account_type')}")

        audit_log("list_accounts", "odoo", "success", {"count": len(accounts)})
        return True

    except Exception as e:
        print(f"✗ Odoo account listing failed: {e}", file=sys.stderr)
        audit_log("list_accounts", "odoo", "error", {"error": str(e)})
        return False


def check_status():
    """Check Odoo integration status."""
    has_creds = check_odoo_credentials()
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    month = datetime.now().strftime("%Y-%m")
    tx_file = ACCOUNTING_DIR / f"transactions_{month}.json"
    has_data = tx_file.exists()

    print("Odoo Accounting Status:")
    print(f"  Credentials: {'✓ Configured' if has_creds else '✗ Not configured'}")
    print(f"  Mode: {'DRY RUN (simulated)' if dry_run else 'LIVE (Odoo connection)'}")
    print(f"  Data: {'✓ ' + tx_file.name if has_data else '✗ No data (run sync)'}")

    if has_data:
        tx = json.loads(tx_file.read_text())
        print(f"  Transactions: {len(tx)}")

    # Test connection if credentials present and not dry-run
    if has_creds and not dry_run:
        try:
            db, uid, password, models = get_odoo_connection()
            if uid:
                print(f"  Connection: ✓ Connected to {os.getenv('ODOO_URL')}")
                print(f"  User: {os.getenv('ODOO_USER')}")
            else:
                print(f"  Connection: ✗ Failed (check credentials)")
        except Exception as e:
            print(f"  Connection: ✗ Error - {e}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Odoo Accounting Operations")
    parser.add_argument("--action", required=True,
                       choices=["sync", "summary", "invoices", "expenses", "accounts", "status"])
    parser.add_argument("--period", default="monthly", choices=["daily", "weekly", "monthly", "custom"])
    parser.add_argument("--start", help="Start date (YYYY-MM-DD) for custom period")
    parser.add_argument("--end", help="End date (YYYY-MM-DD) for custom period")
    parser.add_argument("--status", default="all", choices=["all", "paid", "not_paid", "partial", "in_payment"])
    parser.add_argument("--top", type=int, default=10, help="Number of top items to show")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "sync":
        if not sync_transactions():
            sys.exit(1)
    elif args.action == "summary":
        if not generate_summary(args.period, args.start, args.end):
            sys.exit(1)
    elif args.action == "invoices":
        if not list_invoices(args.status):
            sys.exit(1)
    elif args.action == "expenses":
        if not analyze_expenses(args.top):
            sys.exit(1)
    elif args.action == "accounts":
        if not list_accounts():
            sys.exit(1)
    elif args.action == "status":
        check_status()


if __name__ == "__main__":
    main()
