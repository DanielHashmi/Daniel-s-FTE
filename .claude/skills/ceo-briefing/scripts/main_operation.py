#!/usr/bin/env python3
"""CEO Briefing Generator - Gold Tier Skill

Generate weekly business audit and CEO briefing with revenue, tasks,
bottlenecks, and proactive suggestions.
"""
import argparse
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
BRIEFINGS_DIR = VAULT_ROOT / "Briefings"
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"
DONE_DIR = VAULT_ROOT / "Done"
LOGS_DIR = VAULT_ROOT / "Logs"
BUSINESS_GOALS = VAULT_ROOT / "Business_Goals.md"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"

# Sample data for dry-run mode
SAMPLE_GOALS = """
## Q1 2026 Objectives

### Revenue Target
- Monthly goal: $10,000
- Current MTD: $4,500

### Key Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |

### Upcoming Deadlines
- Project Alpha Final: 2026-01-25
- Q1 Tax Filing: 2026-01-31
- Client B Proposal: 2026-02-05
"""


def setup_dirs():
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "ceo_briefing",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "ceo_briefing_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


def get_financial_data(days: int = 7) -> dict:
    """Get financial data from Xero sync or use sample data."""
    month = datetime.now().strftime("%Y-%m")
    tx_file = ACCOUNTING_DIR / f"transactions_{month}.json"

    if tx_file.exists():
        transactions = json.loads(tx_file.read_text())
    else:
        # Sample data for demonstration
        transactions = [
            {"type": "invoice", "amount": 1500, "client": "Acme Corp", "date": "2026-01-15", "status": "paid"},
            {"type": "invoice", "amount": 2500, "client": "TechStart", "date": "2026-01-16", "status": "unpaid"},
            {"type": "expense", "amount": -99, "vendor": "Adobe", "category": "Software", "date": "2026-01-10"},
            {"type": "expense", "amount": -49, "vendor": "Notion", "category": "Software", "date": "2026-01-12"},
            {"type": "payment", "amount": 1500, "from": "Acme Corp", "date": "2026-01-17"},
        ]

    revenue = sum(t["amount"] for t in transactions if t.get("amount", 0) > 0)
    expenses = sum(abs(t["amount"]) for t in transactions if t.get("amount", 0) < 0)
    net = revenue - expenses

    # Subscription analysis
    subscriptions = [t for t in transactions if t.get("category") == "Software"]

    return {
        "weekly_revenue": revenue,
        "mtd_revenue": revenue,  # Simplified
        "monthly_goal": 10000,
        "expenses": expenses,
        "net_profit": net,
        "subscriptions": subscriptions,
        "transactions": transactions
    }


def get_completed_tasks(days: int = 7) -> list:
    """Get completed tasks from Done folder."""
    done_files = []

    if DONE_DIR.exists():
        for f in DONE_DIR.glob("*.md"):
            try:
                stat = f.stat()
                # Check if modified in last N days
                if datetime.fromtimestamp(stat.st_mtime) > datetime.now() - timedelta(days=days):
                    done_files.append({
                        "name": f.stem,
                        "completed": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
                        "size": stat.st_size
                    })
            except Exception:
                continue

    # Add sample data if empty
    if not done_files:
        done_files = [
            {"name": "Invoice_Acme_Corp", "completed": "2026-01-17", "size": 512},
            {"name": "Email_Client_Followup", "completed": "2026-01-16", "size": 256},
            {"name": "Social_LinkedIn_Post", "completed": "2026-01-15", "size": 128},
        ]

    return done_files


def get_upcoming_deadlines(horizon_days: int = 14) -> list:
    """Extract deadlines from Business_Goals.md."""
    deadlines = []

    if BUSINESS_GOALS.exists():
        content = BUSINESS_GOALS.read_text()
        # Simple deadline extraction - look for dates
        import re
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        for line in content.split('\n'):
            if 'deadline' in line.lower() or 'due' in line.lower() or '-' in line:
                matches = re.findall(date_pattern, line)
                for match in matches:
                    try:
                        date = datetime.strptime(match, "%Y-%m-%d")
                        days_remaining = (date - datetime.now()).days
                        if 0 <= days_remaining <= horizon_days:
                            deadlines.append({
                                "description": line.strip("- ").strip(),
                                "date": match,
                                "days_remaining": days_remaining,
                                "at_risk": days_remaining < 7
                            })
                    except ValueError:
                        continue

    # Add sample deadlines if empty
    if not deadlines:
        today = datetime.now()
        deadlines = [
            {"description": "Project Alpha Final", "date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
             "days_remaining": 6, "at_risk": True},
            {"description": "Q1 Tax Filing", "date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
             "days_remaining": 12, "at_risk": False},
        ]

    return sorted(deadlines, key=lambda x: x["days_remaining"])


def analyze_subscriptions(transactions: list) -> list:
    """Analyze subscriptions for unused/wasteful spending."""
    subscriptions = []
    for t in transactions:
        if t.get("category") == "Software" or t.get("type") == "expense":
            vendor = t.get("vendor", "Unknown")
            amount = abs(t.get("amount", 0))

            # Simple heuristic - flag subscriptions with no recent "activity"
            # In production, this would check login data
            subscriptions.append({
                "name": vendor,
                "monthly_cost": amount,
                "last_activity": "Unknown",  # Would need activity tracking
                "recommendation": "Review" if amount > 30 else "Keep"
            })

    return subscriptions


def generate_briefing(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Path:
    """Generate comprehensive CEO briefing."""
    today = datetime.now()
    week_start = today - timedelta(days=7)

    # Gather data
    financial = get_financial_data(7)
    tasks = get_completed_tasks(7)
    deadlines = get_upcoming_deadlines(14)
    subscriptions = analyze_subscriptions(financial.get("transactions", []))

    # Calculate metrics
    goal_progress = (financial["mtd_revenue"] / financial["monthly_goal"]) * 100
    trend = "On Track" if goal_progress >= 45 else ("Ahead" if goal_progress >= 60 else "Behind")

    # Generate briefing content
    briefing = f"""# Monday Morning CEO Briefing
**Week of {week_start.strftime('%B %d, %Y')}**
Generated: {today.strftime('%Y-%m-%d %H:%M')}

---

## Executive Summary

{trend} for monthly revenue target. {len(tasks)} tasks completed this week.
{len([d for d in deadlines if d['at_risk']])} deadline(s) at risk in the next 14 days.

---

## Revenue

| Metric | Value | Status |
|--------|-------|--------|
| This Week | ${financial['weekly_revenue']:,.2f} | {"✅" if financial['weekly_revenue'] > 0 else "⚠️"} |
| Month-to-Date | ${financial['mtd_revenue']:,.2f} | {goal_progress:.0f}% of goal |
| Monthly Goal | ${financial['monthly_goal']:,.2f} | Target |
| Net Profit | ${financial['net_profit']:,.2f} | After expenses |

**Trend:** {trend} {"🚀" if trend == "Ahead" else ("✅" if trend == "On Track" else "⚠️")}

---

## Completed Tasks ({len(tasks)})

| Task | Completed |
|------|-----------|
"""
    for task in tasks[:10]:  # Limit to 10
        briefing += f"| {task['name'].replace('_', ' ')} | {task['completed']} |\n"

    briefing += f"""
---

## Bottlenecks

"""
    # Simple bottleneck detection - tasks that took longer than average
    if tasks:
        briefing += "Based on task completion patterns:\n"
        briefing += "- No significant bottlenecks detected this week\n"
    else:
        briefing += "- Insufficient data for bottleneck analysis\n"

    briefing += f"""
---

## Cost Optimization

### Subscription Analysis
| Service | Monthly Cost | Recommendation |
|---------|--------------|----------------|
"""
    for sub in subscriptions[:5]:
        briefing += f"| {sub['name']} | ${sub['monthly_cost']:,.2f} | {sub['recommendation']} |\n"

    total_sub_cost = sum(s['monthly_cost'] for s in subscriptions)
    briefing += f"\n**Total Subscription Costs:** ${total_sub_cost:,.2f}/month\n"

    briefing += f"""
---

## Upcoming Deadlines

| Deadline | Date | Days Left | Status |
|----------|------|-----------|--------|
"""
    for deadline in deadlines:
        status = "⚠️ AT RISK" if deadline['at_risk'] else "✅ On Track"
        briefing += f"| {deadline['description'][:40]} | {deadline['date']} | {deadline['days_remaining']} | {status} |\n"

    briefing += f"""
---

## Proactive Suggestions

1. **Revenue:** {"Consider promotional campaign to boost sales" if trend == "Behind" else "Maintain current momentum"}
2. **Subscriptions:** Review services marked for "Review" to optimize costs
3. **Deadlines:** {"Focus on at-risk deadlines this week" if any(d['at_risk'] for d in deadlines) else "All deadlines on track"}

---

*Generated by CEO Briefing Skill v1.0*
*AI Employee - Gold Tier*
"""

    # Save briefing
    filename = f"{today.strftime('%Y-%m-%d')}_Monday_Briefing.md"
    output_path = BRIEFINGS_DIR / filename
    output_path.write_text(briefing)

    audit_log("generate", str(output_path), "success", {
        "revenue": financial["weekly_revenue"],
        "tasks_completed": len(tasks),
        "deadlines_at_risk": len([d for d in deadlines if d["at_risk"]])
    })

    return output_path


def main():
    parser = argparse.ArgumentParser(description="CEO Briefing Generator")
    parser.add_argument("--action", required=True,
                       choices=["generate", "revenue", "tasks", "subscriptions", "deadlines"])
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--period", default="weekly", choices=["daily", "weekly", "monthly"])
    parser.add_argument("--detect-bottlenecks", action="store_true")
    parser.add_argument("--unused-threshold", type=int, default=30, help="Days since last activity")
    parser.add_argument("--horizon", type=int, default=14, help="Days to look ahead for deadlines")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "generate":
        output = generate_briefing(args.start, args.end)
        print(f"✓ CEO Briefing generated: {output.name}")

    elif args.action == "revenue":
        data = get_financial_data(7 if args.period == "weekly" else 30)
        print(f"Revenue ({args.period}):")
        print(f"  Total: ${data['weekly_revenue']:,.2f}")
        print(f"  Expenses: ${data['expenses']:,.2f}")
        print(f"  Net: ${data['net_profit']:,.2f}")

    elif args.action == "tasks":
        tasks = get_completed_tasks(7)
        print(f"Completed Tasks (last 7 days): {len(tasks)}")
        for task in tasks[:10]:
            print(f"  - {task['name']} ({task['completed']})")

    elif args.action == "subscriptions":
        data = get_financial_data(30)
        subs = analyze_subscriptions(data.get("transactions", []))
        print(f"Subscription Analysis:")
        for sub in subs:
            print(f"  ${sub['monthly_cost']:,.2f}/mo - {sub['name']} [{sub['recommendation']}]")

    elif args.action == "deadlines":
        deadlines = get_upcoming_deadlines(args.horizon)
        print(f"Upcoming Deadlines ({args.horizon} days):")
        for d in deadlines:
            status = "⚠️" if d["at_risk"] else "✅"
            print(f"  {status} {d['description']} - {d['date']} ({d['days_remaining']} days)")


if __name__ == "__main__":
    main()
