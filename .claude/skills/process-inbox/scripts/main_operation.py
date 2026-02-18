#!/usr/bin/env python3
"""
process-inbox skill implementation.

Implements the hackathon loop:
Needs_Action/ -> (plan + approval drafts) -> Plans/ + Pending_Approval/ -> Done/

This is intentionally a one-shot command (run via Claude Code skill or scheduler).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional


def _project_root() -> Path:
    # .claude/skills/process-inbox/scripts/main_operation.py -> scripts -> process-inbox -> skills -> .claude -> root
    return Path(__file__).resolve().parents[5]


def _claim_by_move(vault_root: Path, action_file: Path, agent_id: str) -> Optional[Path]:
    in_progress = vault_root / "In_Progress" / agent_id
    in_progress.mkdir(parents=True, exist_ok=True)
    dest = in_progress / action_file.name
    if dest.exists():
        dest = in_progress / f"{action_file.stem}_{int(time.time())}{action_file.suffix}"
    try:
        action_file.rename(dest)
        return dest
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Process vault Needs_Action into Plans + Pending_Approval")
    parser.add_argument("--vault-path", default="AI_Employee_Vault")
    parser.add_argument("--agent-role", default=os.getenv("AGENT_ROLE", "local"))
    parser.add_argument("--agent-id", default=os.getenv("AGENT_ID", "local-agent-001"))
    parser.add_argument("--max-files", type=int, default=0, help="Max action files to process (0=unlimited)")
    parser.add_argument("--draft-approvals", action="store_true", help="Create Pending_Approval drafts (cloud-style)")
    parser.add_argument("--update-dashboard", action="store_true", help="Update Dashboard.md after processing")

    args = parser.parse_args()

    project_root = _project_root()
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    from src.lib.vault import vault
    from src.orchestration.plan_manager import PlanManager
    from src.orchestration.draft_manager import DraftManager
    from src.orchestration.dashboard_manager import DashboardManager

    vault.set_root(str(args.vault_path))
    vault.ensure_structure()

    actions = sorted(vault.list_files_recursive("needs_action", "*.md"), key=lambda p: p.name)
    if args.max_files and args.max_files > 0:
        actions = actions[: args.max_files]

    if not actions:
        print("No pending action files.")
        return 0

    plan_manager = PlanManager(use_ai=True)
    draft_manager = DraftManager(agent_id=args.agent_id, agent_role=str(args.agent_role).strip().lower())

    processed = 0
    for action_file in actions:
        claimed = _claim_by_move(vault.root, action_file, args.agent_id)
        if not claimed:
            continue

        plan_filename = plan_manager.create_plan_from_action(claimed)
        if plan_filename:
            processed += 1

            if args.draft_approvals and str(args.agent_role).strip().lower() == "cloud":
                # Draft approvals for actions that require HITL.
                try:
                    raw = vault.read_file(claimed)
                    parts = raw.split("---", 2)
                    if len(parts) >= 3:
                        import yaml

                        meta = yaml.safe_load(parts[1]) or {}
                        action_type = str(meta.get("type", "")).strip().lower()
                        action_id = str(meta.get("id") or claimed.stem)
                        if action_type == "email":
                            draft_manager.draft_email_reply(claimed)
                        elif action_type == "social":
                            m = meta.get("metadata") or {}
                            platform = str(m.get("platform") or meta.get("platform") or "").strip().lower()
                            if platform:
                                draft_manager.draft_social_post(platform, parts[2].strip(), source_action_id=action_id)
                except Exception:
                    pass

            # Keep the claimed file in In_Progress until completion (file-movement completion strategy).
            # Local executor will move it to Done/ after approved execution / completion.

    if args.update_dashboard:
        try:
            dashboard = DashboardManager()
            watchers_status = {}
            pending = len(vault.list_files_recursive("needs_action", "*.md"))
            dashboard.update_status(watchers_status=watchers_status, pending_count=pending, recent_activity=[
                f"Processed {processed} action file(s) via /process-inbox",
            ])
        except Exception:
            pass

    print(f"Processed: {processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
