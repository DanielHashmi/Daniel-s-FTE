import time
import subprocess
import os
import sys
from pathlib import Path
from src.watchers.base import BaseWatcher
from src.lib.logging import get_logger

class OdooWatcher(BaseWatcher):
    def __init__(self, interval: int = 60):
        super().__init__("odoo_watcher", interval)
        self.logger = get_logger("odoo_watcher")
        self.script_path = os.path.join(os.getcwd(), ".claude", "skills", "odoo-accounting", "scripts", "main_operation.py")

    def check_for_updates(self):
        """
        Run Odoo Sync periodically.
        """
        self.run_sync()
        return []

    def run_sync(self):
        try:
            # Check if script exists
            if not os.path.exists(self.script_path):
                self.logger.error(f"Odoo script not found at {self.script_path}")
                return

            self.logger.info("Running Odoo Sync...")
            
            # Using sys.executable to ensure we use the same environment
            cmd = [sys.executable, self.script_path, "sync"]
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                # Log only if interesting or periodically
                if "Synced" in result.stdout:
                    # Parse "Synced N transactions"
                    self.logger.info(f"Odoo Sync Result: {result.stdout.strip()}")
            else:
                self.logger.error(f"Odoo Sync Failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error executing Odoo Sync: {e}")

    def create_action_file(self, item) -> Path:
        return Path("") # Not used
