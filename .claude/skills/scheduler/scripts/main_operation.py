#!/usr/bin/env python3
"""
Scheduler skill (Silver/Gold/Platinum).

Hackathon requirement: basic scheduling via cron (Linux/macOS) or Task Scheduler (Windows).
This skill stores schedules in the vault and can apply them to Windows Task Scheduler.

Windows schedule formats supported by `apply`:
- hourly
- daily@HH:MM
- weekly@DAY@HH:MM (DAY=MON,TUE,WED,THU,FRI,SAT,SUN)
- every@Nmin
- every@Nhour
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VAULT_ROOT = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
CONFIG_DIR = VAULT_ROOT / "Config"
SCHEDULE_FILE = CONFIG_DIR / "schedules.json"


def setup_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_schedules() -> list[dict]:
    if not SCHEDULE_FILE.exists():
        return []
    try:
        return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_schedules(schedules: list[dict]) -> None:
    SCHEDULE_FILE.write_text(json.dumps(schedules, indent=2), encoding="utf-8")


def list_schedules() -> None:
    schedules = load_schedules()
    if not schedules:
        print("No scheduled tasks.")
        return

    print(f"{'Comment':<24} | {'Schedule':<18} | Command")
    print("-" * 90)
    for s in schedules:
        print(f"{s.get('comment', 'N/A'):<24} | {s.get('schedule', 'N/A'):<18} | {s.get('cmd', 'N/A')}")


def add_schedule(cmd: str, schedule: str, comment: str) -> bool:
    schedules = load_schedules()
    if any(s.get("comment") == comment for s in schedules):
        print(f"[ERR] Schedule with comment '{comment}' already exists. Remove it first.")
        return False

    schedules.append({"cmd": cmd, "schedule": schedule, "comment": comment, "active": True})
    save_schedules(schedules)
    print(f"[OK] Added schedule: {comment} ({schedule})")
    return True


def remove_schedule(comment: str) -> bool:
    schedules = load_schedules()
    before = len(schedules)
    schedules = [s for s in schedules if s.get("comment") != comment]
    if len(schedules) == before:
        print(f"[ERR] Schedule '{comment}' not found.")
        return False
    save_schedules(schedules)
    print(f"[OK] Removed schedule: {comment}")
    return True


def _parse_windows_schedule(schedule: str) -> list[str]:
    s = (schedule or "").strip().lower()
    if s == "hourly":
        return ["/SC", "HOURLY", "/MO", "1"]

    m = re.match(r"^daily@(\d{2}:\d{2})$", s)
    if m:
        return ["/SC", "DAILY", "/ST", m.group(1)]

    m = re.match(r"^weekly@([a-z]{3})@(\d{2}:\d{2})$", s)
    if m:
        day = m.group(1).upper()
        return ["/SC", "WEEKLY", "/D", day, "/ST", m.group(2)]

    m = re.match(r"^every@(\d+)min$", s)
    if m:
        return ["/SC", "MINUTE", "/MO", m.group(1)]

    m = re.match(r"^every@(\d+)hour$", s)
    if m:
        return ["/SC", "HOURLY", "/MO", m.group(1)]

    raise ValueError("Unsupported format. Use: hourly | daily@HH:MM | weekly@DAY@HH:MM | every@Nmin | every@Nhour")


def apply_schedules_windows() -> bool:
    schedules = load_schedules()
    if not schedules:
        print("No schedules to apply.")
        return True

    failures = 0
    for s in schedules:
        if not s.get("active", True):
            continue

        comment = s.get("comment") or "fte-task"
        cmd = s.get("cmd")
        schedule = s.get("schedule")
        if not cmd or not schedule:
            failures += 1
            print(f"[ERR] Skipping invalid entry (missing cmd/schedule): {comment}")
            continue

        task_name = f"FTE_{comment}"
        try:
            sch_args = _parse_windows_schedule(schedule)
        except Exception as exc:
            failures += 1
            print(f"[ERR] Invalid schedule '{schedule}' for {comment}: {exc}")
            continue

        args = [
            "schtasks",
            "/Create",
            "/TN",
            task_name,
            "/TR",
            f"cmd.exe /c {cmd}",
            *sch_args,
            "/F",
        ]

        try:
            subprocess.run(args, check=True, capture_output=True, text=True)
            print(f"[OK] Applied: {task_name} ({schedule})")
        except subprocess.CalledProcessError as exc:
            failures += 1
            stderr = (exc.stderr or "").strip()
            print(f"[ERR] Failed applying {task_name}: {stderr[:200]}")

    return failures == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scheduler operations")
    parser.add_argument("--action", required=True, choices=["list", "add", "remove", "apply"])
    parser.add_argument("--cmd", help="Command to execute")
    parser.add_argument("--schedule", help="Schedule string")
    parser.add_argument("--comment", help="Unique identifier/comment for the task")
    args = parser.parse_args()

    setup_dirs()

    if args.action == "list":
        list_schedules()
        return 0

    if args.action == "add":
        if not all([args.cmd, args.schedule, args.comment]):
            print("[ERR] --cmd, --schedule, and --comment required for add")
            return 1
        return 0 if add_schedule(args.cmd, args.schedule, args.comment) else 1

    if args.action == "remove":
        if not args.comment:
            print("[ERR] --comment required for remove")
            return 1
        return 0 if remove_schedule(args.comment) else 1

    if args.action == "apply":
        if os.name != "nt":
            print("[ERR] apply is implemented for Windows Task Scheduler only.")
            return 1
        return 0 if apply_schedules_windows() else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
