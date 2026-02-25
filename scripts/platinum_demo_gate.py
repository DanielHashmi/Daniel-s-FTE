#!/usr/bin/env python3
"""Platinum demo gate validator

Implements the hackathon minimum passing gate:
Email arrives while Local is offline -> Cloud drafts + Pending_Approval ->
Local returns, human approves -> Local executes via MCP -> logs -> Done.

Usage:
  python scripts/platinum_demo_gate.py [--vault-path AI_Employee_Vault_DemoGate] [--cleanup]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_frontmatter(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


def _parse_log_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            return [data]
    except Exception:
        pass

    out: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Platinum minimum passing gate flow")
    parser.add_argument("--vault-path", default="AI_Employee_Vault_DemoGate")
    parser.add_argument("--cleanup", action="store_true", help="Remove demo vault after run")
    args = parser.parse_args()

    # Use an isolated demo vault so this test does not interfere with real queues.
    demo_vault = (PROJECT_ROOT / args.vault_path).resolve()
    if demo_vault.exists():
        shutil.rmtree(demo_vault)
    demo_vault.mkdir(parents=True, exist_ok=True)

    os.environ["VAULT_PATH"] = str(demo_vault)
    os.environ["REASONING_ENGINE"] = os.getenv("REASONING_ENGINE", "qwen")
    os.environ["DRY_RUN"] = "true"
    os.environ["DEV_MODE"] = "true"
    os.environ["AUTO_APPROVAL_ENABLED"] = "false"

    # Import after VAULT_PATH is set.
    from src.lib.vault import vault
    from src.orchestration.orchestrator import Orchestrator

    vault.set_root(str(demo_vault))
    vault.ensure_structure()

    print("[1/8] Creating inbound email action while local is offline...")
    action_id = f"demo_email_{int(time.time())}"
    action_content = (
        "---\n"
        f"id: \"{action_id}\"\n"
        "type: \"email\"\n"
        "source: \"gmail_watcher\"\n"
        "domain: \"personal\"\n"
        "priority: \"high\"\n"
        f"timestamp: \"{_now_iso()}\"\n"
        "status: \"pending\"\n"
        "metadata:\n"
        "  sender: \"client@example.com\"\n"
        "  subject: \"Need invoice update\"\n"
        "  thread_id: \"demo-thread-001\"\n"
        "  msg_id: \"demo-msg-001\"\n"
        "---\n\n"
        "# Incoming Email\n\n"
        "Please send me the updated invoice by today.\n"
    )
    action_file = vault.write_action(f"EMAIL_{action_id}.md", action_content, domain="personal")

    print("[2/8] Running cloud cycle (draft-only)...")
    os.environ["AGENT_ROLE"] = "cloud"
    os.environ["AGENT_ID"] = "cloud-agent-demo"
    cloud = Orchestrator()
    cloud.running = True
    cloud.run_cycle()

    print("[3/8] Validating cloud outputs (plan + pending approval)...")
    plan_candidates = vault.list_files_recursive("plans", f"PLAN_{action_id}.md")
    if not plan_candidates:
        print("FAIL: Cloud did not create plan file")
        return 1

    pending = vault.list_files_recursive("pending_approval", "*.md")
    approval_file: Optional[Path] = None
    for p in pending:
        meta = _read_frontmatter(p)
        if str(meta.get("source_action_id") or "") == action_id:
            approval_file = p
            break
    if not approval_file:
        print("FAIL: Cloud did not create matching Pending_Approval draft")
        return 1

    print("[4/8] Simulating human approval (move to Approved/)...")
    approval_meta = _read_frontmatter(approval_file)
    domain = str(approval_meta.get("domain") or "").strip().lower() or "general"
    approved_dir = vault.get_domain_dir("approved", domain)
    approved_dir.mkdir(parents=True, exist_ok=True)
    approved_file = approved_dir / approval_file.name
    approval_file.rename(approved_file)

    print("[5/8] Running local cycle (executes approved via MCP in dry-run)...")
    os.environ["AGENT_ROLE"] = "local"
    os.environ["AGENT_ID"] = "local-agent-demo"
    local = Orchestrator()
    local.running = True
    local.run_cycle()

    print("[6/8] Verifying approved item moved to Done...")
    done_files = vault.list_files_recursive("done", "*.md")
    done_names = {p.name for p in done_files}
    if approved_file.name not in done_names:
        print("FAIL: Approved item was not moved to Done")
        return 1

    print("[7/8] Verifying originating action + plan completion...")
    done_action = any(action_id in p.name for p in done_files)
    if not done_action:
        print("FAIL: Originating action file not completed into Done")
        return 1

    plan_in_done = any(p.name == f"PLAN_{action_id}.md" for p in done_files)
    if not plan_in_done:
        print("FAIL: Plan file not moved to Done")
        return 1

    print("[8/8] Verifying audit log entry...")
    log_file = vault.dirs["logs"] / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entries = _parse_log_file(log_file)
    has_email_send = any(
        str(e.get("action_type") or "") in {"email_send", "send_email"}
        for e in entries
    )
    if not has_email_send:
        print("FAIL: No email_send audit entry found")
        return 1

    print("PASS: Platinum minimum gate flow completed successfully")
    print(f"Demo vault: {demo_vault}")

    if args.cleanup:
        shutil.rmtree(demo_vault, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
