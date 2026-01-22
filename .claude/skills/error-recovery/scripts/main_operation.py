#!/usr/bin/env python3
"""Error Recovery & Graceful Degradation - Gold Tier Skill

Handle errors gracefully with retry logic, automatic recovery,
and graceful degradation for autonomous operation.
"""
import argparse
import sys
import json
import os
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from functools import wraps
import random

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
RECOVERY_QUEUE = VAULT_ROOT / "Recovery_Queue"
QUARANTINE = VAULT_ROOT / "Quarantine"
ALERTS = VAULT_ROOT / "Alerts"
LOGS_DIR = VAULT_ROOT / "Logs"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"

# Retry configuration
DEFAULT_RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1,      # seconds
    "max_delay": 60,      # seconds
    "backoff": "exponential",  # or "linear"
    "jitter": True
}

# Error categories and recovery strategies
ERROR_STRATEGIES = {
    "transient": {
        "description": "Network timeout, rate limit",
        "strategy": "retry_with_backoff",
        "max_retries": 3
    },
    "authentication": {
        "description": "Expired token, revoked access",
        "strategy": "refresh_token_or_alert",
        "max_retries": 1
    },
    "logic": {
        "description": "Misinterpreted data",
        "strategy": "human_review",
        "max_retries": 0
    },
    "data": {
        "description": "Corrupted file, missing field",
        "strategy": "quarantine_and_alert",
        "max_retries": 0
    },
    "system": {
        "description": "Process crash, disk full",
        "strategy": "watchdog_restart",
        "max_retries": 3
    }
}


def setup_dirs():
    RECOVERY_QUEUE.mkdir(parents=True, exist_ok=True)
    QUARANTINE.mkdir(parents=True, exist_ok=True)
    ALERTS.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "error_recovery",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "error_recovery_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


def calculate_delay(attempt: int, config: dict = None) -> float:
    """Calculate retry delay with optional jitter."""
    config = config or DEFAULT_RETRY_CONFIG

    if config["backoff"] == "exponential":
        delay = config["base_delay"] * (2 ** attempt)
    else:  # linear
        delay = config["base_delay"] * (attempt + 1)

    delay = min(delay, config["max_delay"])

    if config["jitter"]:
        # Add up to 25% jitter
        jitter = delay * 0.25 * random.random()
        delay += jitter

    return delay


def retry_operation(operation_id: str, max_attempts: int = 3, backoff: str = "exponential"):
    """Retry a failed operation from the recovery queue."""
    queue_file = RECOVERY_QUEUE / f"{operation_id}.json"

    if not queue_file.exists():
        print(f"✗ Operation not found: {operation_id}")
        return False

    operation = json.loads(queue_file.read_text())

    config = {
        **DEFAULT_RETRY_CONFIG,
        "max_attempts": max_attempts,
        "backoff": backoff
    }

    print(f"Retrying operation: {operation_id}")
    print(f"  Original action: {operation.get('action', 'unknown')}")
    print(f"  Max attempts: {max_attempts}")

    success = False
    for attempt in range(max_attempts):
        print(f"\n  Attempt {attempt + 1}/{max_attempts}...")

        # Simulate retry (in production, would re-execute the operation)
        dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        if dry_run:
            # Simulate success on 3rd attempt for demo
            if attempt >= 2:
                success = True
                print("    [DRY RUN] Operation succeeded")
                break
            else:
                delay = calculate_delay(attempt, config)
                print(f"    [DRY RUN] Operation failed, waiting {delay:.1f}s...")
                time.sleep(min(delay, 2))  # Cap delay for demo

    if success:
        # Remove from queue
        queue_file.unlink()
        print(f"\n✓ Operation {operation_id} completed successfully")
        audit_log("retry", operation_id, "success", {"attempts": attempt + 1})
    else:
        # Update retry count
        operation["retry_count"] = operation.get("retry_count", 0) + max_attempts
        operation["last_retry"] = datetime.now().isoformat()
        queue_file.write_text(json.dumps(operation, indent=2))
        print(f"\n✗ Operation {operation_id} failed after {max_attempts} attempts")
        audit_log("retry", operation_id, "failed", {"attempts": max_attempts})

    return success


def refresh_token(service: str):
    """Refresh authentication token for a service."""
    token_services = {
        "gmail": {"token_file": "~/.gmail_token.json", "refresh_method": "oauth"},
        "odoo": {"token_file": "~/.odoo_config.json", "refresh_method": "api_key"},
        "linkedin": {"token_file": "~/.linkedin_token.json", "refresh_method": "oauth"},
        "facebook": {"token_file": "~/.meta_token.json", "refresh_method": "long_lived"},
        "instagram": {"token_file": "~/.meta_token.json", "refresh_method": "long_lived"},
        "twitter": {"token_file": "~/.twitter_tokens.json", "refresh_method": "oauth2"}
    }Replacement with Odoo configuration and API key method - earliest complete match in the file.

    if service not in token_services:
        print(f"✗ Unknown service: {service}")
        return False

    config = token_services[service]
    token_path = Path(os.path.expanduser(config["token_file"]))

    print(f"Refreshing {service} token...")
    print(f"  Token file: {token_path}")
    print(f"  Refresh method: {config['refresh_method']}")

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        print(f"  [DRY RUN] Would refresh {service} token")
        audit_log("refresh_token", service, "success (dry_run)")
        print(f"\n✓ Token refresh simulated for {service}")
        return True

    # Real token refresh would go here
    print(f"✗ Real token refresh not implemented. Configure credentials.")
    return False


def quarantine_file(file_path: str, reason: str):
    """Move corrupted file to quarantine with metadata."""
    source = Path(file_path)

    if not source.exists():
        print(f"✗ File not found: {file_path}")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine_name = f"{timestamp}_{source.name}"
    dest = QUARANTINE / quarantine_name

    # Create metadata
    metadata = {
        "original_path": str(source.absolute()),
        "quarantined_at": datetime.now().isoformat(),
        "reason": reason,
        "file_size": source.stat().st_size
    }

    # Move file
    shutil.move(str(source), str(dest))

    # Write metadata
    metadata_file = QUARANTINE / f"{quarantine_name}.meta.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))

    print(f"✓ File quarantined: {quarantine_name}")
    print(f"  Reason: {reason}")
    audit_log("quarantine", str(source), "success", metadata)

    # Create human review alert
    create_alert("quarantine", f"File quarantined: {source.name}", metadata)

    return True


def create_alert(alert_type: str, message: str, details: dict = None):
    """Create alert for human review."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    alert_id = f"ALERT_{alert_type.upper()}_{timestamp}"

    alert_content = f"""---
id: {alert_id}
type: alert
category: {alert_type}
created: {datetime.now().isoformat()}
priority: high
status: pending
---

# Alert: {message}

## Details
{json.dumps(details or {}, indent=2)}

## Action Required
Please review this alert and take appropriate action.

---
*Generated by Error Recovery Skill*
"""

    alert_file = ALERTS / f"{alert_id}.md"
    alert_file.write_text(alert_content)

    return alert_file


def check_health():
    """Check health of all system components."""
    print("System Health Check")
    print("=" * 50)

    components = {
        "Gmail API": lambda: os.getenv("GMAIL_CLIENT_ID") is not None,
        "Xero API": lambda: os.getenv("XERO_CLIENT_ID") is not None,
        "LinkedIn": lambda: os.getenv("LINKEDIN_ACCESS_TOKEN") is not None,
        "Meta (FB/IG)": lambda: os.getenv("META_ACCESS_TOKEN") is not None,
        "Twitter": lambda: os.getenv("TWITTER_API_KEY") is not None,
        "Recovery Queue": lambda: RECOVERY_QUEUE.exists(),
        "Quarantine": lambda: QUARANTINE.exists(),
        "Logs": lambda: LOGS_DIR.exists()
    }

    all_healthy = True
    for name, check in components.items():
        try:
            healthy = check()
            status = "✓ Healthy" if healthy else "✗ Unconfigured"
            if not healthy:
                all_healthy = False
        except Exception as e:
            status = f"✗ Error: {e}"
            all_healthy = False

        print(f"  {name:20} {status}")

    # Check recovery queue
    queue_files = list(RECOVERY_QUEUE.glob("*.json"))
    print(f"\n  Recovery Queue: {len(queue_files)} pending")

    # Check quarantine
    quarantine_files = list(QUARANTINE.glob("*"))
    quarantine_count = len([f for f in quarantine_files if not f.name.endswith(".meta.json")])
    print(f"  Quarantine: {quarantine_count} files")

    # Check alerts
    alert_files = list(ALERTS.glob("*.md"))
    print(f"  Pending Alerts: {len(alert_files)}")

    print(f"\n{'✓ System healthy' if all_healthy else '⚠️ Some components need attention'}")
    return all_healthy


def process_recovery_queue():
    """Process all operations in the recovery queue."""
    queue_files = list(RECOVERY_QUEUE.glob("*.json"))

    if not queue_files:
        print("✓ Recovery queue is empty")
        return True

    print(f"Processing recovery queue ({len(queue_files)} operations)...")

    success_count = 0
    for queue_file in queue_files:
        operation_id = queue_file.stem
        if retry_operation(operation_id):
            success_count += 1

    print(f"\n✓ Processed {success_count}/{len(queue_files)} operations successfully")
    return success_count == len(queue_files)


def run_watchdog():
    """Run watchdog check for critical processes."""
    print("Watchdog Check")
    print("-" * 40)

    # In production, this would check PM2/supervisord processes
    processes = {
        "orchestrator": {"expected": True, "pid_file": "/tmp/orchestrator.pid"},
        "gmail_watcher": {"expected": True, "pid_file": "/tmp/gmail_watcher.pid"},
        "whatsapp_watcher": {"expected": True, "pid_file": "/tmp/whatsapp_watcher.pid"}
    }

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    for name, config in processes.items():
        pid_file = Path(config["pid_file"])

        if dry_run:
            print(f"  [DRY RUN] {name}: Would check PID at {pid_file}")
        else:
            if pid_file.exists():
                print(f"  ✓ {name}: Running")
            else:
                print(f"  ✗ {name}: Not running - would restart")

    print("\n✓ Watchdog check complete")
    return True


def view_errors(since: str = "24h"):
    """View recent errors from audit log."""
    # Parse time range
    if since.endswith("h"):
        hours = int(since[:-1])
        cutoff = datetime.now() - timedelta(hours=hours)
    elif since.endswith("d"):
        days = int(since[:-1])
        cutoff = datetime.now() - timedelta(days=days)
    else:
        cutoff = datetime.now() - timedelta(hours=24)

    print(f"Errors since {cutoff.strftime('%Y-%m-%d %H:%M')}")
    print("-" * 50)

    # Check recent log files
    error_count = 0
    for log_file in sorted(LOGS_DIR.glob("*.json"), reverse=True)[:7]:  # Last 7 days
        try:
            logs = json.loads(log_file.read_text())
            for entry in logs:
                if entry.get("result", "").startswith("fail") or "error" in entry.get("result", "").lower():
                    log_time = datetime.fromisoformat(entry["timestamp"])
                    if log_time >= cutoff:
                        error_count += 1
                        print(f"\n  [{entry['timestamp']}]")
                        print(f"    Action: {entry.get('action_type', 'unknown')}")
                        print(f"    Target: {entry.get('target', 'unknown')}")
                        print(f"    Result: {entry.get('result', 'unknown')}")
        except Exception:
            continue

    if error_count == 0:
        print("  No errors found in the specified time range")
    else:
        print(f"\nTotal errors: {error_count}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Error Recovery & Graceful Degradation")
    parser.add_argument("--action", required=True,
                       choices=["retry", "refresh-token", "quarantine", "health-check",
                               "process-queue", "watchdog", "errors"])
    parser.add_argument("--operation-id", help="Operation ID for retry")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--backoff", choices=["exponential", "linear"], default="exponential")
    parser.add_argument("--service", help="Service for token refresh")
    parser.add_argument("--file", help="File path for quarantine")
    parser.add_argument("--reason", help="Reason for quarantine")
    parser.add_argument("--since", default="24h", help="Time range for error view (e.g., 24h, 7d)")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "retry":
        if not args.operation_id:
            print("Error: --operation-id required for retry action")
            sys.exit(1)
        retry_operation(args.operation_id, args.max_attempts, args.backoff)

    elif args.action == "refresh-token":
        if not args.service:
            print("Error: --service required for refresh-token action")
            sys.exit(1)
        refresh_token(args.service)

    elif args.action == "quarantine":
        if not args.file or not args.reason:
            print("Error: --file and --reason required for quarantine action")
            sys.exit(1)
        quarantine_file(args.file, args.reason)

    elif args.action == "health-check":
        if not check_health():
            sys.exit(1)

    elif args.action == "process-queue":
        process_recovery_queue()

    elif args.action == "watchdog":
        run_watchdog()

    elif args.action == "errors":
        view_errors(args.since)


if __name__ == "__main__":
    main()
