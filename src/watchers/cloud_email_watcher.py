"""Cloud Email Watcher - Draft-only mode for offline email processing."""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import os
import time

from src.watchers.base_watcher import BaseWatcher


class CloudEmailWatcher(BaseWatcher):
    """Cloud-based email watcher that creates DRAFT actions for handover to local agent."""

    def __init__(
        self,
        vault_path: Path,
        check_interval: int = 180,  # 3 minutes for cloud env
        draft_template_path: Optional[str] = None
    ):
        """
        Initialize cloud email watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            check_interval: Seconds between checks
            draft_template_path: Path to draft reply template
        """
        super().__init__(vault_path, check_interval)

        self.draft_template_path = Path(draft_template_path) if draft_template_path else None
        self.cloud_agent_id = os.getenv('CLOUD_AGENT_ID', 'cloud-agent-001')

        self.logger.info(f"Cloud Email Watcher initialized (agent: {self.cloud_agent_id})")

    def check_for_updates(self) -> List[Dict]:
        """
        Check email sources that would normally exist in cloud environment.

        Returns:
            List of dicts with item metadata
        """
        self.logger.debug("Checking for email updates (draft mode)")

        # In cloud environment, we would check:
        # - Email API/Webhook endpoints
        # - Message queues (AWS SQS, GCP Pub/Sub)
        # - Database for pending emails

        # For simulation: Check Needs_Action for email actions that need drafting
        found_items = []

        try:
            # Scan for action files marked for cloud processing
            for action_file in self.needs_action.glob("*.yaml"):
                try:
                    with open(action_file, 'r') as f:
                        content = f.read()

                    # Check if this is an email-related action
                    if 'type: email' in content or 'EMAIL' in content.upper():
                        action_id = self._extract_action_id(action_file)
                        if action_id and action_id not in self.processed_ids:
                            self.logger.info(f"Found email action: {action_id}")

                            # Add to found items
                            found_items.append({
                                'id': action_id,
                                'type': 'email',
                                'source': self.cloud_agent_id,
                                'priority': 'high',  # Email is typically high priority
                                'content': f"Email action requires draft: {action_file}",
                                'timestamp': datetime.utcnow().isoformat(),
                                'action_file': str(action_file)
                            })
                except Exception as e:
                    self.logger.warning(f"Error reading {action_file}: {e}")

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")

        return found_items

    def _extract_action_id(self, action_file: Path) -> Optional[str]:
        """Extract action_id from YAML frontmatter."""
        try:
            with open(action_file, 'r') as f:
                content = f.read()

            if '---' in content:
                frontmatter = content.split('---')[1]
                # Simple parsing, as YAML might not be available yet
                for line in frontmatter.split('\n'):
                    if 'action_id:' in line or 'action_id :' in line:
                        return line.split(':')[1].strip()
        except Exception:
            pass
        return None

    def create_action_file(self, item: Dict) -> Path:
        """
        Create DRAFT action in Needs_Action folder.

        Args:
            item: Dict with item metadata from check_for_updates

        Returns:
            Path to created action file
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        action_id = f"email_draft_{timestamp}"

        # Mark as cloud-processed to avoid re-processing
        self.processed_ids.add(item['id'])

        # Create the action content
        action_content = f"""---
action_id: {action_id}
type: email
source: {item['source']}
priority: draft_requires_approval
requires_handover: true
cloud_draft: true
parent_action: {item['id']}
timestamp: {item['timestamp']}
title: Draft Email Response
---

## Email Draft Summary

**Original Action**: {item['content']}

**Status**: Draft created by cloud agent - requires local agent approval

## Draft Content

This email response was drafted by the cloud agent in **DRAFT MODE**.

**DRAFT_MODE: true**

**IMPORTANT**: This draft HAS NOT been sent. It requires review and approval by the local agent.

### Next Steps

1. Review the email draft content
2. Verify recipient and content accuracy
3. Approve for sending (local agent will handle actual delivery)
4. If rejected, provide feedback for cloud agent improvement

### Cloud Agent Notes

- **Agent ID**: {self.cloud_agent_id}
- **Draft Timestamp**: {datetime.utcnow().isoformat()}
- **Mode**: Cloud (DRAFT ONLY)

***

**HANDOVER REQUIRED** - This email draft needs local agent review and approval before sending.
"""

        filename = f"{action_id}.yaml"
        action_file = self.needs_action / filename

        # Write action file
        with open(action_file, 'w') as f:
            f.write(action_content)

        self.logger.info(f"Created DRAFT action: {action_file}")

        return action_file

    def run(self):
        """Main loop for the cloud email watcher."""
        self.logger.info(f"Starting Cloud Email Watcher (check interval: {self.check_interval}s)")

        self.running = True
        while self.running:
            try:
                items = self.check_for_updates()

                for item in items:
                    self.logger.info(f"Processing item: {item['id']}")
                    action_file = self.create_action_file(item)
                    self.logger.info(f"Created DRAFT action: {action_file}")

                # Sleep for check interval
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.logger.info("Stopping Cloud Email Watcher...")
                self.running = False
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Sleep on error before retry


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cloud_email_watcher.py <vault_path>")
        sys.exit(1)

    vault_path = Path(sys.argv[1])

    # Create and run watcher
    watcher = CloudEmailWatcher(vault_path, check_interval=180)
    watcher.run()
