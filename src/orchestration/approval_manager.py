"""
Approval Manager.

Handles creating approval request files and processing results.
"""

import time
import hashlib
import yaml
import subprocess
import json
from pathlib import Path
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
            
            # Parse YAML frontmatter
            parts = content.split("---")
            if len(parts) < 3:
                self.logger.error(f"Invalid approval file format: {filepath.name}")
                return

            metadata = yaml.safe_load(parts[1])
            body = parts[2].strip()

            # Log the approval decision
            self.logger.log_approval_decision(
                decision="approved",
                action_file=str(filepath),
                reason="Human approved via file move to Approved/"
            )

            # Execution logic
            action = metadata.get("action") or metadata.get("action_type")
            platform = metadata.get("platform")

            if action == "social_post" and platform == "twitter":
                # Extract content from body
                # The body has headers like ## Content
                lines = body.split("\n")
                content_lines = []
                in_content = False
                for line in lines:
                    if line.startswith("## Content"):
                        in_content = True
                        continue
                    elif line.startswith("##") and in_content:
                        break
                    
                    if in_content:
                        content_lines.append(line)
                
                tweet_text = "\n".join(content_lines).strip()
                if not tweet_text:
                    tweet_text = body.split("\n")[0] # Fallback to first line

                self.logger.info(f"Executing tweet: {tweet_text[:50]}...")
                
                # Call social-mcp
                mcp_path = Path("mcp-servers/social-mcp/index.js")
                if mcp_path.exists():
                    rpc_call = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "call_tool",
                        "params": {
                            "name": "post_to_twitter",
                            "arguments": {"content": tweet_text}
                        }
                    }
                    
                    # Run node command
                    try:
                        result = subprocess.run(
                            ["node", str(mcp_path)],
                            input=json.dumps(rpc_call),
                            text=True,
                            capture_output=True,
                            check=True
                        )
                        self.logger.info(f"Tweet execution result: {result.stdout}")
                    except subprocess.CalledProcessError as e:
                        self.logger.error(f"Tweet execution failed: {e.stderr}")
                else:
                    self.logger.error("social-mcp server not found")

            else:
                self.logger.info(f"Approved action ready for execution (No automatic handler): {filepath.name}")

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
