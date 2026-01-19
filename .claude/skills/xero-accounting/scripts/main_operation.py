#!/usr/bin/env python3
"""Xero Accounting Operations - Gold Tier Skill

Syncs transactions, invoices, and financial data from Xero.
Generates financial summaries and reports for CEO Briefing.
"""
import argparse
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"
LOGS_DIR = VAULT_ROOT / "Logs"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"

# Simulated transaction data for dry-run mode
SAMPLE_TRANSACTIONS = [
    {"id": "INV-001", "type": "invoice", "amount": 1500.00, "client": "Acme Corp", "date": "2026-01-15", "status": "paid"},
    {"id": "INV-002", "type": "invoice", "amount": 2500.00, "client": "TechStart Inc", "date": "2026-01-16", "status": "unpaid"},
    {"id": "EXP-001", "type": "expense", "amount": -99.00, "vendor": "Adobe", "category": "Software", "date": "2026-01-10"},
    {"id": "EXP-002", "type": "expense", "amount": -49.00, "vendor": "Notion", "category": "Software", "date": "2026-01-12"},
    {"id": "PAY-001", "type": "payment", "amount": 1500.00, "from": "Acme Corp", "date": "2026-01-17", "invoice": "INV-001"},
]


def setup_dirs():
    ACCOUNTING_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "xero_accounting",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "xero_accounting_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


def check_xero_credentials() -> bool:
    """Check if Xero credentials are configured."""
    required = ["XERO_CLIENT_ID", "XERO_CLIENT_SECRET", "XERO_TENANT_ID"]
    return all(os.getenv(var) for var in required)


def sync_transactions():
    """Sync transactions from Xero (or simulate in dry-run mode)."""
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if not check_xero_credentials() or dry_run:
        # Use sample data in dry-run mode
        month = datetime.now().strftime("%Y-%m")
        output_file = ACCOUNTING_DIR / f"transactions_{month}.json"

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

    # Real Xero API integration would go here
    print("✗ Real Xero sync requires xero-python library. Enable DRY_RUN=true for simulation.")
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
    unpaid = [t for t in transactions if t.get("type") == "invoice" and t.get("status") == "unpaid"]
    unpaid_total = sum(t["amount"] for t in unpaid)

    # Generate summary markdown
    summary_date = datetime.now().strftime("%Y-%m-%d")
    summary = f"""# Financial Summary - {period.capitalize()}
Generated: {summary_date}

## Overview
| Metric | Amount |
|--------|--------|
| Total Revenue | ${revenue:,.2f} |
| Total Expenses | ${expenses:,.2f} |
| Net Profit | ${net_profit:,.2f} |
| Unpaid Invoices | ${unpaid_total:,.2f} |

## Expense Breakdown
| Category | Amount |
|----------|--------|
"""
    for cat, amount in sorted(expense_categories.items(), key=lambda x: -x[1]):
        summary += f"| {cat} | ${amount:,.2f} |\n"

    if unpaid:
        summary += "\n## Unpaid Invoices\n"
        for inv in unpaid:
            summary += f"- {inv['id']}: ${inv['amount']:,.2f} from {inv.get('client', 'Unknown')}\n"

    summary += f"\n---\n*Generated by xero-accounting skill*\n"

    output_file = ACCOUNTING_DIR / f"summary_{summary_date}.md"
    output_file.write_text(summary)

    print(f"✓ Financial summary generated")
    print(f"  Revenue: ${revenue:,.2f} | Expenses: ${expenses:,.2f} | Net: ${net_profit:,.2f}")
    audit_log("summary", str(output_file), "success", {"revenue": revenue, "expenses": expenses, "net": net_profit})
    return True


def list_invoices(status: str = "all"):
    """List invoices filtered by status."""
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
    return True


def check_status():
    """Check Xero integration status."""
    has_creds = check_xero_credentials()
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    month = datetime.now().strftime("%Y-%m")
    tx_file = ACCOUNTING_DIR / f"transactions_{month}.json"
    has_data = tx_file.exists()

    print("Xero Accounting Status:")
    print(f"  Credentials: {'✓ Configured' if has_creds else '✗ Not configured'}")
    print(f"  Mode: {'DRY RUN (simulated)' if dry_run else 'LIVE'}")
    print(f"  Data: {'✓ ' + tx_file.name if has_data else '✗ No data (run sync)'}")

    if has_data:
        tx = json.loads(tx_file.read_text())
        print(f"  Transactions: {len(tx)}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Xero Accounting Operations")
    parser.add_argument("--action", required=True,
                       choices=["sync", "summary", "invoices", "expenses", "status"])
    parser.add_argument("--period", default="monthly", choices=["daily", "weekly", "monthly", "custom"])
    parser.add_argument("--start", help="Start date (YYYY-MM-DD) for custom period")
    parser.add_argument("--end", help="End date (YYYY-MM-DD) for custom period")
    parser.add_argument("--status", default="all", choices=["all", "paid", "unpaid", "overdue"])
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
    elif args.action == "status":
        check_status()


if __name__ == "__main__":
    main()
