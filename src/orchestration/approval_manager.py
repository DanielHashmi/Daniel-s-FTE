"""
Approval Manager.

Handles creating approval request files and processing results.
"""

import time
import hashlib
import yaml
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from src.lib.logging import get_logger
from src.lib.vault import vault
import os

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

    def _extract_social_content(self, body: str) -> str:
        """Extract post content from markdown body."""
        lines = body.split("\n")
        content_lines = []
        in_content = False

        for line in lines:
            if line.startswith("## Content"):
                in_content = True
                continue
            if line.startswith("##") and in_content:
                break
            if in_content and line.strip().lower().startswith("*this post requires approval"):
                break
            if in_content:
                content_lines.append(line)

        content = "\n".join(content_lines).strip()
        if content:
            return content

        # Fallback: first non-empty non-note line
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.lower().startswith("*this post requires approval"):
                return stripped
        return ""

    def _extract_json_payload(self, raw_output: str) -> Optional[Dict[str, Any]]:
        """Best-effort extraction of JSON payload from subprocess output."""
        for line in reversed(raw_output.splitlines()):
            candidate = line.strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
        return None

    def _handle_facebook_post(self, metadata: Dict[str, Any], body: str, filepath: Path) -> bool:
        """Handle approved Facebook social post using Qwen + Playwright."""
        brain = str(metadata.get("brain", "qwen")).strip().lower()
        if brain and brain != "qwen":
            self.logger.error(
                f"Facebook post rejected: only Qwen brain is allowed, got '{brain}' for {filepath.name}"
            )
            return False

        prompt = str(metadata.get("qwen_prompt", "")).strip()
        approved_content = self._extract_social_content(body)
        if not prompt and not approved_content:
            self.logger.error(f"Missing qwen_prompt/content for facebook post {filepath.name}")
            return False

        script_path = Path("src/social/facebook_qwen_poster.py")
        if not script_path.exists():
            self.logger.error(f"Facebook poster script not found: {script_path}")
            return False

        # HITL guarantee: post EXACTLY what the human approved.
        # Only generate with Qwen when the file contains no approved content.
        if approved_content:
            cmd = [
                sys.executable,
                str(script_path),
                "--mode",
                "post",
                "--content",
                approved_content,
                "--json",
            ]
        else:
            cmd = [
                sys.executable,
                str(script_path),
                "--mode",
                "generate-and-post",
                "--prompt",
                prompt,
                "--json",
            ]
        if os.getenv("DRY_RUN", "false").lower() == "true":
            cmd.append("--dry-run")
        if os.getenv("FACEBOOK_HEADLESS", "false").lower() == "true":
            cmd.append("--headless")

        self.logger.info(f"Executing Facebook automation command for {filepath.name}")
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            self.logger.error(
                f"Facebook automation failed for {filepath.name}: {process.stderr or process.stdout}"
            )
            return False

        payload = self._extract_json_payload(process.stdout or "")
        if payload and payload.get("success"):
            preview = ""
            generation = payload.get("generation", {})
            if isinstance(generation, dict):
                preview = str(generation.get("generated_content", ""))[:120]

            self.logger.log_action(
                action_type="facebook_post",
                result="success",
                target=str(filepath),
                details={
                    "mode": "qwen_playwright",
                    "dry_run": os.getenv("DRY_RUN", "false").lower() == "true",
                    "generated_preview": preview,
                },
            )
            self.logger.info(f"Facebook post execution successful: {filepath.name}")
            return True

        # If JSON is not parseable but command succeeded, still record success with raw output
        self.logger.log_action(
            action_type="facebook_post",
            result="success",
            target=str(filepath),
            details={
                "mode": "qwen_playwright",
                "dry_run": os.getenv("DRY_RUN", "false").lower() == "true",
                "raw_output_preview": (process.stdout or "").strip()[:200],
            },
        )
        self.logger.info(f"Facebook automation completed with non-JSON output: {filepath.name}")
        return True

    def process_approved(self, filepath) -> bool:
        """Handle logic when a file appears in Approved/"""
        try:
            # Read file to get context
            content = vault.read_file(filepath)
            
            # Parse YAML frontmatter
            parts = content.split("---")
            if len(parts) < 3:
                self.logger.error(f"Invalid approval file format: {filepath.name}")
                return False

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
            platform = str(metadata.get("platform", "")).strip().lower()

            if action in ("social_post", "post") and platform == "facebook":
                return self._handle_facebook_post(metadata, body, filepath)

            elif action in ("social_post", "post") and platform == "twitter":
                # Extract content from body
                # The body has headers like ## Content
                tweet_text = self._extract_social_content(body)
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
                        return True
                    except subprocess.CalledProcessError as e:
                        self.logger.error(f"Tweet execution failed: {e.stderr}")
                        return False
                else:
                    self.logger.error("social-mcp server not found")
                    return False

            elif metadata.get('type') == 'invoice_posting' and action == 'post':
                invoice_id = metadata.get('invoice_id')
                if invoice_id:
                    self.logger.info(f"Executing Odoo invoice post: {invoice_id}")
                    try:
                        # Call main_operation.py directly
                        script_path = Path(".claude/skills/odoo-accounting/scripts/main_operation.py")
                        result = subprocess.run(
                            [sys.executable, str(script_path), "--mode", "live", "post", str(invoice_id), "--no-approval"],
                            text=True,
                            capture_output=True,
                            check=True
                        )
                        self.logger.info(f"Invoice post result: {result.stdout}")
                        return True
                    except subprocess.CalledProcessError as e:
                        self.logger.error(f"Invoice post failed: {e.stderr}")
                        return False
                else:
                    self.logger.error("Missing invoice_id in approval metadata")
                    return False

            # Qwen Autonomous Delegation
            elif os.getenv("REASONING_ENGINE") == "qwen":
                self.logger.info(f"Delegating generic task to Qwen: {filepath.name}")
                
                # Use body as prompt, sanitizing quotes
                prompt = body.replace('"', '\\"')
                if len(prompt) > 2000:
                   prompt = prompt[:2000]

                try:
                    # qwen -p "prompt" -y
                    cmd = f'qwen -p "{prompt}" -y'
                    self.logger.info(f"Running Qwen command: {cmd}")
                    
                    # Run with shell=True to ensure command is found
                    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if process.returncode == 0:
                        self.logger.info(f"Qwen execution success: {process.stdout}")
                        return True
                    else:
                        self.logger.error(f"Qwen execution failed (exit {process.returncode}): {process.stderr}")
                        return False

                except Exception as e:
                    self.logger.error(f"Qwen execution exception: {e}")
                    return False

            else:
                self.logger.info(f"Approved action ready for execution (No automatic handler): {filepath.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error processing approved file {filepath}: {e}")
            return False

    def process_rejected(self, filepath) -> bool:
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
            return True

        except Exception as e:
            self.logger.error(f"Error processing rejected file {filepath}: {e}")
            return False
