"""
Dashboard Manager.

Updates the AI Employee Dashboard with system status and activity.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from src.lib.logging import get_logger
from src.lib.vault import vault

class DashboardManager:
    def __init__(self):
        self.logger = get_logger("dashboard_manager")
        self.dashboard_path = vault.root / "Dashboard.md"

    def update_status(self,
                     watchers_status: Dict[str, str],
                     pending_count: int,
                     recent_activity: List[str],
                     errors: List[str] = None):
        """
        Update the dashboard with current system status.

        Args:
            watchers_status: Dict of watcher names to their status
            pending_count: Number of pending actions
            recent_activity: List of recent activity strings
            errors: List of error messages (optional)
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()

            # Build dashboard content
            content = f"""# AI Employee Dashboard

**Last Updated**: {timestamp}

## System Status (Silver Tier)

"""
            # Watchers status
            for watcher_name, status in watchers_status.items():
                content += f"- **{watcher_name}**: {status}\n"

            content += f"\n## Pending Actions\n\n**Count**: {pending_count}\n\n"

            if pending_count == 0:
                content += "All actions have been processed. No pending items.\n"

            # Recent Activity
            content += "\n## Recent Activity\n\n"
            if recent_activity:
                for activity in recent_activity[-10:]:  # Last 10 items
                    content += f"- {activity}\n"
            else:
                content += "No recent activity.\n"

            # Errors
            content += "\n## Errors\n\n"
            if errors and len(errors) > 0:
                for error in errors:
                    content += f"- ⚠️ {error}\n"
            else:
                content += "No errors.\n"

            content += "\n---\n\n*Dashboard automatically updated by AI Employee Orchestrator.*\n"

            # Write to dashboard
            with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info("Dashboard updated successfully")

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

    def log_activity(self, activity: str):
        """
        Append an activity to the dashboard's recent activity section.
        This is a lightweight update that doesn't rebuild the entire dashboard.
        """
        # For now, we'll just log it
        # In a production system, we might maintain a separate activity log
        self.logger.info(f"Activity: {activity}")
