"""Test vault sync latency and performance."""

import pytest
import tempfile
from pathlib import Path
import shutil
import time

from deployment.vault_sync.claim_task import ClaimValidator


class TestVaultSyncLatency:
    """Test vault sync performance meets <30s target."""

    @pytest.fixture
    def test_vault(self):
        """Create test vault structure."""
        temp_dir = Path(tempfile.mkdtemp())
        vault_path = temp_dir / "AI_Employee_Vault"
        vault_path.mkdir()

        # Create base folders
        folders = [
            "Inbox",
            "Needs_Action",
            "Done",
            "Plans",
            "Logs",
            "Pending_Approval",
            "Approved",
            "Rejected",
            "In_Progress/cloud-agent",
            "In_Progress/local-agent",
        ]

        for folder in folders:
            (vault_path / folder).mkdir(parents=True)

        yield vault_path

        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    def test_single_file_sync_latency(self, test_vault):
        """Test single file sync/claim latency."""
        # Create a file in Needs_Action
        action_file = test_vault / "Needs_Action" / "latency_test.yaml"
        action_file.write_text("""---
action_id: latency_001
type: test
---
Content for latency test
""")

        # Measure claim time (simulates sync time)
        validator = ClaimValidator(str(test_vault), "cloud-agent")

        start_time = time.time()
        success, message = validator.claim(str(action_file))
        end_time = time.time()

        # Verify success
        assert success is True

        # Check latency (should be <30s, actually should be <1s)
        latency = end_time - start_time
        print(f"Single file claim latency: {latency:.3f}s")

        assert latency < 1.0  # Should be very fast

    def test_batch_action_processing_latency(self, test_vault):
        """Test processing batch of 50 actions."""
        # Create 50 action files
        action_files = []
        for i in range(50):
            action_file = test_vault / "Needs_Action" / f"batch_action_{i:03d}.yaml"
            action_file.write_text(f"""---
action_id: batch_{i:03d}
type: email
---
Email body {i}
""")
            action_files.append(action_file)

        # Measure time to claim all
        validator = ClaimValidator(str(test_vault), "cloud-agent")

        start_time = time.time()

        for action_file in action_files:
            success, _ = validator.claim(str(action_file))
            assert success is True

        end_time = time.time()

        total_latency = end_time - start_time
        avg_latency_per_file = total_latency / 50

        print(f"Batch processing: 50 files in {total_latency:.3f}s")
        print(f"Average per file: {avg_latency_per_file:.3f}s")

        # Processing 50 files should take <10s (200ms per file)
        assert total_latency < 10.0

    def test_large_file_sync_latency(self, test_vault):
        """Test sync latency with large file (1MB)."""
        # Create large file
        large_file = test_vault / "Needs_Action" / "large_file.yaml"

        # Generate ~1MB of content
        large_content = "x" * (1024 * 1024)  # 1MB
        large_file.write_text(f"""---
action_id: large_001
type: document
---
{large_content}
""")

        size_mb = large_file.stat().st_size / (1024 * 1024)
        print(f"File size: {size_mb:.2f} MB")

        # Measure claim time
        validator = ClaimValidator(str(test_vault), "cloud-agent")

        start_time = time.time()
        success, message = validator.claim(str(large_file))
        end_time = time.time()

        assert success is True

        latency = end_time - start_time
        print(f"Large file sync latency: {latency:.3f}s ({size_mb:.2f} MB)")

        # Should complete in <5s even for large file
        assert latency < 5.0

    def test_sync_with_no_changes(self, test_vault):
        """Test sync performance when no changes to sync."""
        # Scan empty Needs_Action
        validator = ClaimValidator(str(test_vault), "cloud-agent")

        start_time = time.time()

        available_actions = list((test_vault / "Needs_Action").glob("*.yaml"))

        end_time = time.time()

        latency = end_time - start_time
        print(f"Scan with no changes: {latency:.6f}s")

        # Should be extremely fast
        assert latency < 0.001

    def test_concurrent_access_simulation(self, test_vault):
        """Test that concurrent claims don't cause data corruption."""
        import threading

        results = {'agent_a': 0, 'agent_b': 0, 'conflicts': 0}

        def claim_actions(agent_name, start, end):
            validator = ClaimValidator(str(test_vault), agent_name)

            for i in range(start, end):
                action_file = test_vault / "Needs_Action" / f"concurrent_{i:03d}.yaml"
                if action_file.exists():
                    success, msg = validator.claim(str(action_file))

                    if success:
                        results[agent_name] += 1
                    elif "already claimed" in msg:
                        results['conflicts'] += 1

        # Create actions
        for i in range(20):
            action_file = test_vault / "Needs_Action" / f"concurrent_{i:03d}.yaml"
            action_file.write_text(f"""---
action_id: concurrent_{i:03d}
---
Action {i}
""")

        # Both agents try to claim concurrently
        thread_a = threading.Thread(target=claim_actions, args=("agent_a", 0, 20))
        thread_b = threading.Thread(target=claim_actions, args=("agent_b", 0, 20))

        thread_a.start()
        thread_b.start()

        thread_a.join()
        thread_b.join()

        total_claimed = results['agent_a'] + results['agent_b']
        print(f"Agent A claimed: {results['agent_a']}")
        print(f"Agent B claimed: {results['agent_b']}")
        print(f"Conflicts detected: {results['conflicts']}")
        print(f"Total actions: {total_claimed}")

        # All 20 actions should be claimed (no losses)
        assert total_claimed == 20

    def test_sync_latency_meets_target(self):
        """Verify sync latency target of <30s is achieved."""
        # The target from plan.md is <30s sync latency
        # Our implementation should be much faster (<1s for reasonable loads)

        # Run multiple tests and calculate average
        latencies = []

        for _ in range(10):
            temp_dir = Path(tempfile.mkdtemp())
            vault_path = temp_dir / "AI_Employee_Vault"
            vault_path.mkdir()

            (vault_path / "Needs_Action").mkdir()
            (vault_path / "In_Progress" / "test-agent").mkdir(parents=True)

            action_file = vault_path / "Needs_Action" / "target_test.yaml"
            action_file.write_text("""---
action_id: target_001
---
Test
""")

            validator = ClaimValidator(str(vault_path), "test-agent")

            start = time.time()
            validator.claim(str(action_file))
            end = time.time()

            latencies.append(end - start)

            shutil.rmtree(temp_dir)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        print(f"Average sync latency: {avg_latency:.3f}s")
        print(f"Max sync latency: {max_latency:.3f}s")

        # Must meet <30s target
        assert avg_latency < 30.0
        assert max_latency < 30.0

        # Should be much faster in practice
        assert avg_latency < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
