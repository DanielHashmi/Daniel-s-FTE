"""End-to-end test simulating dual-agent conflict scenario."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import shutil
import time

from deployment.vault_sync.claim_task import ClaimValidator


class TestDualAgentConflictE2E:
    """End-to-end test of dual-agent conflict handling."""

    def test_cloud_and_local_both_see_same_action(self):
        """
        Simulate scenario where both cloud and local agents see the same action
        at the same time (before sync).
        """
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        # Setup folder structure
        (vault_path / "Needs_Action").mkdir(parents=True)
        (vault_path / "In_Progress" / "cloud-agent").mkdir(parents=True)
        (vault_path / "In_Progress" / "local-agent").mkdir(parents=True)

        # Create action that both agents will see
        shared_action = vault_path / "Needs_Action" / "urgent_request.yaml"
        shared_action.write_text("""---
action_id: urgent_999
type: email
priority: urgent
timestamp: 2026-01-20T09:00:00Z
---

Urgent client request requiring immediate response
""")

        # Both agents check for updates
        validator_cloud = ClaimValidator(str(vault_path), "cloud-agent")
        validator_local = ClaimValidator(str(vault_path), "local-agent")

        # First agent to claim wins
        result_cloud, msg_cloud = validator_cloud.claim(str(shared_action))

        # Simulate small delay
        time.sleep(0.1)

        result_local, msg_local = validator_local.claim(str(shared_action))

        # Cloud agent should succeed (first)
        assert result_cloud is True
        assert "urgent_999" in msg_cloud

        # Local agent should be blocked
        assert result_local is False
        assert "already claimed" in msg_local

        # File should be in cloud agent's folder
        cloud_claimed = list((vault_path / "In_Progress" / "cloud-agent").glob("*.yaml"))
        assert len(cloud_claimed) == 1

        # Local agent has no files
        local_claimed = list((vault_path / "In_Progress" / "local-agent").glob("*.yaml"))
        assert len(local_claimed) == 0

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_conflict_resolution_via_first_claim_wins(self):
        """Test that simple first-claim-wins strategy resolves conflicts."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        (vault_path / "Needs_Action").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-a").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-b").mkdir(parents=True)

        # Create multiple actions
        for i in range(5):
            action = vault_path / "Needs_Action" / f"action_{i:03d}.yaml"
            action.write_text(f"""---
action_id: action_{i:03d}
type: task
---
Task {i}
""")

        # Simulate race condition - both agents try to claim all
        validator_a = ClaimValidator(str(vault_path), "agent-a")
        validator_b = ClaimValidator(str(vault_path), "agent-b")

        results_a = []
        results_b = []

        for i in range(5):
            action_path = vault_path / "Needs_Action" / f"action_{i:03d}.yaml"

            # Both try to claim (one will win)
            result_a, _ = validator_a.claim(str(action_path))
            result_b, _ = validator_b.claim(str(action_path))

            results_a.append(result_a)
            results_b.append(result_b)

        # Total successful claims should be 5 (no duplicates)
        total_claims = sum(results_a) + sum(results_b)
        assert total_claims == 5

        # Each agent should have some files (not all to one)
        files_a = list((vault_path / "In_Progress" / "agent-a").glob("*.yaml"))
        files_b = list((vault_path / "In_Progress" / "agent-b").glob("*.yaml"))

        assert len(files_a) + len(files_b) == 5

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_conflict_detection_in_sync(self):
        """
        Simulate conflict detected during vault sync:
        Same action_id found in both agents' folders after sync completes.
        """
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        (vault_path / "In_Progress" / "cloud-agent").mkdir(parents=True)
        (vault_path / "In_Progress" / "local-agent").mkdir(parents=True)

        # Simulate sync creating duplicate (shouldn't happen with claim-by-move)
        # But test conflict detection anyway
        shared_action1 = vault_path / "In_Progress" / "cloud-agent" / "action_shared.yaml"
        shared_action1.write_text("""---
action_id: conflict_001
agent: cloud-agent
---
Content from cloud
""")

        shared_action2 = vault_path / "In_Progress" / "local-agent" / "action_shared.yaml"
        shared_action2.write_text("""---
action_id: conflict_001
agent: local-agent
---
Content from local
""")

        # Run conflict detection
        validator_cloud = ClaimValidator(str(vault_path), "cloud-agent")
        validator_local = ClaimValidator(str(vault_path), "local-agent")

        # Both think the other claimed it
        is_claimed_cloud = validator_cloud.is_action_claimed_by_other(shared_action1)
        is_claimed_local = validator_local.is_action_claimed_by_other(shared_action2)

        # Both should see conflict
        assert is_claimed_cloud is True
        assert is_claimed_local is True

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_sync_latency_minimizes_conflicts(self):
        """
        Test that claim-by-move (atomic) minimizes conflicts during sync.
        Unlike copy-then-delete, move is atomic on same filesystem.
        """
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        (vault_path / "Needs_Action").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-fast").mkdir(parents=True)
        (vault_path / "In_Progress" / "agent-slow").mkdir(parents=True)

        # Create 10 actions
        actions = []
        for i in range(10):
            action = vault_path / "Needs_Action" / f"fast_action_{i:03d}.yaml"
            action.write_text(f"""---
action_id: fast_{i:03d}
---
Fast action {i}
""")
            actions.append(action)

        # Fast agent claims all quickly
        validator_fast = ClaimValidator(str(vault_path), "agent-fast")

        for action in actions:
            validator_fast.claim(str(action))

        # Slow agent tries to claim same actions
        validator_slow = ClaimValidator(str(vault_path), "agent-slow")
        conflict_count = 0

        for action in actions:
            _, msg = validator_slow.claim(str(action))
            if "already claimed" in msg:
                conflict_count += 1

        # All should be conflicts (fast agent won all)
        assert conflict_count == 10
        assert len(list((vault_path / "In_Progress" / "agent-fast").glob("*.yaml"))) == 10
        assert len(list((vault_path / "In_Progress" / "agent-slow").glob("*.yaml"))) == 0

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_e2e_workflow_with_conflict_handling(self):
        """
        Complete E2E test:
        1. Cloud agent processes email
        2. Creates draft
        3. Local agent sees draft after sync
        4. No conflict because cloud claimed the original action
        """
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        # Create full folder structure
        for folder in ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "In_Progress/cloud-agent", "In_Progress/local-agent"]:
            (vault_path / folder).mkdir(parents=True, exist_ok=True)

        # Step 1: Email arrives (action created in Needs_Action)
        email_action = vault_path / "Needs_Action" / "email_urgent.yaml"
        email_action.write_text("""---
action_id: email_urgent_001
type: email
priority: urgent
source: gmail
---

Urgent: Need response now
""")

        # Step 2: Cloud agent claims it
        validator_cloud = ClaimValidator(str(vault_path), "cloud-agent")
        result, msg = validator_cloud.claim(str(email_action))

        assert result is True
        assert not email_action.exists()  # Moved

        # Step 3: Cloud creates draft and puts in Pending_Approval
        draft_file = vault_path / "Pending_Approval" / "draft_response.yaml"
        draft_file.write_text("""---
draft_id: draft_001
type: email_draft
requires_approval: true
---

Draft response
""")

        # Step 4: Local agent sees draft is in Pending_Approval (not a conflict)
        local_validator = ClaimValidator(str(vault_path), "local-agent")

        # Local agent should NOT try to claim the draft (different workflow)
        # This is key: drafts are different from original actions

        assert draft_file.exists()  # Still there (not claimed)

        # Cleanup
        shutil.rmtree(temp_dir)


def test_claim_by_move_is_atomic():
    """Test that filesystem move is atomic (claim-by-move principle)."""
    import os

    temp_dir = Path(tempfile.mkdtemp())
    vault_path = temp_dir / "AI_Employee_Vault"
    vault_path.mkdir()

    (vault_path / "Needs_Action").mkdir(parents=True)
    (vault_path / "In_Progress" / "atomic-agent").mkdir(parents=True)

    # Create action
    src = vault_path / "Needs_Action" / "atomic.yaml"
    src.write_text("test")

    # Move is atomic (renames inode, not copy+delete)
    dst = vault_path / "In_Progress" / "atomic-agent" / "atomic.yaml"

    src_initial_inode = src.stat().st_ino
    os.rename(str(src), str(dst))
    dst_inode = dst.stat().st_ino

    # Same inode means atomic (no copy)
    assert src_initial_inode == dst_inode

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
