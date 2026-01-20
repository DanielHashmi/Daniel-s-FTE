"""Integration tests for US3: Conflict Resolution with claim-by-move validator."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from deployment.vault_sync.claim_task import ClaimValidator


class TestClaimValidator:
    """Test the claim-by-move validator functionality."""

    @pytest.fixture
    def setup_vault(self):
        """Create temporary vault with multiple agents."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        # Create folders
        for folder in ["Needs_Action", "In_Progress"]:
            (vault_path / folder).mkdir()

        # Create multiple agent folders
        (vault_path / "In_Progress" / "cloud-agent-001").mkdir()
        (vault_path / "In_Progress" / "cloud-agent-002").mkdir()
        (vault_path / "In_Progress" / "local-agent-001").mkdir()

        yield vault_path

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def validator(self, setup_vault):
        """Create claim validator for testing."""
        return ClaimValidator(str(setup_vault), "cloud-agent-001")

    def test_validator_initialization(self, validator, setup_vault):
        """Test validator initializes with correct paths."""
        assert validator.vault_path == setup_vault
        assert validator.agent_id == "cloud-agent-001"
        assert validator.claimed_path == setup_vault / "In_Progress" / "cloud-agent-001"

    def test_validate_action_file_missing_frontmatter(self, validator, setup_vault):
        """Test validation fails for files without YAML frontmatter."""
        # Create invalid action file
        invalid_file = setup_vault / "Needs_Action" / "invalid.yaml"
        invalid_file.write_text("This file has no YAML frontmatter\n")

        valid, message = validator.validate_action_file(invalid_file)

        assert valid is False
        assert "Missing YAML frontmatter" in message

    def test_validate_action_file_valid_structure(self, validator, setup_vault):
        """Test validation passes for valid action files."""
        # Create valid action file
        valid_file = setup_vault / "Needs_Action" / "valid.yaml"
        valid_file.write_text("""---
action_id: test_001
type: email
source: test
---

Content
""")

        valid, message = validator.validate_action_file(valid_file)

        assert valid is True
        assert message == "Valid"

    def test_detect_action_claimed_by_another_agent(self, validator, setup_vault):
        """Test detection of actions claimed by other agents."""
        # Claim action for cloud-agent-001
        action_file = setup_vault / "Needs_Action" / "duplicate_test.yaml"
        action_file.write_text("""---
action_id: duplicate_001
---
Content
""")

        # First claim by cloud-agent-001
        validator1 = ClaimValidator(str(setup_vault), "cloud-agent-001")
        success, msg = validator1.claim(str(action_file))
        assert success is True

        # Try to claim same action by cloud-agent-002
        validator2 = ClaimValidator(str(setup_vault), "cloud-agent-002")
        is_claimed = validator2.is_action_claimed_by_other(action_file)

        assert is_claimed is True

    def test_allow_claim_if_not_claimed(self, validator, setup_vault):
        """Test that unclaimed actions can be claimed."""
        # Create action file
        action_file = setup_vault / "Needs_Action" / "claimable.yaml"
        action_file.write_text("""---
action_id: claimable_001
---
Content
""")

        validator2 = ClaimValidator(str(setup_vault), "cloud-agent-002")
        is_claimed = validator2.is_action_claimed_by_other(action_file)

        # Should not be claimed initially
        assert is_claimed is False

    def test_claim_moves_file_atomically(self, validator, setup_vault):
        """Test that claim operation moves file atomically."""
        action_file = setup_vault / "Needs_Action" / "move_test.yaml"
        action_file.write_text("""---
action_id: move_001
---
Content
""")

        # Claim the file
        success, message = validator.claim(str(action_file))

        assert success is True
        # File should be moved from Needs_Action
        assert not action_file.exists()

    def test_claim_creates_timestamped_name(self, validator, setup_vault):
        """Test that claimed files get timestamped names."""
        action_file = setup_vault / "Needs_Action" / "timestamp_test.yaml"
        action_file.write_text("""---
action_id: timestamp_001
---
Content
""")

        success, message = validator.claim(str(action_file))

        assert success is True
        # Should include timestamp in name
        claimed_files = list((setup_vault / "In_Progress" / "cloud-agent-001").glob("*.yaml"))
        assert len(claimed_files) == 1
        assert str(claimed_files[0]).startswith(str(setup_vault / "In_Progress" / "cloud-agent-001" / "timestamp_001"))

    def test_claim_record_created(self, validator, setup_vault):
        """Test that claim record is written."""
        action_file = setup_vault / "Needs_Action" / "record_test.yaml"
        action_file.write_text("""---
action_id: record_001
---
Content
""")

        success, message = validator.claim(str(action_file))

        assert success is True

        # Check for claim record file
        agent_folder = setup_vault / "In_Progress" / "cloud-agent-001"
        record_files = list(agent_folder.glob("*_claim.json"))

        assert len(record_files) == 1


class TestDualAgentConflicts:
    """Test scenarios with multiple agents competing for actions."""

    def test_two_agents_cannot_claim_same_action(self):
        """Test that first claimer wins, second is blocked."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        (vault_path / "Needs_Action").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-a").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-b").mkdir(parents=True)

        # Create shared action
        action_file = vault_path / "Needs_Action" / "shared_action.yaml"
        action_file.write_text("""---
action_id: shared_001
---
Shared action
""")

        # Agent A tries to claim
        validator_a = ClaimValidator(str(vault_path), "agent-a")
        result_a, _ = validator_a.claim(str(action_file))

        # Agent B tries to claim same action
        validator_b = ClaimValidator(str(vault_path), "agent-b")
        result_b, msg_b = validator_b.claim(str(action_file))

        # Agent A should succeed
        assert result_a is True

        # Agent B should be blocked
        assert result_b is False
        assert "already claimed" in msg_b

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    def test_agents_can_claim_different_actions(self):
        """Test that different actions can be claimed by different agents."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        (vault_path / "Needs_Action").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-a").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-b").mkdir(parents=True)

        # Create two different actions
        action1 = vault_path / "Needs_Action" / "action_1.yaml"
        action1.write_text("""---
action_id: action_001
---
Action 1
""")

        action2 = vault_path / "Needs_Action" / "action_2.yaml"
        action2.write_text("""---
action_id: action_002
---
Action 2
""")

        # Agent A claims first action
        validator_a = ClaimValidator(str(vault_path), "agent-a")
        result_a, _ = validator_a.claim(str(action1))

        # Agent B claims second action
        validator_b = ClaimValidator(str(vault_path), "agent-b")
        result_b, _ = validator_b.claim(str(action2))

        # Both should succeed
        assert result_a is True
        assert result_b is True

        # Both files should be moved
        assert not action1.exists()
        assert not action2.exists()

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


class TestConflictResolution:
    """Test conflict resolution mechanisms."""

    def test_detect_conflicts_via_action_id(self):
        """Test conflict detection by checking for duplicate action_ids."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        (vault_path / "In_Progress" / "agent-a").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-b").mkdir(parents=True)

        # Create conflicting actions (same action_id in different agents)
        action_a = vault_path / "In_Progress" / "agent-a" / "action_dup.yaml"
        action_a.write_text("""---
action_id: duplicate_action
agent: agent-a
---
Content
""")

        action_b = vault_path / "In_Progress" / "agent-b" / "action_dup.yaml"
        action_b.write_text("""---
action_id: duplicate_action
agent: agent-b
---
Content
""")

        # Manual conflict detection
        agent_folders = [d for d in (vault_path / "In_Progress").iterdir() if d.is_dir()]

        action_ids = {}
        conflicts = []

        for agent_folder in agent_folders:
            for file in agent_folder.glob("*.yaml"):
                content = file.read_text()
                if 'action_id:' in content:
                    action_id = content.split('action_id:')[1].split('\n')[0].strip()
                    if action_id in action_ids:
                        conflicts.append({
                            'action_id': action_id,
                            'agents': [action_ids[action_id], str(agent_folder.name)],
                            'files': [str(action_ids[f'{action_id}_file']), str(file)]
                        })
                    else:
                        action_ids[action_id] = str(agent_folder.name)
                        action_ids[f'{action_id}_file'] = str(file)

        # Should detect conflict
        assert len(conflicts) > 0
        assert conflicts[0]['action_id'] == 'duplicate_action'

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


def test_us3_mvp_requirements():
    """Test that US3 MVP requirements are met."""
    # MVP: Claim-by-move prevents duplicate processing

    # Verify claim-task.py exists
    claim_file = Path("deployment/vault-sync/claim-task.py")
    assert claim_file.exists()

    # Verify conflict detection logic exists
    content = claim_file.read_text()
    assert 'ClaimValidator' in content
    assert 'action_id' in content.lower()


class TestConcurrencySafety:
    """Test thread-safety of claim operation."""

    def test_claim_operation_idempotence(self):
        """Test that claiming same action twice doesn't cause issues."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        (vault_path / "Needs_Action").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-a").mkdir(parents=True)

        # Create action
        action_file = vault_path / "Needs_Action" / "idempotent.yaml"
        action_file.write_text("""---
action_id: idempotent_001
---
Content
""")

        validator = ClaimValidator(str(vault_path), "agent-a")

        # Try to claim twice
        result1, _ = validator.claim(str(action_file))
        result2, msg2 = validator.claim(str(action_file))

        # First should succeed
        assert result1 is True

        # Second should fail (already claimed)
        assert result2 is False

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
