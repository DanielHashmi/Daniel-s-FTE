#!/usr/bin/env python3
"""ralph-wiggum-loop skill (Gold Tier)

Implements the hackathon "Ralph Wiggum" persistence loop using a file-movement
completion strategy.

Because Qwen is non-interactive, this skill re-runs one orchestration cycle
repeatedly until completion conditions are met.

Completion strategies:
- watch-file: complete when the watched file is moved into Done/
- global queue: complete when Needs_Action/, Pending_Approval/, Approved/, and In_Progress/ are empty

If Pending_Approval items exist, the loop pauses (HITL).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger
from src.lib.vault import vault
from src.orchestration.orchestrator import Orchestrator

logger = get_logger("ralph_wiggum_loop_skill")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_loop_id() -> str:
    return f"RALPH_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{int(time.time()*1000)}"


def _write_state(path: Path, state: Dict[str, Any]) -> None:
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _completion_watch_file(watch_file: str) -> bool:
    p = Path(watch_file)
    if not p.is_absolute():
        p = vault.root / watch_file
    done = vault.dirs["done"] / p.name
    return done.exists() or (not p.exists())


def _queue_empty() -> bool:
    return (
        len(vault.list_files_recursive("needs_action", "*.md")) == 0
        and len(vault.list_files_recursive("pending_approval", "*.md")) == 0
        and len(vault.list_files_recursive("approved", "*.md")) == 0
        and len(vault.list_files_recursive("in_progress", "*.md")) == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a persistent Ralph Wiggum loop")
    parser.add_argument("--prompt", required=True, help="High-level task prompt (recorded for audit)")
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--watch-file", help="Relative-to-vault file path to watch for movement to Done/")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between iterations")

    args = parser.parse_args()
    vault.ensure_structure()

    loop_id = _generate_loop_id()
    state_path = vault.dirs["ralph_state"] / f"{loop_id}.json"

    state: Dict[str, Any] = {
        "loop_id": loop_id,
        "prompt": args.prompt,
        "max_iterations": int(args.max_iterations),
        "watch_file": args.watch_file,
        "created": _utc_now_iso(),
        "status": "running",
        "current_iteration": 0,
        "iterations": [],
        "paused_for_approval": False,
    }

    _write_state(state_path, state)
    logger.log_action(
        action_type="ralph_loop_started",
        result="success",
        target=str(state_path),
        parameters={"prompt": args.prompt[:200], "watch_file": args.watch_file or ""},
        approval_status="not_required",
    )

    orch = Orchestrator()
    orch.running = True  # enables heartbeat writes during run_cycle

    for i in range(int(args.max_iterations)):
        state["current_iteration"] = i + 1

        # HITL pause: do not proceed while there are pending approvals.
        pending = vault.list_files_recursive("pending_approval", "*.md")
        if pending:
            state["status"] = "paused_awaiting_approval"
            state["paused_for_approval"] = True
            state["iterations"].append({
                "number": i + 1,
                "timestamp": _utc_now_iso(),
                "note": f"Paused: {len(pending)} pending approval item(s)",
            })
            _write_state(state_path, state)
            logger.log_action(
                action_type="ralph_loop_paused",
                result="success",
                target=loop_id,
                details={"pending_approval": len(pending)},
                approval_status="pending",
            )
            print(f"Paused: {len(pending)} pending approval item(s).")
            break

        # Run one orchestration cycle.
        try:
            orch.run_cycle()
        except Exception as exc:
            state["iterations"].append({
                "number": i + 1,
                "timestamp": _utc_now_iso(),
                "error": str(exc)[:300],
            })
            _write_state(state_path, state)
            logger.log_action(
                action_type="ralph_loop_iteration",
                result="error",
                target=loop_id,
                details={"iteration": i + 1, "error": str(exc)[:300]},
            )
            time.sleep(args.sleep)
            continue

        # Completion check.
        completed = False
        if args.watch_file:
            completed = _completion_watch_file(args.watch_file)
        else:
            completed = _queue_empty()

        state["iterations"].append({
            "number": i + 1,
            "timestamp": _utc_now_iso(),
            "completed": completed,
        })
        _write_state(state_path, state)

        if completed:
            state["status"] = "completed"
            state["completed"] = _utc_now_iso()
            _write_state(state_path, state)
            logger.log_action(
                action_type="ralph_loop_completed",
                result="success",
                target=loop_id,
                details={"iterations": i + 1},
            )
            print(f"Completed in {i + 1} iteration(s).")
            break

        time.sleep(args.sleep)

    if state.get("status") == "running":
        state["status"] = "max_iterations_reached"
        _write_state(state_path, state)
        logger.log_action(
            action_type="ralph_loop_max_iterations",
            result="warning",
            target=loop_id,
            details={"iterations": state.get("current_iteration")},
        )
        print("Max iterations reached without completion.")

    # Archive state into Ralph_History for audit.
    try:
        history_path = vault.dirs["ralph_history"] / f"{loop_id}.json"
        history_path.write_text(state_path.read_text(encoding="utf-8"), encoding="utf-8")
        state_path.unlink(missing_ok=True)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
