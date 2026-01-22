"""E2E tests for US1: Offline Email Handover workflow."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.watchers.cloud_email_watcher import CloudEmailWatcher
from deployment.cloud.draft_reply import DraftReplyGenerator
from src.handlers.local_approval import LocalApprovalHandler


class TestUS1OfflineWorkflow:
    """Test complete US1 workflow: Cloud draft → Local approval → Handover."""

    @pytest.fixture
    def setup_vault(self):
        """Create isolated vault for each test."""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "AI_Employee_Vault"
        vault_path.mkdir()

        # Create standard folders
        for folder in ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Rejected", "Logs"]:
            (vault_path / folder).mkdir()

        yield vault_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_complete_handover_workflow(self, setup_vault, monkeypatch):
        """Test complete end-to-end handover workflow."""
        vault = setup_vault

        # Step 1: Simulate incoming email (create action file)
        incoming_email = """---
action_id: client_query_001
type: email
source: gmail
priority: high
timestamp: 2026-01-20T08:00:00Z
sender: client@example.com
subject: Urgent: Need response by EOD
---

Hi,

We need clarification on the Q1 proposal pricing. Can you respond today?

Thanks,
John
"""
        action_file = vault / "Needs_Action" / "client_query_001.yaml"
        action_file.write_text(incoming_email)

        # Step 2: Cloud watcher detects and processes (would normally run on cloud VM)
        monkeypatch.setenv('CLOUD_AGENT_ID', 'cloud-agent-001')
        cloud_watcher = CloudEmailWatcher(vault, check_interval=60)

        # Simulate being on cloud (detects email actions)
        items = cloud_watcher.check_for_updates()
        assert len(items) > 0

        item = items[0]
        assert item['type'] == 'email'
        assert item['source'] == 'cloud-agent-001'

        # Step 3: Cloud watcher creates DRAFT action
        draft_action_file = cloud_watcher.create_action_file(item)
        assert draft_action_file.exists()
        assert 'DRAFT_MODE' in draft_action_file.read_text()

        # Step 4: Cloud generates draft email response (simulates cloud environment)
        import yaml
        action = yaml.safe_load(incoming_email.split('---')[1])
        draft_gen = DraftReplyGenerator(str(vault))

        context = {
            'recipient': 'client@example.com',
            'sender_name': 'AI Assistant'
        }
        draft_email_file = draft_gen.generate_draft(action, context)
        assert draft_email_file.exists()
        assert draft_email_file.parent == vault / "Pending_Approval"

        # Step 5: Sync happens (Syncthing) - handover to local agent
        # (In real scenario, file would sync to local machine)

        # Step 6: Local agent picks up and approves
        monkeypatch.setenv('LOCAL_AGENT_ID', 'local-agent-001')
        local_handler = LocalApprovalHandler(vault)

        # Verify draft is detected
        drafts = local_handler.scan_pending_drafts()
        assert len(drafts) == 1
        assert drafts[0] == draft_email_file

        # Simulate approval without sending (no email creds in test)
        # Just verify the draft exists and can be processed
        draft_metadata = yaml.safe_load(draft_email_file.read_text().split('---')[1])
        assert draft_metadata['mode'] == 'DRAFT'
        assert draft_metadata['requires_approval'] is True
        assert draft_metadata['cloud_environment'] is True

    def test_offline_mode_no_send(self, setup_vault):
        """Test that drafts don't send in offline mode without approval."""
        vault = setup_vault

        # Create draft directly in Pending_Approval
        draft_content = """---
draft_id: offline_test_001
type: email_draft
mode: DRAFT
recipient: test@example.com
subject: Test Subject
requires_approval: true
cloud_environment: true
---

Test email body
"""
        draft_file = vault / "Pending_Approval" / "offline_test_001.yaml"
        draft_file.write_text(draft_content)

        # Verify it's pending (not auto-sent)
        handler = LocalApprovalHandler(vault)
        drafts = handler.scan_pending_drafts()
        assert draft_file in drafts

        # Verify no credentials = no automatic sending
        assert handler._has_email_credentials() is False

    def test_draft_mode_flag_preserved(self, setup_vault, monkeypatch):
        """Test that DRAFT_MODE flag is preserved through entire workflow."""
        # Critical: Draft mode prevents accidental sending

        vault = setup_vault
        monkeypatch.setenv('CLOUD_AGENT_ID', 'cloud-agent-001')

        # Create initial action
        action = """---
action_id: draft_flag_test
type: urgent
timestamp: 2026-01-20T12:00:00Z
---

Urgent request for information
"""
        action_file = vault / "Needs_Action" / "draft_flag_test.yaml"
        action_file.write_text(action)

        # Cloud processes and creates draft
        watcher = CloudEmailWatcher(vault)
        items = watcher.check_for_updates()
        assert len(items) > 0

        draft_action = watcher.create_action_file(items[0])
        content = draft_action.read_text()

        # Verify multiple DRAFT indicators
        assert 'DRAFT_MODE' in content or 'cloud_draft: true' in content
        assert 'requires_handover: true' in content
        assert 'HANDOVER REQUIRED' in content

    def test_dual_agent_identification(self, setup_vault, monkeypatch):
        """Test that both agents are correctly identified in workflow."""
        vault = setup_vault

        # Cloud agent setup
        monkeypatch.setenv('CLOUD_AGENT_ID', 'cloud-agent-prod-01')
        cloud_watcher = CloudEmailWatcher(vault)
        assert cloud_watcher.cloud_agent_id == 'cloud-agent-prod-01'

        # Local agent setup
        monkeypatch.setenv('LOCAL_AGENT_ID', 'local-agent-dev-01')
        local_handler = LocalApprovalHandler(vault)
        assert local_handler.local_agent_id == 'local-agent-dev-01'

    def test_rejection_path(self, setup_vault):
        """Test draft rejection workflow."""
        vault = setup_vault

        # Create draft
        draft_path = vault / "Pending_Approval" / "reject_me.yaml"
        draft_path.write_text("""---
draft_id: reject_me
type: email_draft
mode: DRAFT
recipient: spam@example.com
requires_approval: true
cloud_environment: true
---

Spam content
""")

        # Reject it
        handler = LocalApprovalHandler(vault)
        result = handler.reject_draft(draft_path)

        assert result['action'] == 'rejected'
        assert not draft_path.exists()

        # Verify moved to Rejected
        rejected_files = list((vault / "Rejected").glob("*.yaml"))
        assert len(rejected_files) == 1
        assert 'reject_me' in rejected_files[0].name

    def test_audit_logging(self, setup_vault):
        """Test that approval/rejection actions are logged."""
        vault = setup_vault

        handler = LocalApprovalHandler(vault)

        # Create and reject a draft
        draft_path = vault / "Pending_Approval" / "audit_test.yaml"
        draft_path.write_text("""---
draft_id: audit_test
type: email_draft
mode: DRAFT
recipient: test@example.com
subject: Test
requires_approval: true
cloud_environment: true
---
Test body
""")

        handler.reject_draft(draft_path)

        # Check log was created
        log_files = list((vault / "Logs").glob("approval_*.json"))
        assert len(log_files) > 0

        # Verify log content
        log_content = log_files[0].read_text()
        assert 'draft_rejected' in log_content
        assert 'local-agent-001' in log_content


def test_us1_mvp_requirements():
    """Test that US1 MVP requirements are met."""
    # MVP: Cloud can create drafts, local can approve them

    # Verify cloud components exist
    assert Path("src/watchers/cloud_email_watcher.py").exists()
    assert Path("deployment/cloud/draft_reply.py").exists()

    # Verify local components exist
    assert Path("src/handlers/local_approval.py").exists()

    # Verify draft mode indicators in code
    watcher_content = Path("src/watchers/cloud_email_watcher.py").read_text()
    assert 'DRAFT' in watcher_content.upper() or 'draft' in watcher_content

    handler_content = Path("src/handlers/local_approval.py").read_text()
    assert 'approve' in handler_content.lower()
