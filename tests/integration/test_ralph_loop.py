"""Integration tests for Ralph Wiggum loop state handling."""

from pathlib import Path

from src.lib.state import StateManager
from src.lib.vault import vault
from src.orchestration.ralph_loop import RalphLoopManager


def _set_temp_vault(workspace_tmp_dir):
    original = vault.root
    test_root = workspace_tmp_dir / "AI_Employee_Vault"
    vault.set_root(str(test_root))
    vault.ensure_structure()
    return original


def test_ralph_suitability_detects_multistep_action(workspace_tmp_dir):
    original_root = _set_temp_vault(workspace_tmp_dir)
    try:
        action_file = vault.write_action(
            "TASK_multistep.md",
            (
                "---\n"
                "id: act_ralph_1\n"
                "type: task\n"
                "source: filesystem\n"
                "---\n\n"
                "1. Gather data\n"
                "2. Analyze results\n"
                "3. Draft response\n"
                "4. Request approval\n"
                "5. Execute final action\n"
            ),
            domain="business",
        )

        manager = RalphLoopManager()
        assert manager.is_suitable_for_ralph(action_file) is True
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()


def test_create_loop_for_action_writes_state(workspace_tmp_dir):
    original_root = _set_temp_vault(workspace_tmp_dir)
    try:
        state_dir = workspace_tmp_dir / "ralph_state_runtime"
        history_dir = workspace_tmp_dir / "ralph_history_runtime"
        custom_state_manager = StateManager(state_dir=state_dir, history_dir=history_dir)

        action_file = vault.write_action(
            "TASK_loop_state.md",
            (
                "---\n"
                "id: act_ralph_2\n"
                "type: task\n"
                "source: filesystem\n"
                "---\n\n"
                "Complete all steps and report status.\n"
            ),
            domain="business",
        )

        manager = RalphLoopManager()
        manager.state_manager = custom_state_manager

        loop_id = manager.create_loop_for_action(action_file)
        assert loop_id is not None

        state_file = state_dir / f"{loop_id}.json"
        assert state_file.exists()
        content = state_file.read_text(encoding="utf-8")
        assert "TASK_COMPLETE" in content
        assert str(action_file.name) in content
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()
