"""
Plan Manager.

Responsible for analyzing Action Files and generating Execution Plans.
This is the "Reasoning" step of the AI Employee loop.

Per hackathon requirements: "Claude Code acts as the reasoning engine...
It uses its File System tools to read your tasks and write reports."

The plan manager now uses Claude Code CLI for intelligent plan generation,
with fallback to template-based logic if Claude is unavailable.
"""

import time
import hashlib
import yaml
import re
import os
from typing import Dict, Any, Optional
from src.lib.logging import get_logger
from src.lib.vault import vault

# Import Claude invoker for intelligent plan generation
try:
    from src.orchestration.claude_invoker import get_claude_invoker, ClaudeInvoker
    CLAUDE_INVOKER_AVAILABLE = True
except ImportError:
    CLAUDE_INVOKER_AVAILABLE = False


class PlanManager:
    def __init__(self, use_claude: bool = True):
        """
        Initialize the Plan Manager.

        Args:
            use_claude: If True, attempt to use Claude Code for plan generation.
                       If False or Claude unavailable, use template-based logic.
        """
        self.logger = get_logger("plan_manager")
        self.sensitive_keywords = ["email", "pay", "send", "post", "delete", "archive", "transfer", "invite"]

        # Initialize Claude invoker if available and requested
        self.claude_invoker: Optional[ClaudeInvoker] = None
        self.use_claude = use_claude

        if use_claude and CLAUDE_INVOKER_AVAILABLE:
            try:
                self.claude_invoker = get_claude_invoker(vault_path=str(vault.root))
                if self.claude_invoker.is_available:
                    self.logger.info("Claude Code integration enabled for intelligent planning")
                else:
                    self.logger.info("Claude Code CLI not found - using template-based planning")
                    self.claude_invoker = None
            except Exception as e:
                self.logger.error(f"Failed to initialize Claude invoker: {e}")
                self.claude_invoker = None
        else:
            self.logger.info("Template-based planning mode (Claude integration disabled)")

    def create_plan_from_action(self, action_file_path: Any) -> str:
        """
        Read an action file and generate a plan.

        If Claude Code is available, uses intelligent AI-powered planning.
        Otherwise, falls back to rule-based template logic.

        Returns:
            The filename of the created plan, or empty string on failure.
        """
        try:
            content = vault.read_file(action_file_path)

            # Parse frontmatter
            parts = content.split('---', 2)
            if len(parts) < 3:
                self.logger.error("Invalid action file format")
                return ""

            frontmatter = yaml.safe_load(parts[1])
            body = parts[2]

            # Try Claude Code first if available
            plan_content = None
            if self.claude_invoker and self.claude_invoker.is_available:
                self.logger.info("Attempting Claude Code intelligent planning...")
                plan_content = self.claude_invoker.invoke_for_planning(
                    action_content=content,
                    action_metadata=frontmatter
                )

                if plan_content:
                    self.logger.info("Successfully generated plan using Claude Code")
                else:
                    self.logger.info("Claude Code returned no output, falling back to templates")

            # Fallback to template-based logic
            if not plan_content:
                self.logger.info("Using template-based plan generation")
                plan_content = self._generate_plan_logic(frontmatter, body)

            # Write Plan File
            timestamp = int(time.time())
            filename = f"{timestamp}_plan_{frontmatter.get('id', 'unknown')}.md"
            path = vault.write_plan(filename, plan_content)

            self.logger.log_action(
                action_type="create_plan",
                result="success",
                target=str(path),
                details={
                    "source_action": frontmatter.get('id'),
                    "used_claude": bool(self.claude_invoker and plan_content)
                }
            )

            return filename

        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            return ""

    def _generate_plan_logic(self, meta: Dict[str, Any], body: str) -> str:
        """
        Internal template-based logic to determine the plan.
        This is the fallback when Claude Code is not available.
        """
        action_type = meta.get("type", "unknown")
        action_id = meta.get("id", "unknown")

        # Default template
        plan = f"""---
id: "plan_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
action_ref: "{action_id}"
created: "{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
status: "planning"
planning_mode: "template"
---

# Objective
Handle incoming {action_type} from {meta.get('source', 'unknown')}.

# Context
{body[:200]}...

# Execution Steps
"""

        # Logic based on type
        if action_type == "email":
            plan += self._plan_email_response(meta)
        elif action_type == "message":
            plan += self._plan_message_response(meta)
        elif action_type == "social":
            plan += self._plan_social_post(meta)
        elif action_type == "file_drop":
            plan += self._plan_file_processing(meta)
        else:
            plan += "- [ ] 1. Review Request\n"
            plan += "- [ ] 2. Determine appropriate action\n"
            plan += "- [ ] 3. Execute or request approval\n"

        plan += "\n# Note\n"
        plan += "*This plan was generated using template logic. For intelligent planning, ensure Claude Code CLI is installed and available.*\n"

        return plan

    def _plan_email_response(self, meta: Dict[str, Any]) -> str:
        """Template for email action planning."""
        steps = ""
        steps += "- [ ] 1. Analyze email content\n"
        steps += "- [ ] 2. Draft response\n"
        # For email, sending is always sensitive
        steps += "- [ ] 3. **[APPROVAL REQUIRED]** Send Reply\n"
        steps += "- [ ] 4. Archive Email\n"
        return steps

    def _plan_message_response(self, meta: Dict[str, Any]) -> str:
        """Template for message action planning."""
        steps = ""
        steps += "- [ ] 1. Read message\n"
        steps += "- [ ] 2. Draft reply\n"
        steps += "- [ ] 3. **[APPROVAL REQUIRED]** Send Reply\n"
        return steps

    def _plan_social_post(self, meta: Dict[str, Any]) -> str:
        """Template for social media post planning."""
        steps = ""
        steps += "- [ ] 1. Review post content\n"
        steps += "- [ ] 2. Check for duplicate content\n"
        steps += "- [ ] 3. Format for platform\n"
        steps += "- [ ] 4. **[APPROVAL REQUIRED]** Publish Post\n"
        steps += "- [ ] 5. Log post URL and engagement\n"
        return steps

    def _plan_file_processing(self, meta: Dict[str, Any]) -> str:
        """Template for file drop action planning."""
        steps = ""
        steps += "- [ ] 1. Analyze file content\n"
        steps += "- [ ] 2. Determine file type and purpose\n"
        steps += "- [ ] 3. Process according to type\n"
        steps += "- [ ] 4. Move to appropriate folder\n"
        return steps

    def get_planning_mode(self) -> str:
        """Return the current planning mode."""
        if self.claude_invoker and self.claude_invoker.is_available:
            return "claude_code"
        return "template"

    def get_stats(self) -> Dict[str, Any]:
        """Get planning statistics."""
        stats = {
            "planning_mode": self.get_planning_mode(),
            "claude_available": bool(self.claude_invoker and self.claude_invoker.is_available),
        }

        if self.claude_invoker:
            stats["claude_stats"] = self.claude_invoker.get_stats()

        return stats


if __name__ == "__main__":
    pm = PlanManager()
    print(f"Planning mode: {pm.get_planning_mode()}")
    print(f"Stats: {pm.get_stats()}")
