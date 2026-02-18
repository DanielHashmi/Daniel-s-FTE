"""
Watchdog.

Monitors system health and restarts processes if needed.
(In this architecture, PM2 handles restarts, so Watchdog focuses on functional health checks
and alerting).
"""

import subprocess
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from src.lib.logging import get_logger
from src.lib.vault import vault

class Watchdog:
    def __init__(self):
        self.logger = get_logger("watchdog")
        self.pm2_app_name = os.getenv("PM2_ORCHESTRATOR_APP", "daniel-fte-orchestrator")
        self.heartbeat_path = vault.dirs["logs"] / "orchestrator_heartbeat.json"
        self.max_stale_seconds = int(os.getenv("WATCHDOG_MAX_HEARTBEAT_STALE_SECONDS", "30"))

    def check_health(self):
        """Run health checks."""
        vault.ensure_structure()

        # 1) Heartbeat freshness (primary health signal for the brain)
        self._check_heartbeat()

        # 2) Check PM2 status (secondary)
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

    def _check_heartbeat(self) -> None:
        try:
            if not self.heartbeat_path.exists():
                self._alert(f"Missing heartbeat file: {self.heartbeat_path}")
                return

            raw = self.heartbeat_path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(raw) if raw.strip().startswith("{") else {}
            ts = str(data.get("timestamp") or "").strip()

            # Heartbeat timestamp is written in UTC Z format.
            hb_time = None
            if ts.endswith("Z"):
                try:
                    hb_time = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                except ValueError:
                    hb_time = None

            if not hb_time:
                # Fallback: file mtime
                hb_time = datetime.fromtimestamp(self.heartbeat_path.stat().st_mtime, tz=timezone.utc)

            age = (datetime.now(timezone.utc) - hb_time).total_seconds()
            if age <= self.max_stale_seconds:
                return

            self._alert(f"Orchestrator heartbeat stale ({age:.0f}s). Attempting restart via PM2: {self.pm2_app_name}")
            self._restart_pm2_app()

        except Exception as exc:
            self._alert(f"Watchdog heartbeat check failed: {exc}")

    def _restart_pm2_app(self) -> None:
        try:
            subprocess.run(["pm2", "restart", self.pm2_app_name], capture_output=True, text=True)
            self.logger.log_action(
                action_type="watchdog_restart",
                result="success",
                target=self.pm2_app_name,
                details={"reason": "stale_heartbeat"},
            )
        except Exception as exc:
            self.logger.log_action(
                action_type="watchdog_restart",
                result="error",
                target=self.pm2_app_name,
                details={"reason": "stale_heartbeat", "error": str(exc)[:200]},
            )

    def _alert(self, message: str) -> None:
        try:
            ts = int(time.time() * 1000)
            path = vault.dirs["alerts"] / f"{ts}_watchdog.md"
            path.write_text(
                f"# Watchdog Alert\n\nTimestamp: {datetime.now(timezone.utc).isoformat()}\n\n{message}\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        self.logger.warning(message)

if __name__ == "__main__":
    wd = Watchdog()
    wd.check_health()
