"""
Central Orchestrator.

This is the main brain of the Functional Assistant.
It monitors the vault (Needs_Action) for new files,
triggers the planning process, and oversees execution.
"""

import time
import sys
import threading
from pathlib import Path
from src.lib.logging import get_logger
from src.lib.vault import vault

# Import Watchers
from src.watchers.gmail import GmailWatcher 
from src.watchers.whatsapp import WhatsAppWatcher
from src.watchers.linkedin import LinkedInWatcher

# Import Plan Manager & Approval Manager
from src.orchestration.plan_manager import PlanManager
from src.orchestration.approval_manager import ApprovalManager
from src.handlers.local_approval import LocalApprovalHandler
from src.orchestration.watchdog import Watchdog
from src.orchestration.dashboard_manager import DashboardManager
from src.orchestration.ralph_loop import RalphLoopManager

class Orchestrator:
    def __init__(self):
        self.logger = get_logger("orchestrator")
        self.running = False
        self.poll_interval = 5 # Seconds - fast poll for local file changes

        # Initialize watchers
        self.watchers = [
            GmailWatcher(interval=60), 
            WhatsAppWatcher(interval=60),
            LinkedInWatcher(interval=300)
        ]
        self.watcher_threads = []

        # Initialize Managers
        self.plan_manager = PlanManager()
        self.approval_manager = ApprovalManager()
        self.local_approval_handler = LocalApprovalHandler(str(vault.root))
        self.watchdog = Watchdog()
        self.dashboard_manager = DashboardManager()
        self.ralph_manager = RalphLoopManager()
        self.ralph_manager.integrate_with_orchestrator(self)
        
        self.last_health_check = 0
        self.last_dashboard_update = 0
        self.last_odoo_sync = 0
        self.recent_activity = []

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
        self.running = True

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

        self.stop_watchers()

    def run_cycle(self):
        """Single coordination cycle."""
        # 1. Check for Pending Actions (Inbox processing)
        self.check_needs_action()

        # 2. Check for Pending Approvals (State changes)
        self.check_approvals()

        # 3. Check for Handover Drafts (US1: Cloud-to-Local)
        self.check_handovers()

        # 4. Check for Active Plans (Execution monitoring)
        self.check_active_plans()

        # 5. Odoo Daily Sync (Every 24h or manual trigger)
        current_time = time.time()
        if current_time - self.last_odoo_sync > 86400: # 24 hours
            self.sync_odoo()
            self.last_odoo_sync = current_time

        # 6. Watchdog / Health Check (Every 60s)
        if current_time - self.last_health_check > 60:
            self.watchdog.check_health()
            self.last_health_check = current_time

        # 7. Dashboard Update (Every 30s)
        if current_time - self.last_dashboard_update > 30:
            self.update_dashboard()
            self.last_dashboard_update = current_time

    def check_needs_action(self):
        """Look for new files in Needs_Action/"""
        actions = vault.list_files("needs_action", "*.md")
        if not actions:
            return

        for action_file in actions:
            self.logger.info(f"Processing action file: {action_file.name}")

            # Generate Plan
            plan_file = self.plan_manager.create_plan_from_action(action_file)

            if plan_file:
                self.logger.info(f"Plan created: {plan_file}")

                # Move action to 'done' to avoid reprocessing
                try:
                    vault.move_file(action_file, "done")
                    self.recent_activity.append(f"Planned task: {action_file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to move action file {action_file.name}: {e}")
            else:
                 self.logger.error(f"Failed to create plan for {action_file.name}")

    def check_approvals(self):
        """Check for state changes in approvals."""
        # Check Approved/ folder for items ready to execute
        approved = vault.list_files("approved", "*.md")
        approved.extend(vault.list_files("approved", "*.yaml"))
        
        for app_file in approved:
            self.logger.info(f"Found approved item: {app_file.name}")
            self.approval_manager.process_approved(app_file)
            # Move to Done to stop processing
            vault.move_file(app_file, "done")
            self.recent_activity.append(f"Executed approved: {app_file.name}")

        # Check Rejected/ folder for items to cancel
        rejected = vault.list_files("rejected", "*.md")
        rejected.extend(vault.list_files("rejected", "*.yaml"))
        
        for rej_file in rejected:
            self.logger.info(f"Found rejected item: {rej_file.name}")
            self.approval_manager.process_rejected(rej_file)
            # Move to Done
            vault.move_file(rej_file, "done")
            self.recent_activity.append(f"Rejected task: {rej_file.name}")

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
        # Check active plans in Plans/
        plans = vault.list_files("plans", "*.md")
        for plan_file in plans:
            try:
                content = vault.read_file(plan_file)
                # If plan marked as TASK_COMPLETE, move to done
                if "<promise>TASK_COMPLETE</promise>" in content or "status: \"completed\"" in content:
                    self.logger.info(f"Plan {plan_file.name} completed, moving to done.")
                    vault.move_file(plan_file, "done")
                    self.recent_activity.append(f"Completed plan: {plan_file.name}")
            except Exception as e:
                self.logger.error(f"Error checking plan {plan_file.name}: {e}")

    def sync_odoo(self):
        """Perform daily Odoo accounting sync."""
        self.logger.info("Starting scheduled Odoo accounting sync...")
        try:
            script_path = Path(".claude/skills/odoo-accounting/scripts/main_operation.py")
            if script_path.exists():
                import subprocess
                subprocess.run(["python3", str(script_path), "--action", "sync"], check=True)
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
            pending_actions = vault.list_files("needs_action", "*.md")
            pending_count = len(pending_actions) if pending_actions else 0

            # Update dashboard
            self.dashboard_manager.update_status(
                watchers_status=watchers_status,
                pending_count=pending_count,
                recent_activity=self.recent_activity,
                errors=[]
            )

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.start()
