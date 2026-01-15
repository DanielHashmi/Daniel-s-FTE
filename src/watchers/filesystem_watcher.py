"""File system watcher for monitoring Inbox folder."""

from pathlib import Path
from typing import List, Dict
from datetime import datetime, UTC
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from src.watchers.base_watcher import BaseWatcher


class InboxHandler(FileSystemEventHandler):
    """Handler for file system events in Inbox folder."""

    def __init__(self, watcher: 'FileSystemWatcher'):
        """
        Initialize handler.

        Args:
            watcher: Parent FileSystemWatcher instance
        """
        self.watcher = watcher
        self.pending_files = set()

    def on_created(self, event: FileCreatedEvent):
        """
        Handle file creation events.

        Args:
            event: File creation event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Filter by supported extensions
        supported_extensions = ['.txt', '.md', '.pdf', '.docx', '.csv', '.json']
        if file_path.suffix.lower() not in supported_extensions:
            self.watcher.logger.debug(f"Ignoring unsupported file type: {file_path.name}")
            return

        # Add to pending files (debouncing)
        self.pending_files.add(file_path)
        self.watcher.logger.debug(f"Detected new file: {file_path.name}")


class FileSystemWatcher(BaseWatcher):
    """Watcher for monitoring file system Inbox folder."""

    def __init__(self, vault_path: Path, check_interval: int = 60):
        """
        Initialize file system watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            check_interval: Seconds between checks (not used for event-driven monitoring)
        """
        super().__init__(vault_path, check_interval)
        self.inbox = self.vault_path / "Inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)

        # Set up watchdog observer
        self.observer = Observer()
        self.handler = InboxHandler(self)
        self.observer.schedule(self.handler, str(self.inbox), recursive=False)

    def check_for_updates(self) -> List[Dict]:
        """
        Check Inbox folder for new files.

        Uses both event-driven (watchdog) and polling-based detection
        to work reliably on all systems, including WSL.

        Returns:
            List of file items to process
        """
        items = []

        # Process pending files from event handler (event-driven)
        pending_files = list(self.handler.pending_files)
        self.handler.pending_files.clear()

        # Also scan Inbox folder directly (polling-based, works on WSL)
        # This is a fallback for systems where inotify doesn't work
        supported_extensions = ['.txt', '.md', '.pdf', '.docx', '.csv', '.json']
        for file_path in self.inbox.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                # Skip files in .processed folder
                if '.processed' in str(file_path):
                    continue
                # Add to pending if not already there
                if file_path not in pending_files:
                    pending_files.append(file_path)
                    self.logger.debug(f"Detected file via polling: {file_path.name}")

        for file_path in pending_files:
            if not file_path.exists():
                continue

            # Wait a moment to ensure file is fully written
            time.sleep(0.1)

            try:
                # Read file content
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                # Determine priority based on filename keywords
                priority = self._determine_priority(file_path.name, content)

                # Create item
                item = {
                    "id": file_path.name,
                    "type": "file",
                    "source": "inbox",
                    "priority": priority,
                    "content": f"File: {file_path.name}\n\n{content[:500]}",  # First 500 chars
                    "timestamp": datetime.now(UTC).isoformat(),
                    "suggested_actions": [
                        f"Review file: {file_path.name}",
                        "Process content",
                        "Archive or delete file"
                    ],
                    "notes": f"Detected from Inbox folder. File size: {file_path.stat().st_size} bytes"
                }

                items.append(item)

                # Move file to prevent reprocessing
                archive_path = self.inbox / ".processed" / file_path.name
                archive_path.parent.mkdir(exist_ok=True)
                file_path.rename(archive_path)

            except Exception as e:
                self.logger.error(f"Failed to process file {file_path.name}: {e}", exc_info=True)

        return items

    def _determine_priority(self, filename: str, content: str) -> str:
        """
        Determine priority based on filename and content keywords.

        Args:
            filename: Name of the file
            content: File content

        Returns:
            Priority level (high, medium, low)
        """
        high_keywords = ['urgent', 'asap', 'critical', 'emergency', 'invoice', 'payment']
        medium_keywords = ['important', 'soon', 'review', 'feedback']

        text = (filename + " " + content).lower()

        for keyword in high_keywords:
            if keyword in text:
                return "high"

        for keyword in medium_keywords:
            if keyword in text:
                return "medium"

        return "low"

    def create_action_file(self, item: Dict) -> Path:
        """
        Create action file from file item.

        Args:
            item: File item metadata

        Returns:
            Path to created action file
        """
        filename = self._generate_action_filename(
            item["type"],
            item["source"],
            item["timestamp"]
        )

        content = self._create_action_file_content(
            item["type"],
            item["source"],
            item["timestamp"],
            item["priority"],
            item["content"],
            item.get("suggested_actions"),
            item.get("notes")
        )

        action_file = self.needs_action / filename
        action_file.write_text(content)

        return action_file

    def run(self):
        """Start the file system watcher with event-driven monitoring."""
        self.observer.start()
        self.logger.info("Started watchdog observer for Inbox folder")

        try:
            super().run()
        finally:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Stopped watchdog observer")

    def stop(self):
        """Stop the watcher and observer."""
        super().stop()
        if self.observer.is_alive():
            self.observer.stop()


def main():
    """Main entry point for file system watcher."""
    from src.config import get_config

    config = get_config()
    watcher = FileSystemWatcher(config.vault_path, config.watcher_check_interval)

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    main()
