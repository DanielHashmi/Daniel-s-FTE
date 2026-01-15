"""
Watchdog.

Monitors system health and restarts processes if needed.
(In this architecture, PM2 handles restarts, so Watchdog focuses on functional health checks
and alerting).
"""

import subprocess
from src.lib.logging import get_logger

class Watchdog:
    def __init__(self):
        self.logger = get_logger("watchdog")

    def check_health(self):
        """Run health checks."""
        # Check PM2 status
        try:
            result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse JSON output to check status of apps
                # For now just log success
                self.logger.info("System health check passed (PM2 active)")
            else:
                self.logger.error("System health check failed: PM2 unreachable")
        except Exception as e:
            self.logger.error(f"Watchdog error: {e}")

if __name__ == "__main__":
    wd = Watchdog()
    wd.check_health()
