#!/usr/bin/env python3
"""watcher-manager skill

Manage always-on orchestrator/watcher processes via PM2.

Current architecture:
- Watchers run as threads inside orchestrator processes
- PM2 apps are defined in `ecosystem.config.js`
  - `daniel-fte-orchestrator-local`
  - `daniel-fte-orchestrator-cloud`
  - `daniel-fte-dashboard`
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[5]
ECOSYSTEM = PROJECT_ROOT / "ecosystem.config.js"

APP_GROUPS: Dict[str, List[str]] = {
    "local": ["daniel-fte-orchestrator-local"],
    "cloud": ["daniel-fte-orchestrator-cloud"],
    "dashboard": ["daniel-fte-dashboard"],
    "all": [
        "daniel-fte-orchestrator-local",
        "daniel-fte-orchestrator-cloud",
        "daniel-fte-dashboard",
    ],
}


def _run_pm2(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pm2", *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )


def _pm2_available() -> bool:
    try:
        out = _run_pm2(["--version"])
        return out.returncode == 0
    except FileNotFoundError:
        return False


def _print_result(result: subprocess.CompletedProcess) -> None:
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)


def _ensure_started(apps: List[str], dry_run: bool) -> int:
    if not ECOSYSTEM.exists():
        print(f"Missing PM2 ecosystem file: {ECOSYSTEM}", file=sys.stderr)
        return 1
    for app in apps:
        cmd = ["start", str(ECOSYSTEM), "--only", app]
        if dry_run:
            print(f"[DRY RUN] pm2 {' '.join(cmd)}")
            continue
        res = _run_pm2(cmd)
        _print_result(res)
        if res.returncode != 0:
            return res.returncode
    if not dry_run:
        _run_pm2(["save"])
    return 0


def _simple_action(action: str, apps: List[str], dry_run: bool) -> int:
    for app in apps:
        cmd = [action, app]
        if dry_run:
            print(f"[DRY RUN] pm2 {' '.join(cmd)}")
            continue
        res = _run_pm2(cmd)
        _print_result(res)
        if res.returncode != 0:
            return res.returncode
    if action in {"stop", "restart"} and not dry_run:
        _run_pm2(["save"])
    return 0


def _status(apps: List[str]) -> int:
    res = _run_pm2(["jlist"])
    if res.returncode != 0:
        _print_result(res)
        return res.returncode

    try:
        data = json.loads(res.stdout or "[]")
    except json.JSONDecodeError:
        print("Failed to parse PM2 status JSON", file=sys.stderr)
        return 1

    by_name = {item.get("name"): item for item in data if isinstance(item, dict)}
    print(f"{'APP':<35} {'STATUS':<12} {'RESTARTS':<9} {'UPTIME_SEC'}")
    print("-" * 72)
    now_ms = time.time() * 1000
    for app in apps:
        item = by_name.get(app) or {}
        env = item.get("pm2_env") or {}
        status = env.get("status", "missing")
        restarts = env.get("restart_time", 0)
        uptime_ms = env.get("pm_uptime")
        uptime_sec = 0
        if isinstance(uptime_ms, (int, float)):
            uptime_sec = int(max(0, (now_ms - uptime_ms) / 1000))
        print(f"{app:<35} {status:<12} {str(restarts):<9} {uptime_sec}")
    return 0


def _logs(apps: List[str], lines: int) -> int:
    target = ",".join(apps)
    # Note: `pm2 logs` is a streaming command. Use `--nostream` for one-shot output.
    res = _run_pm2(["logs", target, "--lines", str(lines), "--nostream"])
    _print_result(res)
    return res.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage orchestrator/watcher processes via PM2")
    parser.add_argument("--action", required=True, choices=["start", "stop", "restart", "status", "logs"])
    parser.add_argument(
        "--target",
        default="all",
        choices=["local", "cloud", "dashboard", "all"],
        help="Which PM2 app group to manage",
    )
    parser.add_argument("--lines", type=int, default=50, help="Number of log lines for --action logs")
    parser.add_argument("--dry-run", action="store_true", help="Print PM2 commands without executing them")
    args = parser.parse_args()

    if not _pm2_available():
        print("PM2 is not available. Install with: npm install -g pm2", file=sys.stderr)
        return 1

    apps = APP_GROUPS[args.target]
    if args.action == "start":
        return _ensure_started(apps, dry_run=args.dry_run)
    if args.action == "stop":
        return _simple_action("stop", apps, dry_run=args.dry_run)
    if args.action == "restart":
        return _simple_action("restart", apps, dry_run=args.dry_run)
    if args.action == "status":
        return _status(apps)
    if args.action == "logs":
        return _logs(apps, args.lines)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
