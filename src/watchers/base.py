"""
Base Watcher Module.

This defines the contract for all Watchers in the system.
Watchers are responsible for monitoring input channels (Gmail, WhatsApp, etc.)
and converting relevant events into Action Files in the Vault.
"""

import time
import abc
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from src.lib.logging import get_logger
from src.lib.vault import vault

class BaseWatcher(abc.ABC):
    """Abstract base class for all channel watchers."""

    def __init__(self, name: str, interval: int = 60):
        self.name = name
        self.interval = interval
        self.logger = get_logger(name)
        self.running = False

        # Ensure vault structure is ready
        vault.ensure_structure()

    def start(self):
        """Start the monitoring loop."""
        self.logger.info(f"Starting {self.name} watcher...", interval=self.interval)
        self.running = True

        while self.running:
            try:
                self.check_for_updates()
            except Exception as e:
                self.logger.error(f"Error in {self.name} watcher loop: {str(e)}")

            # Simple sleep for poll interval
            time.sleep(self.interval)

    def stop(self):
        """Stop the monitoring loop."""
        self.logger.info(f"Stopping {self.name} watcher...")
        self.running = False

    @abc.abstractmethod
    def check_for_updates(self):
        """
        Poll the channel for new events.
        Must be implemented by concrete classes.
        Should call create_action_file() when relevant events are found.
        """
        pass

    def create_action_file(self,
                          type: str,
                          content: str,
                          metadata: Dict[str, Any],
                          priority: str = "normal") -> str:
        """
        Helper to write a standardized Action File to the Vault.

        Returns:
            str: The filename created.
        """
        # Generate a unique ID
        timestamp = int(time.time())
        unique_str = f"{self.name}-{timestamp}-{str(metadata)}"
        action_id = f"act_{hashlib.md5(unique_str.encode()).hexdigest()[:8]}"

        filename = f"{timestamp}_{self.name}_{type}.md"

        # Determine strict source type from class name or param
        source = self.name.replace("_watcher", "").lower()

        # Construct content variables
        iso_timestamp = datetime.now(timezone.utc).isoformat()

        yaml_frontmatter = f"""---
id: "{action_id}"
type: "{type}"
source: "{source}"
priority: "{priority}"
timestamp: "{iso_timestamp}"
status: "pending"
metadata:
"""
        # Add metadata fields safely
        for k, v in metadata.items():
            # Basic YAML escaping for string values
            if isinstance(v, str):
                v_clean = v.replace('"', '\\"')
                yaml_frontmatter += f"  {k}: \"{v_clean}\"\n"
            else:
                yaml_frontmatter += f"  {k}: {v}\n"

        yaml_frontmatter += "---\n\n"

        full_content = yaml_frontmatter + content

        path = vault.write_action(filename, full_content)

        self.logger.log_action(
            action_type="create_action_file",
            result="success",
            target=str(path),
            details={"action_id": action_id}
        )

        return filename
