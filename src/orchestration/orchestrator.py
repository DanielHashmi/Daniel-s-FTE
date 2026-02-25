"""
Central Orchestrator.

This is the main brain of the Functional Assistant.
It monitors the vault (Needs_Action) for new files,
triggers the planning process, and oversees execution.
"""

import time
import sys
import threading
import os
import json
import subprocess
from pathlib import Path
from typing import Optional
from src.lib.logging import get_logger
from src.lib.vault import vault

# Import Watchers lazily/safely so role-specific environments can run with
# only the dependencies they need.
try:
    from src.watchers.gmail import GmailWatcher
except Exception:
    GmailWatcher = None

try:
    from src.watchers.whatsapp import WhatsAppWatcher
except Exception:
    WhatsAppWatcher = None

try:
    from src.watchers.linkedin import LinkedInWatcher
except Exception:
    LinkedInWatcher = None

try:
    from src.watchers.odoo import OdooWatcher
except Exception:
    OdooWatcher = None

try:
    from src.watchers.banking import BankingWatcher
except Exception:
    BankingWatcher = None

try:
    from src.watchers.filesystem import FileSystemWatcher
except Exception:
    FileSystemWatcher = None

# Import Plan Manager & Approval Manager
from src.orchestration.plan_manager import PlanManager
from src.orchestration.approval_manager import ApprovalManager
from src.handlers.local_approval import LocalApprovalHandler
from src.orchestration.watchdog import Watchdog
from src.orchestration.dashboard_manager import DashboardManager
from src.orchestration.ralph_loop import RalphLoopManager
from src.orchestration.draft_manager import DraftManager
import yaml

class Orchestrator:
    def __init__(self):
        self.logger = get_logger("orchestrator")
        self.running = False
        self.poll_interval = 5 # Seconds - fast poll for local file changes
        self.max_needs_action_per_cycle = int(
            os.getenv("ORCHESTRATOR_MAX_NEEDS_ACTION_PER_CYCLE", "2")
        )

        # Platinum: work-zone specialization (cloud drafts, local executes)
        self.agent_role = os.getenv("AGENT_ROLE", "local").strip().lower()
        if self.agent_role not in {"local", "cloud"}:
            self.logger.warning(f"Unknown AGENT_ROLE '{self.agent_role}', defaulting to 'local'")
            self.agent_role = "local"

        self.agent_id = (
            os.getenv("AGENT_ID")
            or (os.getenv("LOCAL_AGENT_ID") if self.agent_role == "local" else os.getenv("CLOUD_AGENT_ID"))
            or f"{self.agent_role}-agent-001"
        )
        # Platinum: enforce work-zone ownership unless explicitly disabled.
        self.strict_work_zones = os.getenv("STRICT_WORK_ZONES", "true").strip().lower() == "true"

        # Initialize watchers
        if self.agent_role == "cloud":
            # Cloud: email triage + social draft/scheduling + accounting drafts (no WhatsApp/banking sessions)
            watcher_specs = [
                ("gmail", GmailWatcher, 60),
                ("linkedin", LinkedInWatcher, 300),
                ("odoo", OdooWatcher, 60),
            ]
        else:
            # Local: approvals + WhatsApp session + final actions (email/social sending occurs only after approval)
            watcher_specs = [
                ("filesystem", FileSystemWatcher, 30),
                ("whatsapp", WhatsAppWatcher, 60),
                ("banking", BankingWatcher, 300),
                ("odoo", OdooWatcher, 60),
            ]
        self.watchers = []
        for watcher_key, watcher_cls, interval in watcher_specs:
            if self._watcher_enabled(watcher_key, default=True):
                if watcher_cls is None:
                    self.logger.warning(
                        f"Watcher unavailable due import/dependency issue: {watcher_key}",
                        watcher=watcher_key,
                        agent_role=self.agent_role,
                    )
                    continue
                self.watchers.append(watcher_cls(interval=interval))
            else:
                self.logger.info(
                    f"Watcher disabled by env: {watcher_key}",
                    watcher=watcher_key,
                    agent_role=self.agent_role,
                )
        self.watcher_threads = []

        # Initialize Managers
        self.plan_manager = PlanManager()
        self.approval_manager = ApprovalManager()
        self.local_approval_handler = LocalApprovalHandler(str(vault.root))
        self.watchdog = Watchdog()
        self.dashboard_manager = DashboardManager()
        self.ralph_manager = RalphLoopManager()
        self.ralph_manager.integrate_with_orchestrator(self)
        self.draft_manager = DraftManager(agent_id=self.agent_id, agent_role=self.agent_role)
        
        self.last_health_check = 0
        self.last_dashboard_update = 0
        self.last_odoo_sync = 0
        self.recent_activity = []
        self.approval_retry_state = {}
        # Safety default: avoid automatic re-execution of approved external actions
        # (e.g., duplicate social posts/emails) unless explicitly enabled.
        self.approved_retry_enabled = os.getenv("APPROVED_RETRY_ENABLED", "false").strip().lower() == "true"
        self.instance_lock_path = vault.dirs["logs"] / f"orchestrator_{self.agent_role}.lock"

    @staticmethod
    def _pid_exists(pid: int) -> bool:
        if not isinstance(pid, int) or pid <= 0:
            return False
        if os.name == "nt":
            try:
                proc = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                output = (proc.stdout or "").lower()
                if "no tasks are running" in output:
                    return False
                return str(pid) in output
            except Exception:
                # Fall through to os.kill check.
                pass
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # If access is denied, assume process exists.
            return True
        except OSError:
            return False
        return True

    def _acquire_instance_lock(self) -> bool:
        """
        Prevent multiple orchestrator processes for the same role from running concurrently.
        """
        try:
            self.instance_lock_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "pid": os.getpid(),
                "agent_role": self.agent_role,
                "agent_id": self.agent_id,
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            payload_text = json.dumps(payload)

            # Race-safe lock acquisition: create lock file atomically.
            for _ in range(2):
                try:
                    fd = os.open(
                        str(self.instance_lock_path),
                        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    )
                    with os.fdopen(fd, "w", encoding="utf-8") as fh:
                        fh.write(payload_text)
                    return True
                except FileExistsError:
                    try:
                        current = json.loads(self.instance_lock_path.read_text(encoding="utf-8"))
                    except Exception:
                        current = {}

                    current_pid = int(current.get("pid") or 0)
                    if current_pid and current_pid != os.getpid() and self._pid_exists(current_pid):
                        self.logger.error(
                            f"Another {self.agent_role} orchestrator is already running (pid={current_pid}). "
                            "Refusing to start duplicate instance."
                        )
                        return False

                    # Stale/corrupt lock: remove and retry once.
                    try:
                        self.instance_lock_path.unlink(missing_ok=True)
                    except Exception as unlink_exc:
                        self.logger.error(f"Failed to clear stale lock: {unlink_exc}")
                        return False

            self.logger.error("Failed to acquire orchestrator lock due to lock contention.")
            return False
        except Exception as exc:
            self.logger.error(f"Failed to acquire orchestrator lock: {exc}")
            return False

    def _release_instance_lock(self) -> None:
        try:
            if not self.instance_lock_path.exists():
                return
            try:
                current = json.loads(self.instance_lock_path.read_text(encoding="utf-8"))
            except Exception:
                current = {}
            lock_pid = int(current.get("pid") or 0)
            if not lock_pid or lock_pid == os.getpid():
                self.instance_lock_path.unlink(missing_ok=True)
        except Exception as exc:
            self.logger.warning(f"Failed to release orchestrator lock: {exc}")

    @staticmethod
    def _env_flag(name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    def _watcher_enabled(self, watcher_key: str, default: bool = True) -> bool:
        return self._env_flag(f"WATCHER_{watcher_key.upper()}_ENABLED", default=default)

    @staticmethod
    def _read_action_metadata(action_file: Path) -> dict:
        try:
            raw = vault.read_file(action_file)
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                data = yaml.safe_load(parts[1]) or {}
                if isinstance(data, dict):
                    return data
        except Exception:
            return {}
        return {}

    def _action_owned_by_role(self, meta: dict) -> bool:
        """
        Platinum work-zone specialization gate.

        Cloud owns:
        - Email triage/drafts
        - Social draft generation/scheduling

        Local owns:
        - Approvals/final execution
        - WhatsApp and banking initiated tasks
        """
        if not self.strict_work_zones:
            return True

        owner_role = str(meta.get("owner_role") or "").strip().lower()
        if owner_role in {"cloud", "local"}:
            return owner_role == self.agent_role

        action_type = str(meta.get("type") or "").strip().lower()
        source = str(meta.get("source") or "").strip().lower()

        cloud_sources = {"gmail", "gmail_watcher", "linkedin", "linkedin_watcher", "scheduler"}
        cloud_types = {"email", "social", "notification"}

        if self.agent_role == "cloud":
            return action_type in cloud_types or source in cloud_sources

        # Local role: avoid claiming cloud-owned drafting inputs.
        if action_type in cloud_types or source in cloud_sources:
            return False
        return True

    def _write_heartbeat(self) -> None:
        """Write a small heartbeat file so the Web UI can detect if the brain is running."""
        try:
            payload = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "pid": os.getpid(),
                "poll_interval_seconds": self.poll_interval,
            }
            path = vault.dirs["logs"] / "orchestrator_heartbeat.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
        except Exception as exc:
            # Never let heartbeat failures break orchestration.
            self.logger.warning(f"Failed to write heartbeat: {exc}")

    def _heartbeat_loop(self) -> None:
        """Continuously write a heartbeat even if a single orchestration cycle takes a long time."""
        while self.running:
            self._write_heartbeat()
            time.sleep(5)

    def start_watchers(self):
        """Start all watchers in separate threads."""
        for watcher in self.watchers:
            t = threading.Thread(target=watcher.start, daemon=True)
            t.start()
            self.watcher_threads.append(t)
            self.logger.info(f"Started {watcher.name} thread")

    def stop_watchers(self):
        """Stop all watchers."""
        for watcher in self.watchers:
            watcher.stop()
        # Threads are daemon, will die when main exits, but polite stopping is good

    def start(self):
        """Start the orchestration loop."""
        self.logger.info("Starting Orchestrator...", interval=self.poll_interval)
        vault.ensure_structure()
        if not self._acquire_instance_lock():
            return
        self.running = True

        try:
            # Heartbeat thread so the UI has a reliable liveness signal.
            threading.Thread(target=self._heartbeat_loop, daemon=True).start()

            # Start Watchers
            self.start_watchers()

            while self.running:
                try:
                    self.run_cycle()
                except KeyboardInterrupt:
                    self.logger.info("Stopping Orchestrator (KeyboardInterrupt)")
                    self.running = False
                except Exception as e:
                    self.logger.error(f"Error in orchestrator cycle: {str(e)}")

                time.sleep(self.poll_interval)
        finally:
            self.stop_watchers()
            self._release_instance_lock()

    def run_cycle(self):
        """Single coordination cycle."""
        current_time = time.time()
        self._write_heartbeat()
        
        # 1. Prioritize approvals so human-approved actions execute quickly (Local only).
        if self.agent_role == "local":
            # Policy-controlled auto-approval for low-risk scheduled items (e.g., scheduled social posts).
            self._auto_approve_pending()
            self.check_approvals()

        # 2. Check for Pending Actions (Inbox processing)
        self.check_needs_action()

        # 3. Check for Handover Drafts (US1: Cloud-to-Local)
        self.check_handovers()

        # 4. Check for Active Plans (Execution monitoring)
        self.check_active_plans()

        # 5. Odoo Sync is now handled by OdooWatcher thread

        # 6. Watchdog / Health Check (Every 60s)
        if current_time - self.last_health_check > 60:
            self.watchdog.check_health()
            self.last_health_check = current_time

        # 7. Dashboard Update (Every 30s)
        if current_time - self.last_dashboard_update > 30:
            # Platinum: single-writer rule for Dashboard.md (Local only).
            if self.agent_role == "local":
                self.update_dashboard()
            self.last_dashboard_update = current_time

    def check_needs_action(self, max_items=None):
        """Look for new files in Needs_Action/"""
        actions = sorted(vault.list_files_recursive("needs_action", "*.md"), key=lambda p: p.name)
        if not actions:
            return

        owned_actions = []
        for action_file in actions:
            meta = self._read_action_metadata(action_file)
            if self._action_owned_by_role(meta):
                owned_actions.append(action_file)

        if not owned_actions:
            return

        if max_items is None:
            max_items = self.max_needs_action_per_cycle
        selected_actions = owned_actions
        if isinstance(max_items, int) and max_items > 0:
            selected_actions = owned_actions[:max_items]

        if len(owned_actions) > len(selected_actions):
            self.logger.info(
                f"Needs_Action backlog detected: processing {len(selected_actions)}/{len(owned_actions)} this cycle"
            )

        for action_file in selected_actions:
            self.logger.info(f"Processing action file: {action_file.name}")

            # Platinum: claim-by-move rule. First agent to move from Needs_Action -> In_Progress owns it.
            claimed_file = self._claim_action_file(action_file)
            if not claimed_file:
                continue

            # Generate Plan
            plan_file = self.plan_manager.create_plan_from_action(claimed_file)

            if plan_file:
                self.logger.info(f"Plan created: {plan_file}")

                # Platinum: Cloud drafts (write Pending_Approval) but never executes.
                if self.agent_role == "cloud":
                    self._create_drafts_for_claimed_action(claimed_file)

                # Keep the claimed file in In_Progress/<agent>/ until the plan is completed.
                # Completion is detected in check_active_plans() and/or after approved execution.
                self.recent_activity.append(f"Planned task: {claimed_file.name}")
            else:
                 self.logger.error(f"Failed to create plan for {action_file.name}")
                 # Graceful degradation: quarantine/queue for manual review instead of losing ownership.
                 try:
                     queued = vault.move_file_safe(claimed_file, "recovery_queue")
                     self.logger.log_action(
                         action_type="plan_failed",
                         result="failure",
                         target=str(queued),
                         details={"reason": "plan_generation_failed", "agent_id": self.agent_id},
                     )
                 except Exception:
                     pass

    def _create_drafts_for_claimed_action(self, claimed_file: Path) -> None:
        """Cloud-only: create Pending_Approval draft files for actions that require HITL."""
        try:
            raw = vault.read_file(claimed_file)
            parts = raw.split("---", 2)
            if len(parts) < 3:
                return
            meta = yaml.safe_load(parts[1]) or {}
            action_type = str(meta.get("type", "")).strip().lower()
            action_id = str(meta.get("id") or claimed_file.stem)

            if action_type == "email":
                approval_path = self.draft_manager.draft_email_reply(claimed_file)
                if approval_path:
                    self._write_signal(f"Drafted email approval: {approval_path.name}")
                return

            if action_type == "social":
                metadata = meta.get("metadata") or {}
                platform = str(metadata.get("platform") or meta.get("platform") or "").strip().lower()
                domain = str(meta.get("domain") or "").strip().lower() or "general"
                auto_approve = bool(metadata.get("auto_approve") or meta.get("auto_approve") or False)
                prompt_text = parts[2].strip()
                if platform:
                    approval_path = self.draft_manager.draft_social_post(
                        platform,
                        prompt_text,
                        source_action_id=action_id,
                        domain=domain,
                        auto_approve=auto_approve,
                    )
                    if approval_path:
                        self._write_signal(f"Drafted {platform} post approval: {approval_path.name}")
                return

        except Exception as exc:
            # Never crash orchestration for draft issues.
            self.logger.warning(f"Draft creation failed for {claimed_file.name}: {exc}")

    def _write_signal(self, summary: str) -> None:
        """Cloud writes signals; Local merges them into Dashboard.md (Platinum)."""
        try:
            vault.ensure_structure()
            ts = int(time.time() * 1000)
            filename = f"{ts}_signal_{self.agent_id}.md"
            path = vault.dirs["signals"] / filename
            path.write_text(f"{summary}\n", encoding="utf-8")
        except Exception as exc:
            self.logger.warning(f"Failed to write signal: {exc}")

    def _claim_action_file(self, action_file: Path) -> Optional[Path]:
        """Claim an action by moving it into In_Progress/<agent_id>/ (atomic on same filesystem)."""
        try:
            if not action_file.exists():
                return None

            agent_dir = vault.dirs["in_progress"] / self.agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            dest = agent_dir / action_file.name

            # Avoid name collisions if we crash and restart.
            if dest.exists():
                timestamp = int(time.time())
                dest = agent_dir / f"{action_file.stem}_{timestamp}{action_file.suffix}"

            action_file.rename(dest)
            self.logger.log_action(
                action_type="claim_action",
                result="success",
                target=str(dest),
                details={"agent_id": self.agent_id, "role": self.agent_role},
            )
            return dest
        except Exception as exc:
            self.logger.error(f"Failed to claim {action_file.name}: {exc}")
            return None

    def _claim_decision_file(self, decision_file: Path, decision_kind: str) -> Optional[Path]:
        """
        Claim an Approved/Rejected item by moving it into an in-progress claim folder.

        This prevents duplicate execution when multiple orchestrator processes are accidentally running.
        """
        try:
            if not decision_file.exists():
                return None
            claims_dir = vault.dirs["in_progress"] / self.agent_id / "approval_claims" / decision_kind
            claims_dir.mkdir(parents=True, exist_ok=True)
            dest = claims_dir / decision_file.name
            if dest.exists():
                dest = claims_dir / f"{decision_file.stem}_{int(time.time())}{decision_file.suffix}"
            decision_file.rename(dest)
            return dest
        except FileNotFoundError:
            return None
        except Exception as exc:
            self.logger.warning(f"Failed to claim {decision_kind} item {decision_file.name}: {exc}")
            return None

    def check_approvals(self):
        """Check for state changes in approvals."""
        # Check Approved/ folder for items ready to execute
        approved = vault.list_files_recursive("approved", "*.md")
        approved.extend(vault.list_files_recursive("approved", "*.yaml"))
        approved_names = {p.name for p in approved}
        for key in list(self.approval_retry_state.keys()):
            if key not in approved_names:
                self.approval_retry_state.pop(key, None)
        
        for app_file in approved:
            approval_name = app_file.name
            try:
                retry_state = self.approval_retry_state.get(approval_name, {})
                next_retry_at = retry_state.get("next_retry_at", 0)
                if next_retry_at and time.time() < next_retry_at:
                    continue

                claimed_file = self._claim_decision_file(app_file, "approved")
                if not claimed_file:
                    continue

                self.logger.info(f"Found approved item: {approval_name}")
                processed = self.approval_manager.process_approved(claimed_file)
                if not processed:
                    if not self.approved_retry_enabled:
                        self.approval_retry_state.pop(approval_name, None)
                        try:
                            moved = vault.move_file_safe(claimed_file, "recovery_queue")
                            self.logger.warning(
                                f"Approved item execution failed; moved to Recovery_Queue for manual review: {approval_name}"
                            )
                            self.logger.log_action(
                                action_type="approved_execution_failed",
                                result="failure",
                                target=str(moved),
                                details={"source_file": str(app_file), "auto_retry": False},
                                approval_status="approved",
                                approved_by="human",
                            )
                        except Exception as move_err:
                            self.logger.error(
                                f"Approved item execution failed and move to Recovery_Queue failed: {approval_name}: {move_err}"
                            )
                        continue

                    previous_count = int(retry_state.get("count", 0))
                    count = previous_count + 1
                    delay_seconds = min(600, 30 * count)
                    self.approval_retry_state[approval_name] = {
                        "count": count,
                        "next_retry_at": time.time() + delay_seconds,
                    }
                    try:
                        retry_dest = app_file.parent / approval_name
                        if retry_dest.exists():
                            retry_dest = app_file.parent / f"{app_file.stem}_{int(time.time())}{app_file.suffix}"
                        claimed_file.rename(retry_dest)
                    except Exception as move_err:
                        self.logger.error(
                            f"Failed to restore approved item for retry ({approval_name}): {move_err}"
                        )
                    self.logger.warning(
                        f"Approved item execution failed, retrying in {delay_seconds}s: {approval_name}"
                    )
                    continue
                self.approval_retry_state.pop(approval_name, None)
                # Move to Done to stop processing
                moved = self._move_file_to_done_safe(claimed_file)
                if moved:
                    self.recent_activity.append(f"Executed approved: {approval_name}")
            except Exception as e:
                self.logger.error(f"Error processing approved item {approval_name}: {e}")

        # Check Rejected/ folder for items to cancel
        rejected = vault.list_files_recursive("rejected", "*.md")
        rejected.extend(vault.list_files_recursive("rejected", "*.yaml"))
        
        for rej_file in rejected:
            rejected_name = rej_file.name
            try:
                claimed_file = self._claim_decision_file(rej_file, "rejected")
                if not claimed_file:
                    continue

                self.logger.info(f"Found rejected item: {rejected_name}")
                processed = self.approval_manager.process_rejected(claimed_file)
                if not processed:
                    self.logger.warning(
                        f"Rejected item handling failed, keeping for retry: {rejected_name}"
                    )
                    try:
                        retry_dest = rej_file.parent / rejected_name
                        if retry_dest.exists():
                            retry_dest = rej_file.parent / f"{rej_file.stem}_{int(time.time())}{rej_file.suffix}"
                        claimed_file.rename(retry_dest)
                    except Exception as move_err:
                        self.logger.error(
                            f"Failed to restore rejected item for retry ({rejected_name}): {move_err}"
                        )
                    continue
                # Move to Done
                moved = self._move_file_to_done_safe(claimed_file)
                if moved:
                    self.recent_activity.append(f"Rejected task: {rejected_name}")
            except Exception as e:
                self.logger.error(f"Error processing rejected item {rejected_name}: {e}")

    def _auto_approve_pending(self) -> None:
        """
        Auto-approve only explicitly-marked, low-risk items.

        Hackathon permission-boundary example:
        - Social media: scheduled posts may be auto-approved

        This is disabled by default. Enable with AUTO_APPROVAL_ENABLED=true.
        """
        if os.getenv("AUTO_APPROVAL_ENABLED", "false").lower() != "true":
            return

        pending = vault.list_files_recursive("pending_approval", "*.md")
        if not pending:
            return

        for p in pending:
            try:
                raw = vault.read_file(p)
                parts = raw.split("---", 2)
                if len(parts) < 3:
                    continue
                meta = yaml.safe_load(parts[1]) or {}
                if not meta.get("auto_approve"):
                    continue

                action = str(meta.get("action") or meta.get("action_type") or "").strip().lower()
                platform = str(meta.get("platform") or "").strip().lower()
                if action != "social_post" or platform not in {"linkedin", "twitter", "facebook", "instagram", "whatsapp"}:
                    continue

                domain = str(meta.get("domain") or "").strip().lower() or None
                dest_dir = vault.get_domain_dir("approved", domain)
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / p.name
                if dest.exists():
                    dest = dest_dir / f"{p.stem}_{int(time.time())}{p.suffix}"
                p.rename(dest)
                self.logger.log_action(
                    action_type="auto_approve",
                    result="success",
                    target=str(dest),
                    details={"platform": platform, "domain": domain or "general"},
                    approval_status="approved",
                    approved_by="policy",
                )
                self.recent_activity.append(f"Auto-approved {platform}: {p.name}")
            except Exception:
                continue

    def check_handovers(self):
        """Check for cloud handover drafts (US1)."""
        drafts = self.local_approval_handler.scan_pending_drafts()
        if drafts:
            self.logger.info(f"Found {len(drafts)} pending cloud drafts")
            # In production, we might want to notify the user via a different channel
            # For now, we just log it and they will see it in Dashboard/Obsidian
            for draft in drafts:
                # We don't auto-process here to maintain HITL
                # The user will move them to Approved/ manually or via manage-approval skill
                pass

    def check_active_plans(self):
        """Monitor running plans and check for completion markers."""
        # Check active plans in Plans/ (recursive to support domain subfolders)
        plans = vault.list_files_recursive("plans", "*.md")
        for plan_file in plans:
            try:
                content = vault.read_file(plan_file)
                parts = content.split("---", 2)
                meta = {}
                body = content
                if len(parts) >= 3:
                    try:
                        meta = yaml.safe_load(parts[1]) or {}
                        body = parts[2]
                    except Exception:
                        meta = {}
                        body = content

                status = str(meta.get("status") or "").strip().lower()
                promise_complete = "<promise>TASK_COMPLETE</promise>" in body

                # If plan marked as complete, move to Done and also complete the originating action.
                if promise_complete or status == "completed":
                    self.logger.info(f"Plan {plan_file.name} completed, moving to done.")

                    action_id = str(meta.get("action_id") or meta.get("action_ref") or "").strip()
                    if action_id:
                        self._complete_action_files(action_id)

                    vault.move_file_safe(plan_file, "done")
                    self.recent_activity.append(f"Completed plan: {plan_file.name}")
            except Exception as e:
                self.logger.error(f"Error checking plan {plan_file.name}: {e}")

    def _complete_action_files(self, action_id: str) -> None:
        """Move any matching in-progress action files into Done/ (Platinum state machine)."""
        if not action_id:
            return
        try:
            candidates = vault.list_files_recursive("in_progress", f"*{action_id}*.md")
            for p in candidates:
                try:
                    vault.move_file_safe(p, "done")
                except Exception:
                    continue
        except Exception:
            return

    def _move_file_to_done_safe(self, file_path: Path) -> bool:
        """Move file to Done/ while tolerating name collisions."""
        try:
            done_target = vault.dirs["done"] / file_path.name
            if done_target.exists():
                timestamp = int(time.time())
                done_target = vault.dirs["done"] / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            file_path.rename(done_target)
            return True
        except Exception as e:
            self.logger.error(f"Failed moving {file_path.name} to Done: {e}")
            return False

    def sync_odoo(self):
        """Perform daily Odoo accounting sync."""
        self.logger.info("Starting scheduled Odoo accounting sync...")
        try:
            script_path = Path(".claude/skills/odoo-accounting/scripts/main_operation.py")
            if script_path.exists():
                import subprocess
                # Use current python executable and correct command structure
                subprocess.run([sys.executable, str(script_path), "sync"], check=True)
                self.logger.info("Odoo sync completed successfully")
                self.recent_activity.append("Synced Odoo accounting")
            else:
                self.logger.warning("Odoo sync script not found")
        except Exception as e:
            self.logger.error(f"Odoo sync failed: {e}")

    def update_dashboard(self):
        """Update the dashboard with current system status."""
        try:
            # Gather watcher status
            watchers_status = {}
            for watcher in self.watchers:
                status = "Running" if watcher.running else "Stopped"
                watchers_status[watcher.name] = status

            # Count pending actions
            pending_actions = vault.list_files_recursive("needs_action", "*.md")
            pending_count = len(pending_actions) if pending_actions else 0

            # Merge cloud signals into the dashboard (single-writer rule: Local only)
            signals = []
            signal_files = sorted(vault.list_files_recursive("signals", "*.md"), key=lambda p: p.name)
            for sig_path in signal_files:
                try:
                    raw = vault.read_file(sig_path).strip()
                    preview = raw.splitlines()[0][:160] if raw else ""
                    signals.append(f"{sig_path.name}: {preview}")
                    # Mark signal as merged by moving to Done/.
                    vault.move_file_safe(sig_path, "done")
                except Exception:
                    continue

            # Update dashboard
            self.dashboard_manager.update_status(
                watchers_status=watchers_status,
                pending_count=pending_count,
                recent_activity=self.recent_activity,
                signals=signals,
                errors=[]
            )

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.start()
