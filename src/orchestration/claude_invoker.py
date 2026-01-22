"""
Claude Code Invoker Module.

Invokes Claude Code CLI as the reasoning engine for plan generation.
This is the "Brain" of the AI Employee system per hackathon requirements.

Per hackathon guide: "The Brain: Claude Code acts as the reasoning engine...
It uses its File System tools to read your tasks and write reports."
"""

import subprocess
import shutil
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

from src.lib.logging import get_logger, AuditLogger


class ClaudeInvoker:
    """
    Invokes Claude Code CLI to generate intelligent plans from action files.

    This replaces template-based plan generation with actual AI reasoning.
    """

    def __init__(
        self,
        vault_path: str = "AI_Employee_Vault",
        max_invocations_per_minute: int = 10,
        timeout_seconds: int = 120
    ):
        self.vault_path = Path(vault_path)
        self.max_invocations_per_minute = max_invocations_per_minute
        self.timeout_seconds = timeout_seconds
        self.logger = get_logger("claude_invoker")
        self.audit_logger = get_logger("claude_invoker_audit")

        # Rate limiting
        self._invocation_times: list = []

        # Check if Claude Code is available
        self._claude_available = self._check_claude_available()

        if self._claude_available:
            self.logger.info("Claude Code CLI detected and available")
        else:
            self.logger.warning("Claude Code CLI not found - will use fallback template logic")

    def _check_claude_available(self) -> bool:
        """Check if the ccr (Claude Code Router) command is available in PATH.

        We use 'ccr code --print' instead of direct 'claude -p' because:
        - ccr handles authentication and model routing automatically
        - Direct claude CLI has TTY/auth issues with subprocess invocation
        - ccr provides consistent behavior across environments
        """
        # Check for ccr (Claude Code Router) which wraps claude CLI with auth handling
        ccr_path = shutil.which("ccr")
        if ccr_path:
            self.logger.info(f"Found ccr (Claude Code Router) at: {ccr_path}")
            return True

        # Fallback: check for direct claude CLI
        claude_path = shutil.which("claude")
        if claude_path:
            self.logger.info(f"Found claude CLI at: {claude_path} (may have auth issues)")
            return False  # Don't use direct claude due to TTY issues

        return False

    def _rate_limit_check(self) -> bool:
        """Check if we're within rate limits. Returns True if OK to proceed."""
        now = time.time()
        # Remove invocations older than 1 minute
        self._invocation_times = [t for t in self._invocation_times if now - t < 60]

        if len(self._invocation_times) >= self.max_invocations_per_minute:
            self.logger.warning(
                f"Rate limit reached: {len(self._invocation_times)}/{self.max_invocations_per_minute} per minute"
            )
            return False
        return True

    def _load_context(self) -> str:
        """Load context from Company_Handbook.md and Business_Goals.md."""
        context_parts = []

        # Load Company Handbook
        handbook_path = self.vault_path / "Company_Handbook.md"
        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding='utf-8')
                # Truncate if too long (keep first 2000 chars)
                if len(content) > 2000:
                    content = content[:2000] + "\n...[truncated]"
                context_parts.append(f"## Company Handbook\n{content}")
            except Exception as e:
                self.logger.error(f"Failed to read Company_Handbook.md: {e}")

        # Load Business Goals (if exists)
        goals_path = self.vault_path / "Business_Goals.md"
        if goals_path.exists():
            try:
                content = goals_path.read_text(encoding='utf-8')
                if len(content) > 1000:
                    content = content[:1000] + "\n...[truncated]"
                context_parts.append(f"## Business Goals\n{content}")
            except Exception as e:
                self.logger.error(f"Failed to read Business_Goals.md: {e}")

        return "\n\n".join(context_parts) if context_parts else "No context files available."

    def invoke_for_planning(
        self,
        action_content: str,
        action_metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Invoke Claude Code to generate a plan from an action file.

        Args:
            action_content: The full content of the action file
            action_metadata: YAML frontmatter metadata from the action file

        Returns:
            Generated plan content as markdown string, or None if failed
        """
        if not self._claude_available:
            self.logger.info("Claude Code not available, returning None for fallback handling")
            return None

        if not self._rate_limit_check():
            self.logger.warning("Rate limited - skipping Claude invocation")
            return None

        # Load context
        context = self._load_context()

        # Build the prompt
        action_type = action_metadata.get('type', 'unknown')
        priority = action_metadata.get('priority', 'normal')
        source = action_metadata.get('source', 'unknown')

        prompt = f"""You are an AI Employee. Generate an execution plan for this action.

CONTEXT:
{context}

ACTION ({action_type} from {source}, priority: {priority}):
{action_content}

OUTPUT ONLY THE MARKDOWN BELOW - NO EXPLANATION, NO COMMENTARY:

---
action_id: "{action_metadata.get('id', 'unknown')}"
type: "{action_type}"
source: "{source}"
created: "{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
requires_approval: <true_if_sensitive_else_false>
---

# Execution Plan: <brief_title>

## Objective
<one_sentence_goal>

## Analysis
<2-3_sentences_about_context_and_intent>

## Execution Steps
- [ ] Step 1
- [ ] Step 2 **[APPROVAL REQUIRED]** (if sending email/payment/posting)
- [ ] Step 3

## Risk Assessment
<brief_risks>

RULES:
- Mark [APPROVAL REQUIRED] for: new contacts, payments, public posts
- Output ONLY the markdown above, nothing else"""

        # Record invocation time for rate limiting
        self._invocation_times.append(time.time())

        start_time = time.time()

        try:
            self.logger.info(f"Invoking Claude Code (via ccr) for {action_type} action planning...")

            # Use ccr (Claude Code Router) which handles auth and model routing
            # Pass prompt via stdin to avoid shell escaping issues with long prompts
            result = subprocess.run(
                ['ccr', 'code', '-p'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env={**os.environ, 'CLAUDE_NO_TELEMETRY': '1'}
            )

            duration = time.time() - start_time

            if result.returncode != 0:
                self.logger.error(f"Claude Code returned error: {result.stderr}")
                self.audit_logger.log_action(
                    action_type="claude_invocation",
                    target="plan_generation",
                    result="failure",
                    parameters={"action_type": action_type, "error": result.stderr[:500]},
                    details={"duration_seconds": duration}
                )
                return None

            output = result.stdout.strip()

            if not output:
                self.logger.error("Claude Code returned empty output")
                return None

            # Log successful invocation
            self.audit_logger.log_action(
                action_type="claude_invocation",
                target="plan_generation",
                result="success",
                parameters={"action_type": action_type, "output_length": len(output)},
                details={"duration_seconds": duration}
            )

            self.logger.info(f"Claude Code completed in {duration:.2f}s, output: {len(output)} chars")

            return output

        except subprocess.TimeoutExpired:
            self.logger.error(f"Claude Code timed out after {self.timeout_seconds}s")
            self.audit_logger.log_action(
                action_type="claude_invocation",
                target="plan_generation",
                result="timeout",
                parameters={"action_type": action_type, "timeout": self.timeout_seconds}
            )
            return None

        except FileNotFoundError:
            self.logger.error("Claude Code CLI not found in PATH")
            self._claude_available = False
            return None

        except Exception as e:
            self.logger.error(f"Claude Code invocation failed: {e}")
            self.audit_logger.log_action(
                action_type="claude_invocation",
                target="plan_generation",
                result="error",
                parameters={"action_type": action_type, "error": str(e)}
            )
            return None

    @property
    def is_available(self) -> bool:
        """Check if Claude Code is available for invocation."""
        return self._claude_available

    def get_stats(self) -> Dict[str, Any]:
        """Get invocation statistics."""
        now = time.time()
        recent_invocations = len([t for t in self._invocation_times if now - t < 60])

        return {
            "claude_available": self._claude_available,
            "invocations_last_minute": recent_invocations,
            "max_per_minute": self.max_invocations_per_minute,
            "timeout_seconds": self.timeout_seconds
        }


# Singleton instance for easy access
_invoker_instance: Optional[ClaudeInvoker] = None


def get_claude_invoker(vault_path: str = "AI_Employee_Vault") -> ClaudeInvoker:
    """Get or create the Claude invoker singleton."""
    global _invoker_instance
    if _invoker_instance is None:
        _invoker_instance = ClaudeInvoker(vault_path=vault_path)
    return _invoker_instance
