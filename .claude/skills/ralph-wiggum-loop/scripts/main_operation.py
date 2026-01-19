#!/usr/bin/env python3
"""Ralph Wiggum Loop - Gold Tier Skill

Autonomous multi-step task executor using persistent iteration loop.
Continues until task completion or max iterations reached.
"""
import argparse
import sys
import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
RALPH_STATE = VAULT_ROOT / "Ralph_State"
RALPH_HISTORY = VAULT_ROOT / "Ralph_History"
LOGS_DIR = VAULT_ROOT / "Logs"
DONE_DIR = VAULT_ROOT / "Done"
PENDING_APPROVAL = VAULT_ROOT / "Pending_Approval"
APPROVED_DIR = VAULT_ROOT / "Approved"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_TIMEOUT = 3600  # 1 hour per iteration


def setup_dirs():
    RALPH_STATE.mkdir(parents=True, exist_ok=True)
    RALPH_HISTORY.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "ralph_wiggum_loop",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "ralph_wiggum_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


def generate_loop_id(prompt: str) -> str:
    """Generate unique loop ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_part = hashlib.md5(prompt.encode()).hexdigest()[:8]
    return f"RALPH_{timestamp}_{hash_part}"


def create_state_file(loop_id: str, prompt: str, max_iterations: int,
                      completion_promise: Optional[str] = None,
                      watch_file: Optional[str] = None,
                      done_folder: Optional[str] = None) -> Path:
    """Create state file for tracking loop execution."""
    state = {
        "loop_id": loop_id,
        "prompt": prompt,
        "max_iterations": max_iterations,
        "completion_promise": completion_promise,
        "watch_file": watch_file,
        "done_folder": done_folder or str(DONE_DIR),
        "current_iteration": 0,
        "status": "pending",
        "started_at": datetime.now().isoformat(),
        "iterations": [],
        "errors": [],
        "paused_for_approval": False
    }

    state_file = RALPH_STATE / f"{loop_id}.json"
    state_file.write_text(json.dumps(state, indent=2))
    return state_file


def check_completion_promise(output: str, promise: str) -> bool:
    """Check if output contains completion promise."""
    return f"<promise>{promise}</promise>" in output or promise in output


def check_file_moved(watch_file: str, done_folder: str) -> bool:
    """Check if watched file has been moved to done folder."""
    original = Path(watch_file)
    done = Path(done_folder) / original.name

    # File is done if it's in done folder or no longer in original location
    return done.exists() or not original.exists()


def check_approval_needed(state: dict) -> bool:
    """Check if there are pending approval requests."""
    # Look for approval files related to this loop
    loop_id = state["loop_id"]
    pending = list(PENDING_APPROVAL.glob(f"*{loop_id}*.md"))
    return len(pending) > 0


def check_approval_granted(state: dict) -> bool:
    """Check if approval has been granted."""
    loop_id = state["loop_id"]
    approved = list(APPROVED_DIR.glob(f"*{loop_id}*.md")) if APPROVED_DIR.exists() else []
    return len(approved) > 0


def run_iteration(state: dict) -> tuple[bool, str]:
    """
    Run one iteration of the loop.
    Returns (completed, output).

    In production, this would invoke Claude Code with the prompt.
    For demonstration, we simulate the iteration.
    """
    prompt = state["prompt"]
    iteration = state["current_iteration"] + 1

    # Simulate Claude Code invocation
    # In production: subprocess.run(["ccr", "code", "--print", prompt], ...)

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        # Simulate work being done
        output = f"[Iteration {iteration}] Processing: {prompt[:50]}..."

        # Simulate completion after a few iterations
        if iteration >= 3:
            if state.get("completion_promise"):
                output += f"\n<promise>{state['completion_promise']}</promise>"

        return False, output

    # Real execution would go here
    try:
        result = subprocess.run(
            ["ccr", "code", "--print", prompt],
            capture_output=True,
            text=True,
            timeout=state.get("timeout", DEFAULT_TIMEOUT)
        )
        return False, result.stdout
    except subprocess.TimeoutExpired:
        return False, "ERROR: Iteration timeout"
    except Exception as e:
        return False, f"ERROR: {str(e)}"


def start_loop(prompt: str, max_iterations: int = DEFAULT_MAX_ITERATIONS,
               completion_promise: Optional[str] = None,
               watch_file: Optional[str] = None,
               done_folder: Optional[str] = None,
               timeout: int = DEFAULT_TIMEOUT) -> str:
    """Start a new Ralph Wiggum loop."""

    loop_id = generate_loop_id(prompt)
    state_file = create_state_file(
        loop_id, prompt, max_iterations,
        completion_promise, watch_file, done_folder
    )

    state = json.loads(state_file.read_text())
    state["status"] = "running"
    state["timeout"] = timeout

    print(f"✓ Ralph Wiggum Loop started: {loop_id}")
    print(f"  Max iterations: {max_iterations}")
    print(f"  Completion: {'Promise-based' if completion_promise else 'File-movement'}")

    completed = False
    while state["current_iteration"] < max_iterations and not completed:
        iteration = state["current_iteration"] + 1
        print(f"\n[Iteration {iteration}/{max_iterations}]")

        # Check for approval pause
        if check_approval_needed(state) and not check_approval_granted(state):
            state["paused_for_approval"] = True
            state["status"] = "paused_awaiting_approval"
            state_file.write_text(json.dumps(state, indent=2))
            print("⏸️  Paused: Awaiting human approval")
            audit_log("pause", loop_id, "awaiting_approval", {"iteration": iteration})
            break

        # Run iteration
        completed, output = run_iteration(state)

        # Record iteration
        state["iterations"].append({
            "number": iteration,
            "timestamp": datetime.now().isoformat(),
            "output_preview": output[:500],
            "completed": completed
        })
        state["current_iteration"] = iteration

        # Check for completion
        if completion_promise and check_completion_promise(output, completion_promise):
            completed = True
            print(f"✓ Completion promise detected!")

        if watch_file and check_file_moved(watch_file, state["done_folder"]):
            completed = True
            print(f"✓ Watched file moved to Done!")

        # Save state
        state_file.write_text(json.dumps(state, indent=2))

        if completed:
            break

        # Brief pause between iterations
        time.sleep(1)

    # Final status
    if completed:
        state["status"] = "completed"
        state["completed_at"] = datetime.now().isoformat()
        print(f"\n✓ Loop completed in {state['current_iteration']} iteration(s)")
    elif state["current_iteration"] >= max_iterations:
        state["status"] = "max_iterations_reached"
        print(f"\n⚠️  Max iterations ({max_iterations}) reached without completion")
        # Create human review request
        create_review_request(state)

    # Move state to history
    state_file.write_text(json.dumps(state, indent=2))
    history_file = RALPH_HISTORY / f"{loop_id}.json"
    state_file.rename(history_file)

    audit_log("complete" if completed else "max_iterations", loop_id, state["status"],
             {"iterations": state["current_iteration"]})

    return loop_id


def create_review_request(state: dict):
    """Create human review request when max iterations reached."""
    review_content = f"""---
id: REVIEW-{state['loop_id']}
type: review_request
action: ralph_loop_incomplete
created: {datetime.now().isoformat()}
priority: high
status: pending
---

# Ralph Wiggum Loop - Human Review Required

## Loop Details
- **Loop ID:** {state['loop_id']}
- **Max Iterations:** {state['max_iterations']}
- **Iterations Used:** {state['current_iteration']}
- **Status:** Max iterations reached without completion

## Original Prompt
{state['prompt']}

## Iteration History
"""
    for it in state["iterations"][-5:]:  # Last 5 iterations
        review_content += f"\n### Iteration {it['number']}\n"
        review_content += f"```\n{it['output_preview']}\n```\n"

    review_content += """
## Action Required
Please review the loop progress and either:
1. Manually complete the remaining work
2. Restart the loop with modified parameters
3. Mark as abandoned

---
*Generated by Ralph Wiggum Loop Skill*
"""

    review_file = PENDING_APPROVAL / f"REVIEW_{state['loop_id']}.md"
    review_file.write_text(review_content)
    print(f"  Review request created: {review_file.name}")


def check_status():
    """Check status of all loops."""
    print("Ralph Wiggum Loop Status:")
    print("-" * 50)

    # Active loops
    active = list(RALPH_STATE.glob("RALPH_*.json"))
    print(f"\nActive Loops: {len(active)}")
    for f in active:
        state = json.loads(f.read_text())
        status_emoji = "🔄" if state["status"] == "running" else "⏸️"
        print(f"  {status_emoji} {state['loop_id']}: {state['status']} ({state['current_iteration']}/{state['max_iterations']})")

    # Completed loops (last 5)
    history = sorted(RALPH_HISTORY.glob("RALPH_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
    print(f"\nRecent History: {len(history)}")
    for f in history:
        state = json.loads(f.read_text())
        status_emoji = "✅" if state["status"] == "completed" else "⚠️"
        print(f"  {status_emoji} {state['loop_id']}: {state['status']}")


def stop_loop(loop_id: str):
    """Stop an active loop."""
    state_file = RALPH_STATE / f"{loop_id}.json"

    if not state_file.exists():
        print(f"✗ Loop not found: {loop_id}")
        return False

    state = json.loads(state_file.read_text())
    state["status"] = "stopped"
    state["stopped_at"] = datetime.now().isoformat()

    # Move to history
    history_file = RALPH_HISTORY / f"{loop_id}.json"
    state_file.write_text(json.dumps(state, indent=2))
    state_file.rename(history_file)

    print(f"✓ Loop stopped: {loop_id}")
    audit_log("stop", loop_id, "stopped", {"iterations": state["current_iteration"]})
    return True


def view_history(limit: int = 10):
    """View loop history."""
    history = sorted(RALPH_HISTORY.glob("RALPH_*.json"),
                    key=lambda x: x.stat().st_mtime, reverse=True)[:limit]

    print(f"Ralph Wiggum Loop History (Last {limit}):")
    print("-" * 60)

    for f in history:
        state = json.loads(f.read_text())
        status_emoji = "✅" if state["status"] == "completed" else "⚠️"
        iterations = state["current_iteration"]
        prompt_preview = state["prompt"][:40] + "..." if len(state["prompt"]) > 40 else state["prompt"]
        print(f"{status_emoji} {state['loop_id']}")
        print(f"   Prompt: {prompt_preview}")
        print(f"   Status: {state['status']} | Iterations: {iterations}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Ralph Wiggum Loop - Autonomous Task Executor")
    parser.add_argument("--action", required=True,
                       choices=["start", "status", "stop", "history"])
    parser.add_argument("--prompt", help="Task prompt for the loop")
    parser.add_argument("--completion-promise", help="Text to detect completion")
    parser.add_argument("--watch-file", help="File to watch for movement to Done")
    parser.add_argument("--done-folder", default=str(DONE_DIR), help="Done folder path")
    parser.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout per iteration (seconds)")
    parser.add_argument("--loop-id", help="Loop ID for stop action")
    parser.add_argument("--limit", type=int, default=10, help="History limit")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "start":
        if not args.prompt:
            print("Error: --prompt required for start action")
            sys.exit(1)
        if not args.completion_promise and not args.watch_file:
            print("Warning: No completion method specified. Using promise-based with 'TASK_COMPLETE'")
            args.completion_promise = "TASK_COMPLETE"

        start_loop(
            args.prompt,
            args.max_iterations,
            args.completion_promise,
            args.watch_file,
            args.done_folder,
            args.timeout
        )

    elif args.action == "status":
        check_status()

    elif args.action == "stop":
        if not args.loop_id:
            print("Error: --loop-id required for stop action")
            sys.exit(1)
        stop_loop(args.loop_id)

    elif args.action == "history":
        view_history(args.limit)


if __name__ == "__main__":
    main()
