"""Base watcher abstract class for all input source monitors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional
import time
from datetime import datetime

from src.utils.logger import setup_logger, get_daily_log_file
from src.utils.yaml_parser import serialize_frontmatter


class BaseWatcher(ABC):
    """Abstract base class for all watchers."""

    def __init__(self, vault_path: Path, check_interval: int = 60):
        """
        Initialize watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            check_interval: Seconds between checks
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.processed_ids = set()  # Track processed items to avoid duplicates
        self.running = False

        # Set up logging
        log_file = get_daily_log_file(self.vault_path, "watcher")
        self.logger = setup_logger(
            f"{self.__class__.__name__}",
            log_file=log_file,
            console=True
        )

        # Ensure Needs_Action folder exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> List[Dict]:
        """
        Check input source for new items.

        Returns:
            List of dicts with item metadata. Each dict should contain:
            - id: Unique identifier for the item
            - type: Type of item (email, file, etc.)
            - source: Source identifier
            - priority: Priority level (high, medium, low)
            - content: Item content or description
            - timestamp: ISO 8601 timestamp
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict) -> Path:
        """
        Create action file in Needs_Action folder.

        Args:
            item: Item metadata from check_for_updates()

        Returns:
            Path to created action file
        """
        pass

    def _generate_action_filename(self, item_type: str, source: str, timestamp: str) -> str:
        """
        Generate standardized action file name.

        Args:
            item_type: Type of item (email, file, manual)
            source: Source identifier
            timestamp: ISO 8601 timestamp

        Returns:
            Filename in format: {TYPE}_{SOURCE}_{TIMESTAMP}.md
        """
        # Convert timestamp to filename-safe format
        safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
        return f"{item_type.upper()}_{source}_{safe_timestamp}.md"

    def _create_action_file_content(
        self,
        item_type: str,
        source: str,
        timestamp: str,
        priority: str,
        content: str,
        suggested_actions: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Create standardized action file content with YAML frontmatter.

        Args:
            item_type: Type of item (email, file, manual)
            source: Source identifier
            timestamp: ISO 8601 timestamp
            priority: Priority level (high, medium, low)
            content: Main content
            suggested_actions: List of suggested actions
            notes: Additional notes

        Returns:
            Complete Markdown content with frontmatter
        """
        frontmatter = {
            "type": item_type,
            "source": source,
            "timestamp": timestamp,
            "priority": priority,
            "status": "pending",
            "created_by": "watcher",
        }

        body_parts = [f"## Content\n\n{content}"]

        if suggested_actions:
            actions_text = "\n".join([f"- [ ] {action}" for action in suggested_actions])
            body_parts.append(f"\n## Suggested Actions\n\n{actions_text}")

        if notes:
            body_parts.append(f"\n## Notes\n\n{notes}")

        body = "\n".join(body_parts)
        return serialize_frontmatter(frontmatter, body)

    def run(self):
        """Main loop: check for updates and create action files."""
        self.running = True
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")
        self.logger.info(f"Vault path: {self.vault_path}")

        while self.running:
            try:
                # Check for new items
                items = self.check_for_updates()

                # Process new items
                for item in items:
                    item_id = item.get("id")
                    if item_id and item_id not in self.processed_ids:
                        try:
                            action_file = self.create_action_file(item)
                            self.processed_ids.add(item_id)
                            self.logger.info(
                                f"Created action file: {action_file.name}",
                                extra={"item_id": item_id, "priority": item.get("priority")}
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Failed to create action file for item {item_id}: {e}",
                                exc_info=True
                            )

                # Wait before next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
                self.stop()
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(self.check_interval)

    def stop(self):
        """Stop the watcher."""
        self.running = False
        self.logger.info(f"Stopping {self.__class__.__name__}")

    def get_status(self) -> Dict:
        """
        Get current watcher status.

        Returns:
            Dict with status information
        """
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "processed_count": len(self.processed_ids),
            "vault_path": str(self.vault_path),
        }
