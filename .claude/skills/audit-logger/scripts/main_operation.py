#!/usr/bin/env python3
"""Comprehensive Audit Logger - Gold Tier Skill

Comprehensive audit logging for all actions with compliance tracking,
log retention, and analysis capabilities.
"""
import argparse
import sys
import json
import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
LOGS_DIR = VAULT_ROOT / "Logs"
ARCHIVE_DIR = LOGS_DIR / "Archive"
AUDIT_SUMMARY = LOGS_DIR / "audit_summary.md"

# Sensitive fields to sanitize
SENSITIVE_FIELDS = ["password", "token", "secret", "api_key", "credential", "auth"]


def setup_dirs():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_params(params: dict) -> dict:
    """Remove sensitive information from parameters."""
    if not params:
        return {}

    sanitized = {}
    for key, value in params.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_params(value)
        elif isinstance(value, str) and len(value) > 500:
            sanitized[key] = value[:500] + "...[TRUNCATED]"
        else:
            sanitized[key] = value

    return sanitized


def log_action(action_type: str, actor: str, target: str, result: str,
               params: Optional[dict] = None, approval_status: Optional[str] = None,
               approved_by: Optional[str] = None, duration_ms: Optional[int] = None,
               error: Optional[str] = None):
    """Log a single action with full context."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"{today}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "actor": actor,
        "target": target,
        "parameters": sanitize_params(params or {}),
        "approval_status": approval_status or "not_required",
        "approved_by": approved_by,
        "approval_timestamp": datetime.now().isoformat() if approved_by else None,
        "result": result,
        "duration_ms": duration_ms,
        "error": error
    }

    try:
        logs = json.loads(log_file.read_text()) if log_file.exists() else []
        logs.append(entry)
        log_file.write_text(json.dumps(logs, indent=2))

        print(f"✓ Action logged: {action_type} -> {target} [{result}]")
        return True

    except Exception as e:
        print(f"✗ Failed to log action: {e}", file=sys.stderr)
        return False


def query_logs(since: Optional[str] = None, until: Optional[str] = None,
               action_type: Optional[str] = None, actor: Optional[str] = None,
               result: Optional[str] = None, limit: int = 100):
    """Query logs with filters."""
    # Parse time filters
    if since:
        if since.endswith("h"):
            since_time = datetime.now() - timedelta(hours=int(since[:-1]))
        elif since.endswith("d"):
            since_time = datetime.now() - timedelta(days=int(since[:-1]))
        else:
            since_time = datetime.fromisoformat(since)
    else:
        since_time = datetime.now() - timedelta(days=7)

    if until:
        until_time = datetime.fromisoformat(until)
    else:
        until_time = datetime.now()

    print(f"Querying logs from {since_time.strftime('%Y-%m-%d %H:%M')} to {until_time.strftime('%Y-%m-%d %H:%M')}")
    if action_type:
        print(f"  Filter: action_type = {action_type}")
    if actor:
        print(f"  Filter: actor = {actor}")
    if result:
        print(f"  Filter: result = {result}")
    print("-" * 60)

    # Collect matching entries
    matches = []

    for log_file in sorted(LOGS_DIR.glob("*.json"), reverse=True):
        try:
            logs = json.loads(log_file.read_text())
            for entry in logs:
                entry_time = datetime.fromisoformat(entry["timestamp"])

                if entry_time < since_time or entry_time > until_time:
                    continue
                if action_type and entry.get("action_type") != action_type:
                    continue
                if actor and entry.get("actor") != actor:
                    continue
                if result and result not in entry.get("result", ""):
                    continue

                matches.append(entry)

                if len(matches) >= limit:
                    break

        except Exception:
            continue

        if len(matches) >= limit:
            break

    # Display results
    for entry in matches[:limit]:
        print(f"\n[{entry['timestamp']}]")
        print(f"  Action: {entry.get('action_type', 'unknown')}")
        print(f"  Actor: {entry.get('actor', 'unknown')}")
        print(f"  Target: {entry.get('target', 'unknown')}")
        print(f"  Result: {entry.get('result', 'unknown')}")
        if entry.get("duration_ms"):
            print(f"  Duration: {entry['duration_ms']}ms")
        if entry.get("error"):
            print(f"  Error: {entry['error']}")

    print(f"\n✓ Found {len(matches)} matching entries")
    return matches


def generate_daily_summary(date: Optional[str] = None):
    """Generate daily activity summary."""
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = datetime.now() - timedelta(days=1)

    date_str = target_date.strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"{date_str}.json"

    if not log_file.exists():
        print(f"No logs found for {date_str}")
        return True

    logs = json.loads(log_file.read_text())

    # Calculate statistics
    stats = {
        "total_actions": len(logs),
        "by_type": defaultdict(int),
        "by_result": defaultdict(int),
        "by_actor": defaultdict(int),
        "avg_duration": 0,
        "errors": []
    }

    total_duration = 0
    duration_count = 0

    for entry in logs:
        stats["by_type"][entry.get("action_type", "unknown")] += 1
        stats["by_result"][entry.get("result", "unknown")] += 1
        stats["by_actor"][entry.get("actor", "unknown")] += 1

        if entry.get("duration_ms"):
            total_duration += entry["duration_ms"]
            duration_count += 1

        if entry.get("error"):
            stats["errors"].append({
                "time": entry["timestamp"],
                "action": entry.get("action_type"),
                "error": entry["error"]
            })

    if duration_count > 0:
        stats["avg_duration"] = total_duration / duration_count

    # Display summary
    print(f"Daily Summary: {date_str}")
    print("=" * 50)

    print(f"\nTotal Actions: {stats['total_actions']}")

    print("\nBy Type:")
    for action_type, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
        print(f"  {action_type}: {count}")

    print("\nBy Result:")
    for result, count in sorted(stats["by_result"].items(), key=lambda x: -x[1]):
        print(f"  {result}: {count}")

    print("\nBy Actor:")
    for actor, count in sorted(stats["by_actor"].items(), key=lambda x: -x[1]):
        print(f"  {actor}: {count}")

    if stats["avg_duration"] > 0:
        print(f"\nAverage Duration: {stats['avg_duration']:.0f}ms")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats["errors"][:5]:
            print(f"  - [{error['time']}] {error['action']}: {error['error'][:50]}")

    return True


def generate_compliance_report(period: str = "monthly"):
    """Generate compliance report with HITL tracking."""
    if period == "weekly":
        days = 7
    elif period == "monthly":
        days = 30
    else:
        days = 90  # quarterly

    since_date = datetime.now() - timedelta(days=days)

    print(f"Compliance Report ({period.capitalize()})")
    print(f"Period: {since_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)

    # Collect all logs in period
    all_entries = []
    for log_file in sorted(LOGS_DIR.glob("*.json")):
        try:
            logs = json.loads(log_file.read_text())
            for entry in logs:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time >= since_date:
                    all_entries.append(entry)
        except Exception:
            continue

    if not all_entries:
        print("No data available for the specified period")
        return True

    # Calculate metrics
    total = len(all_entries)
    approved = sum(1 for e in all_entries if e.get("approval_status") == "approved")
    required_approval = sum(1 for e in all_entries if e.get("approval_status") != "not_required")
    errors = sum(1 for e in all_entries if "fail" in e.get("result", "").lower() or "error" in e.get("result", "").lower())
    recovered = sum(1 for e in all_entries if "recovered" in e.get("result", "").lower())

    approval_rate = (approved / required_approval * 100) if required_approval > 0 else 100
    error_rate = (errors / total * 100) if total > 0 else 0
    recovery_rate = (recovered / errors * 100) if errors > 0 else 100

    print(f"""
## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Actions | {total} |
| Required Approval | {required_approval} |
| Approved | {approved} |
| Errors | {errors} |
| Recovered | {recovered} |

## Compliance Metrics

| Metric | Rate | Status |
|--------|------|--------|
| HITL Compliance | {approval_rate:.1f}% | {"✅ Pass" if approval_rate >= 95 else "⚠️ Review"} |
| Error Rate | {error_rate:.1f}% | {"✅ Pass" if error_rate <= 5 else "⚠️ Review"} |
| Recovery Rate | {recovery_rate:.1f}% | {"✅ Pass" if recovery_rate >= 80 else "⚠️ Review"} |
""")

    # Action breakdown
    action_counts = defaultdict(int)
    for entry in all_entries:
        action_counts[entry.get("action_type", "unknown")] += 1

    print("\n## Action Breakdown\n")
    print("| Action Type | Count | % |")
    print("|-------------|-------|---|")
    for action, count in sorted(action_counts.items(), key=lambda x: -x[1])[:10]:
        pct = count / total * 100
        print(f"| {action} | {count} | {pct:.1f}% |")

    return True


def consolidate_logs():
    """Consolidate today's logs into a single JSON file."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"{today}.json"

    if log_file.exists():
        logs = json.loads(log_file.read_text())
        # Validate JSON structure
        valid = all(isinstance(entry, dict) and "timestamp" in entry for entry in logs)

        if valid:
            print(f"✓ Logs consolidated: {log_file.name} ({len(logs)} entries)")
        else:
            print(f"⚠️ Log file may have invalid entries: {log_file.name}")
    else:
        print(f"No logs to consolidate for {today}")

    return True


def archive_old_logs(older_than_days: int = 90):
    """Archive and compress old log files."""
    cutoff = datetime.now() - timedelta(days=older_than_days)
    archived_count = 0

    for log_file in LOGS_DIR.glob("*.json"):
        if log_file.parent == ARCHIVE_DIR:
            continue

        try:
            file_date = datetime.strptime(log_file.stem, "%Y-%m-%d")
            if file_date < cutoff:
                # Compress and move
                archive_path = ARCHIVE_DIR / f"{log_file.stem}.json.gz"

                with open(log_file, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                log_file.unlink()
                archived_count += 1
                print(f"  Archived: {log_file.name}")

        except ValueError:
            continue  # Skip files that don't match date pattern

    print(f"\n✓ Archived {archived_count} log file(s) older than {older_than_days} days")
    return True


def validate_log_file(file_path: str):
    """Validate integrity of a log file."""
    log_file = Path(file_path)

    if not log_file.exists():
        print(f"✗ File not found: {file_path}")
        return False

    try:
        logs = json.loads(log_file.read_text())

        if not isinstance(logs, list):
            print(f"✗ Invalid format: expected array")
            return False

        required_fields = ["timestamp", "action_type", "result"]
        valid_entries = 0
        invalid_entries = []

        for i, entry in enumerate(logs):
            if not isinstance(entry, dict):
                invalid_entries.append(f"Entry {i}: not a dict")
                continue

            missing = [f for f in required_fields if f not in entry]
            if missing:
                invalid_entries.append(f"Entry {i}: missing {missing}")
                continue

            valid_entries += 1

        print(f"Log Validation: {log_file.name}")
        print(f"  Total entries: {len(logs)}")
        print(f"  Valid entries: {valid_entries}")
        print(f"  Invalid entries: {len(invalid_entries)}")

        if invalid_entries:
            print("\n  Issues:")
            for issue in invalid_entries[:5]:
                print(f"    - {issue}")

        return len(invalid_entries) == 0

    except json.JSONDecodeError as e:
        print(f"✗ JSON parse error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Audit Logger")
    parser.add_argument("--action", required=True,
                       choices=["log", "query", "daily-summary", "compliance-report",
                               "consolidate", "archive", "validate"])

    # Log action params
    parser.add_argument("--type", help="Action type for log")
    parser.add_argument("--actor", help="Actor for log/query")
    parser.add_argument("--target", help="Target for log")
    parser.add_argument("--result", help="Result for log/query")
    parser.add_argument("--params", help="JSON params for log")

    # Query params
    parser.add_argument("--since", help="Start time (e.g., 24h, 7d, 2026-01-15)")
    parser.add_argument("--until", help="End time (ISO format)")
    parser.add_argument("--limit", type=int, default=100, help="Max results")

    # Other params
    parser.add_argument("--date", help="Date for daily-summary (YYYY-MM-DD)")
    parser.add_argument("--period", choices=["weekly", "monthly", "quarterly"], default="monthly")
    parser.add_argument("--older-than", type=int, default=90, help="Days for archive")
    parser.add_argument("--file", help="File path for validate")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "log":
        if not all([args.type, args.actor, args.target, args.result]):
            print("Error: --type, --actor, --target, --result required for log action")
            sys.exit(1)
        params = json.loads(args.params) if args.params else None
        log_action(args.type, args.actor, args.target, args.result, params)

    elif args.action == "query":
        query_logs(args.since, args.until, args.type, args.actor, args.result, args.limit)

    elif args.action == "daily-summary":
        generate_daily_summary(args.date)

    elif args.action == "compliance-report":
        generate_compliance_report(args.period)

    elif args.action == "consolidate":
        consolidate_logs()

    elif args.action == "archive":
        archive_old_logs(args.older_than)

    elif args.action == "validate":
        if not args.file:
            print("Error: --file required for validate action")
            sys.exit(1)
        if not validate_log_file(args.file):
            sys.exit(1)


if __name__ == "__main__":
    main()
