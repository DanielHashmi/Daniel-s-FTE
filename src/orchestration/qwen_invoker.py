"""
Qwen Invoker Module.

Invokes Qwen CLI as the primary reasoning engine.
Uses: qwen -p "prompt" -y
"""

import subprocess
import shutil
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any
from src.lib.logging import get_logger

class QwenInvoker:
    """
    Invokes Qwen CLI to generate intelligent plans.
    Uses the command: qwen -p "prompt" -y
    """

    def __init__(
        self,
        vault_path: str = "AI_Employee_Vault",
        timeout_seconds: int = 120
    ):
        self.vault_path = Path(vault_path)
        self.timeout_seconds = timeout_seconds
        self.logger = get_logger("qwen_invoker")
        
        # Determine executable path
        # On Windows, explicitly look for qwen.cmd if 'qwen' isn't found
        default_bin = "qwen.cmd" if os.name == 'nt' else "qwen"
        env_path = os.getenv("QWEN_PATH", default_bin)
        
        # Try to resolve full path using shutil.which
        resolved = shutil.which(env_path)
        
        # Fallback: check standard npm path on Windows if not resolved
        if not resolved and os.name == 'nt':
             # Check common npm locations
             npm_path = os.path.expandvars(r"%APPDATA%\npm\qwen.cmd")
             if os.path.exists(npm_path):
                 resolved = npm_path
             else:
                 # Try program files just in case
                 pass

        if resolved:
            self.qwen_path = resolved
            self._available = True
            self.logger.info(f"Qwen CLI ready (Path: {self.qwen_path})")
        else:
            self.qwen_path = env_path # Keep for logging
            self._available = False
            self.logger.warning(f"Qwen CLI not found at '{self.qwen_path}' - Qwen disabled.")
            self.logger.warning("Please add 'qwen' to PATH or set QWEN_PATH in .env")

    def available(self) -> bool:
        """Check if Qwen is available."""
        return self._available

    # Alias for property access if needed
    @property
    def is_available(self) -> bool:
        return self._available

    def _load_context(self) -> str:
        """Load context from Company_Handbook.md."""
        handbook_path = self.vault_path / "Company_Handbook.md"
        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding='utf-8')
                return content[:1500]
            except:
                pass
        return ""

    def invoke_for_planning(
        self,
        action_content: str,
        action_metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Invoke Qwen CLI to generate a plan.
        """
        if not self._available:
            self.logger.warning("Qwen invoke called but unavailable.")
            return None

        # Extract metadata
        action_type = action_metadata.get("type", "unknown")
        source = action_metadata.get("source", "unknown")
        action_id = action_metadata.get("id", "unknown")

        # Strict prompt with clear instructions - passed via stdin to avoid escaping issues
        prompt = f"""You are an AI planning assistant. Your ONLY job is to output a valid Markdown execution plan.
NO conversation. NO questions. NO "I'd be happy to help". Just output the plan directly.

ACTION TO PROCESS:
{action_content}

OUTPUT THE FOLLOWING MARKDOWN EXACTLY (fill in the bracketed sections):
---
action_id: "{action_id}"
type: "{action_type}"
status: "pending"
---

# Plan

## Objective
[Write 1-2 sentences describing what needs to be done based on the action above]

## Steps
- [ ] 1. [First step]
- [ ] 2. [Second step]
- [ ] 3. **[APPROVAL REQUIRED]** [Action requiring human approval if any]

## Notes
[Any relevant context or considerations]

BEGIN OUTPUT NOW:"""

        try:
            start_time = time.time()

            # Use stdin to pass prompt - avoids Windows command-line escaping issues
            cmd = [self.qwen_path, '-y', '--input-format', 'text']

            self.logger.info(f"Executing Qwen: {self.qwen_path} ...")

            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding='utf-8',
                errors='replace',
                cwd=str(self.vault_path.parent) if self.vault_path.exists() else None
            )

            duration = time.time() - start_time

            if result.returncode != 0:
                self.logger.error(f"Qwen CLI failed (code {result.returncode}): {result.stderr}")
                return None
            
            raw_output = result.stdout.strip()
            
            if not raw_output:
                self.logger.warning("Qwen returned empty output")
                return None

            self.logger.info(f"Qwen plan generated in {duration:.1f}s")
            
            # Extract valid plan
            plan = self._extract_plan(raw_output)
            if not plan:
                self.logger.warning(f"Qwen output rejected (no plan structure). Raw preview: {raw_output[:200]}")
                return None
                
            return plan

        except subprocess.TimeoutExpired:
            self.logger.error(f"Qwen timed out after {self.timeout_seconds}s")
            return None
        except Exception as e:
            self.logger.error(f"Qwen invocation failed: {e}")
            return None

    def _extract_plan(self, text: str) -> Optional[str]:
        """
        Extract the Markdown plan from Qwen's output, removing conversational fluff.
        """
        if not text: return None

        # 1. Look for Frontmatter start ('---')
        if '---' in text:
            idx = text.find('---')
            # If there's fluff before ---, strip it
            if idx > 0:
                # Optional: log that we stripped something?
                pass
            return text[idx:]
            
        # 2. Look for Header start ('# Plan')
        if '# Plan' in text:
            idx = text.find('# Plan')
            return text[idx:]
        
        # 3. Fallback: Check if it looks like a list
        if '- [ ]' in text:
            return text
            
        return None

# Singleton
_qwen_instance: Optional[QwenInvoker] = None

def get_qwen_invoker(vault_path: str = "AI_Employee_Vault") -> QwenInvoker:
    global _qwen_instance
    if _qwen_instance is None:
        _qwen_instance = QwenInvoker(vault_path=vault_path)
    return _qwen_instance
