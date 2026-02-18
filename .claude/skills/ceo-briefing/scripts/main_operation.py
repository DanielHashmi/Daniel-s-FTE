#!/usr/bin/env python3
"""CEO Briefing Generator (Gold Tier Skill)

Generates the weekly business + accounting audit and writes a CEO briefing into the vault.

Hackathon expectation:
- Reads Business_Goals.md, Done/, and bank/accounting transactions
- Writes a "Monday Morning CEO Briefing" markdown file with YAML frontmatter
- Logs every run to /Logs/YYYY-MM-DD.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.lib.logging import get_logger
from src.lib.vault import vault

logger = get_logger("ceo_briefing_skill")

# Weekly audit logic (hackathon doc style): match merchants/descriptions to subscription names.
SUBSCRIPTION_PATTERNS: Dict[str, str] = {
    "netflix.com": "Netflix",
    "spotify.com": "Spotify",
    "adobe.com": "Adobe Creative Cloud",
    "notion.so": "Notion",
    "slack.com": "Slack",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_date_yyyy_mm_dd(value: str) -> Optional[date]:
    if not value:
        return None
    txt = str(value).strip()
    if not txt:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(txt, fmt).date()
        except ValueError:
            continue
    return None


def _load_transactions() -> List[Dict[str, Any]]:
    """Load transactions from the vault (banking watcher and/or accounting sync)."""

    candidates = []

    banking_path = vault.root / "Banking" / "transactions.json"
    if banking_path.exists():
        candidates.append(banking_path)

    # Accounting sync path: Accounting/transactions/<YYYY-MM>/transactions.json
    month_dir = vault.dirs["accounting"] / "transactions" / datetime.now().strftime("%Y-%m")
    month_path = month_dir / "transactions.json"
    if month_path.exists():
        candidates.append(month_path)

    # Legacy file name used by earlier versions
    legacy_path = vault.dirs["accounting"] / f"transactions_{datetime.now().strftime('%Y-%m')}.json"
    if legacy_path.exists():
        candidates.append(legacy_path)

    for p in candidates:
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return raw
            if isinstance(raw, dict) and isinstance(raw.get("transactions"), list):
                return raw["transactions"]
        except Exception:
            continue

    return []


def _weekly_period(today: date) -> Tuple[date, date]:
    # Default period is the last 7 days ending yesterday (matches Sunday-night -> Monday briefing).
    end = today - timedelta(days=1)
    start = end - timedelta(days=6)
    return start, end


def _next_monday(today: date) -> date:
    if today.weekday() == 0:
        return today
    delta = (7 - today.weekday()) % 7
    return today + timedelta(days=delta)


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _extract_monthly_goal_from_business_goals(path: Path) -> Optional[float]:
    if not path.exists():
        return None
    txt = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Monthly goal:\s*\$?([0-9][0-9,]*(?:\.[0-9]{1,2})?)", txt, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _completed_tasks(days: int = 7) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    done_dir = vault.dirs["done"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for p in sorted(done_dir.glob("*"), key=lambda x: x.name):
        if not p.is_file():
            continue
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            out.append({
                "name": p.name,
                "completed": mtime.date().isoformat(),
            })
        except Exception:
            continue

    return out


def _upcoming_deadlines(horizon_days: int = 14) -> List[Dict[str, Any]]:
    goals_path = vault.root / "Business_Goals.md"
    if not goals_path.exists():
        return []

    today = datetime.now(timezone.utc).date()
    content = goals_path.read_text(encoding="utf-8", errors="replace")
    results: List[Dict[str, Any]] = []

    # Simple: any YYYY-MM-DD in a line counts as a deadline candidate.
    for line in content.splitlines():
        m = re.search(r"(\d{4}-\d{2}-\d{2})", line)
        if not m:
            continue
        d = _parse_date_yyyy_mm_dd(m.group(1))
        if not d:
            continue
        days_remaining = (d - today).days
        if 0 <= days_remaining <= horizon_days:
            results.append({
                "description": line.strip().lstrip("- ").strip(),
                "date": d.isoformat(),
                "days_remaining": days_remaining,
                "at_risk": days_remaining < 7,
            })

    results.sort(key=lambda x: x["days_remaining"])
    return results


def _analyze_subscriptions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    subs: List[Dict[str, Any]] = []
    for t in transactions:
        desc = str(t.get("description") or "").lower()
        amt_raw = t.get("amount")
        try:
            amt = float(amt_raw)
        except Exception:
            continue

        match = None
        for pattern, name in SUBSCRIPTION_PATTERNS.items():
            if pattern in desc:
                match = name
                break
        if not match:
            continue

        dt = _parse_date_yyyy_mm_dd(str(t.get("date") or ""))
        subs.append({
            "name": match,
            "amount": abs(amt),
            "date": dt.isoformat() if dt else "",
            "description": str(t.get("description") or "")[:120],
        })

    return subs


def generate_briefing(horizon_days: int = 14) -> Path:
    vault.ensure_structure()

    today = datetime.now(timezone.utc).date()
    period_start, period_end = _weekly_period(today)
    briefing_date = _next_monday(today)

    transactions = _load_transactions()

    # Filter by period
    weekly_txs: List[Dict[str, Any]] = []
    mtd_txs: List[Dict[str, Any]] = []

    for t in transactions:
        dt = _parse_date_yyyy_mm_dd(str(t.get("date") or ""))
        if not dt:
            continue
        amt_raw = t.get("amount")
        try:
            amt = float(amt_raw)
        except Exception:
            continue

        if period_start <= dt <= period_end:
            weekly_txs.append({**t, "_dt": dt, "_amt": amt})

        if dt.year == today.year and dt.month == today.month:
            mtd_txs.append({**t, "_dt": dt, "_amt": amt})

    weekly_revenue = sum(t["_amt"] for t in weekly_txs if t["_amt"] > 0)
    weekly_expenses = sum(abs(t["_amt"]) for t in weekly_txs if t["_amt"] < 0)
    mtd_revenue = sum(t["_amt"] for t in mtd_txs if t["_amt"] > 0)

    goals_path = vault.root / "Business_Goals.md"
    monthly_goal = _extract_monthly_goal_from_business_goals(goals_path) or 0.0

    completed = _completed_tasks(days=7)
    deadlines = _upcoming_deadlines(horizon_days=horizon_days)
    subscriptions = _analyze_subscriptions(weekly_txs)

    goal_progress = 0.0
    if monthly_goal > 0:
        goal_progress = (mtd_revenue / monthly_goal) * 100

    trend = "On track" if goal_progress >= 45 else "Behind"

    frontmatter = (
        "---\n"
        f"generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"period: {period_start.isoformat()} to {period_end.isoformat()}\n"
        "schema: ceo_briefing_v1\n"
        "---\n\n"
    )

    lines: List[str] = []
    lines.append(frontmatter.rstrip("\n"))
    lines.append("# Monday Morning CEO Briefing")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"{trend} on monthly revenue target. {len(completed)} items moved to Done in the last 7 days.")
    lines.append("")

    lines.append("## Revenue")
    lines.append(f"- **This Week**: {_money(weekly_revenue)}")
    lines.append(f"- **MTD**: {_money(mtd_revenue)}" + (f" ({goal_progress:.0f}% of {_money(monthly_goal)} goal)" if monthly_goal > 0 else ""))
    lines.append(f"- **Expenses (This Week)**: {_money(weekly_expenses)}")
    lines.append("")

    lines.append(f"## Completed Tasks ({len(completed)})")
    if completed:
        for item in completed[:20]:
            lines.append(f"- [x] {item['name']} ({item['completed']})")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Bottlenecks")
    lines.append("Insufficient timing data to compute bottlenecks reliably. (Add created/completed timestamps per task to enable.)")
    lines.append("")

    lines.append("## Proactive Suggestions")
    lines.append("### Cost Optimization")
    if subscriptions:
        for s in subscriptions[:10]:
            lines.append(f"- {s['name']}: {_money(float(s['amount']))} ({s.get('date','')})")
        lines.append("- [ACTION] Review subscriptions above for usefulness. If cancellation is desired, create a Pending_Approval item.")
    else:
        lines.append("- No subscription-like transactions detected in this period.")
    lines.append("")

    lines.append("### Upcoming Deadlines")
    if deadlines:
        for d in deadlines:
            flag = "AT RISK" if d["at_risk"] else "On track"
            lines.append(f"- {d['date']} ({d['days_remaining']} days): {d['description']} [{flag}]")
    else:
        lines.append("- No upcoming deadlines found in Business_Goals.md")
    lines.append("")

    lines.append("---")
    lines.append("*Generated by AI Employee v0.1*")

    filename = f"{briefing_date.isoformat()}_Monday_Briefing.md"
    out_path = vault.dirs["briefings"] / filename
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    logger.log_action(
        action_type="ceo_briefing_generate",
        result="success",
        target=str(out_path),
        parameters={
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "weekly_revenue": weekly_revenue,
            "mtd_revenue": mtd_revenue,
        },
        approval_status="not_required",
    )

    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Monday Morning CEO Briefing")
    parser.add_argument("--action", required=True, choices=["generate"])
    parser.add_argument("--horizon", type=int, default=14, help="Days to look ahead for deadlines")

    args = parser.parse_args()
    if args.action == "generate":
        path = generate_briefing(horizon_days=args.horizon)
        print(f"Generated: {path}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
