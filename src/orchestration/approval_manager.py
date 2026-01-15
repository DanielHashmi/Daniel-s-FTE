"""
Approval Manager.

Handles creating approval request files and processing results.
"""

import time
import hashlib
from typing import Dict, Any
from src.lib.logging import get_logger
from src.lib.vault import vault

class ApprovalManager:
    def __init__(self):
        self.logger = get_logger("approval_manager")

    def create_approval_request(self,
                              action_type: str,
                              context: Dict[str, Any],
                              details: str) -> str:
        """
        Create a file in Pending_Approval/
        """
        timestamp = int(time.time())
        unique_str = f"approval-{timestamp}-{str(context)}"
        appr_id = f"appr_{hashlib.md5(unique_str.encode()).hexdigest()[:8]}"

        filename = f"{timestamp}_{action_type}_approval.md"

        yaml_content = f"""---
id: "{appr_id}"
type: "approval"
action_type: "{action_type}"
created: "{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
status: "pending"
context:
"""
        for k, v in context.items():
            yaml_content += f"  {k}: \"{v}\"\n"

        yaml_content += "---\n\n"
        yaml_content += details

        # Write manually to Pending_Approval
        path = vault.dirs["pending_approval"] / filename
        with open(path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        self.logger.log_action(
            action_type="create_approval",
            result="success",
            target=str(path),
            details={"appr_id": appr_id}
        )

        return filename

    def process_approved(self, filepath):
        """Handle logic when a file appears in Approved/"""
        try:
            # Read file to get context
            content = vault.read_file(filepath)

            # Log the approval decision
            self.logger.log_approval_decision(
                decision="approved",
                action_file=str(filepath),
                reason="Human approved via manage-approval skill"
            )

            # Execute the action (or trigger orchestrator to do it)
            # For now, just log that it would be executed
            self.logger.info(f"Approved action ready for execution: {filepath.name}")

        except Exception as e:
            self.logger.error(f"Error processing approved file {filepath}: {e}")

    def process_rejected(self, filepath):
        """Handle logic when a file appears in Rejected/"""
        try:
            # Read file to get context
            content = vault.read_file(filepath)

            # Log the rejection decision
            self.logger.log_approval_decision(
                decision="rejected",
                action_file=str(filepath),
                reason="Human rejected via manage-approval skill"
            )

            # Cancel the plan
            self.logger.info(f"Rejected action cancelled: {filepath.name}")

        except Exception as e:
            self.logger.error(f"Error processing rejected file {filepath}: {e}")
