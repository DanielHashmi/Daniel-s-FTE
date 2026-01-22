import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from src.orchestration.orchestrator import Orchestrator
from src.orchestration.ralph_loop import RalphLoopManager
from src.lib.vault import vault

@pytest.fixture
def temp_vault():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault.vault_root = Path(tmpdir)
        vault.init_vault()
        yield vault

def test_ralph_loop_integration(temp_vault):
    orchestrator = Orchestrator()

    # Create multi-step action file (Ralph suitable)
    action_file = temp_vault.get_file_path('needs_action', 'multi-step-task.md')
    action_file.write_text("""
---
multi_step: true
steps:
  - step1: run command1
  - step2: run command2
---
""")

    # Run check_needs_action
    orchestrator.check_needs_action()

    # Verify Ralph loop state created
    state_files = temp_vault.list_files('.claude/state/', '*.json')
    assert len(state_files) == 1
    state_file = state_files[0]

    state_data = json.loads(state_file.read_text())
    assert 'loop_id' in state_data
    assert state_data['action_file'] == 'multi-step-task.md'
    assert state_data['iteration'] == 0
    assert state_data['status'] == 'active'

def test_ralph_loop_completion(temp_vault):
    ralph = RalphLoopManager()

    # Create loop
    action_file = temp_vault.get_file_path('needs_action', 'test-task.md')
    loop_id = ralph.create_loop_for_action(action_file)
    assert loop_id is not None

    # Simulate completion by moving to Done
    done_file = temp_vault.get_file_path('done', 'test-task.md')
    action_file.rename(done_file)

    # Check completion detection
    ralph.check_completed_loops()

    # Verify state updated
    state_file = Path('.claude/state/') / f'{loop_id}.json'
    state_data = json.loads(state_file.read_text())
    assert state_data['status'] == 'completed'
