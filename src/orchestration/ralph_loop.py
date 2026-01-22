"""
Ralph Wiggum Loop Integration for Gold Tier.

This module integrates the Ralph Wiggum autonomous task execution loop
with the orchestrator for persistent multi-step task completion.
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from src.lib.logging import get_gold_tier_logger
from src.lib.state import StateManager, TaskState
from src.lib.vault import vault

logger = get_gold_tier_logger("ralph_loop")

class RalphLoopManager:
    """
    Manages Ralph Wiggum autonomous task execution loops.

    This class:
    1. Detects action files suitable for Ralph loops (multi-step tasks)
    2. Creates state files for tracking loop execution
    3. Monitors loop progress and handles completion
    """

    def __init__(self):
        self.state_manager = StateManager()
        self.logger = logger

    def is_suitable_for_ralph(self, action_file: Path) -> bool:
        """
        Determine if an action file is suitable for Ralph loop execution.

        Criteria:
        - Contains 5+ distinct steps or mentions sequential execution
        - File size > 500 bytes (likely multi-step task)
        - Keywords: "step", "sequential", "multi-step", "autonomous"
        """
        try:
            content = vault.read_file(action_file)

            # Check for Ralph keywords
            keywords = ["step", "sequential", "multi-step", "autonomous",
                       "complete all", "then", "next", "after"]

            # Check file size
            file_size = action_file.stat().st_size

            # Check for numbered steps (1. 2. 3. etc.)
            lines = content.lower().split('\n')
            step_count = sum(1 for line in lines if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')))

            # Decision criteria
            has_keywords = any(keyword in content.lower() for keyword in keywords)
            has_steps = step_count >= 3 or 'step' in content.lower()
            is_large = file_size > 500

            suitable = has_keywords or has_steps or is_large

            self.logger.info(
                f"Ralph suitability check: file={action_file.name}, "
                f"keywords={has_keywords}, steps={step_count}, "
                f"size={file_size}, suitable={suitable}"
            )

            return suitable

        except Exception as e:
            self.logger.error(f"Failed to check Ralph suitability for {action_file.name}: {e}")
            return False

    def create_loop_for_action(self, action_file: Path) -> Optional[str]:
        """
        Create a Ralph loop state for an action file.

        Args:
            action_file: Path to the action file

        Returns:
            loop_id if successful, None otherwise
        """
        try:
            content = vault.read_file(action_file)

            # Extract task description from first line or YAML frontmatter
            lines = content.split('\n')
            task_desc = lines[0] if lines else "Complete task"
            if task_desc.startswith('---'):
                # Find first non-YAML line
                for i, line in enumerate(lines[1:], 1):
                    if not line.startswith('---'):
                        task_desc = line
                        break

            # Create loop state
            loop_id = self.state_manager.create_loop(
                task_id=action_file.stem,
                prompt=f"Process the task file {action_file.name} and complete all steps.",
                watch_file=str(action_file),
                done_folder=str(vault.dirs["done"]),
                max_iterations=10,
                completion_promise="TASK_COMPLETE"
            )

            # Log state creation
            self.logger.log_action_with_duration(
                action_type="ralph_loop_created",
                result="success",
                target=loop_id,
                parameters={
                    "action_file": str(action_file.name),
                    "task_desc": task_desc[:100] + "..." if len(task_desc) > 100 else task_desc
                },
                details={
                    "max_iterations": 10,
                    "completion_strategy": "file_movement"
                }
            )

            return loop_id

        except Exception as e:
            self.logger.log_action_with_duration(
                action_type="ralph_loop_created",
                result="error",
                target=str(action_file.name),
                error=e
            )
            return None

    def process_completed_loops(self) -> Dict[str, Any]:
        """
        Check for completed Ralph loops and log results.

        Returns:
            Dict with completion statistics
        """
        stats = {"total": 0, "completed": 0, "failed": 0, "max_iterations": 0}

        try:
            # Get all state files
            state_files = list(Path(".claude/state").glob("RALPH_*.json"))
            stats["total"] = len(state_files)

            for state_file in state_files:
                try:
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)

                    loop_id = state_data.get("loop_id", "")
                    status = state_data.get("status", "")
                    current_iteration = state_data.get("current_iteration", 0)
                    max_iterations = state_data.get("max_iterations", 10)

                    # Update stats
                    if status == "completed":
                        stats["completed"] += 1

                        # Log completion
                        self.logger.log_action_with_duration(
                            action_type="ralph_loop_completed",
                            result="success",
                            target=loop_id,
                            parameters={
                                "iterations": current_iteration,
                                "max_iterations": max_iterations
                            }
                        )

                    elif status == "max_iterations_reached":
                        stats["max_iterations"] += 1

                        # Log max iterations reached
                        self.logger.log_action_with_duration(
                            action_type="ralph_loop_max_iterations",
                            result="warning",
                            target=loop_id,
                            parameters={
                                "iterations": current_iteration,
                                "max_iterations": max_iterations
                            }
                        )

                except Exception as e:
                    self.logger.error(f"Failed to process state file {state_file.name}: {e}")
                    stats["failed"] += 1

        except Exception as e:
            self.logger.error(f"Failed to process completed loops: {e}")

        return stats

    def integrate_with_orchestrator(self, orchestrator) -> None:
        """
        Integrate Ralph loop manager with the orchestrator.

        This adds Ralph loop detection to the orchestrator's check_needs_action method.
        """
        original_check_needs_action = orchestrator.check_needs_action

        def enhanced_check_needs_action():
            """Enhanced version that detects and handles Ralph loop tasks."""
            # Call original method
            original_check_needs_action()

            # Check for Ralph-suitable tasks
            actions = vault.list_files("needs_action", "*.md")
            if not actions:
                return

            for action_file in actions:
                if self.is_suitable_for_ralph(action_file):
                    loop_id = self.create_loop_for_action(action_file)
                    if loop_id:
                        self.logger.info(f"Created Ralph loop {loop_id} for {action_file.name}")
                        # Create a plan to trigger Ralph loop
                        # The Ralph stop hook will handle the rest

        # Replace the method
        orchestrator.check_needs_action = enhanced_check_needs_action
        self.logger.info("Ralph loop manager integrated with orchestrator")

    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """
        Run a single monitoring cycle.

        This should be called periodically to:
        1. Check for completed loops
        2. Update statistics
        3. Handle cleanup

        Returns:
            Statistics for the cycle
        """
        try:
            stats = self.process_completed_loops()

            # Log monitoring stats
            self.logger.info(
                f"Ralph loop monitoring: total={stats['total']}, "
                f"completed={stats['completed']}, failed={stats['failed']}, "
                f"max_iterations={stats['max_iterations']}"
            )

            return stats

        except Exception as e:
            self.logger.error(f"Ralph loop monitoring cycle failed: {e}")
            return {"error": str(e)}

# Global instance
ralph_loop_manager = RalphLoopManager()