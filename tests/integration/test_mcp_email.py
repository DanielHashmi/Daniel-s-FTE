"""Integration tests for Email MCP with cloud draft and local approval workflow."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.watchers.cloud_email_watcher import CloudEmailWatcher
from deployment.cloud.draft_reply import DraftReplyGenerator
from src.handlers.local_approval import LocalApprovalHandler


@pytest.fixture
def test_action_file(temp_vault):
    """Create a test action file that requires email response."""
    action_content = """---
action_id: test_email_001
type: email
source: test
priority: high
timestamp: 2026-01-20T10:00:00Z
title: Test Email Request
---

# Email Request

Please respond to this test email with availability information.
"""
    action_file = temp_vault / "Needs_Action" / "test_email_001.yaml"
    action_file.write_text(action_content)
    return action_file


@pytest.fixture
def cloud_watcher(temp_vault):
    """Create cloud email watcher for testing."""
    watcher = CloudEmailWatcher(temp_vault, check_interval=60)
    return watcher


@pytest.fixture
def draft_generator(temp_vault):
    """Create draft reply generator for testing."""
    generator = DraftReplyGenerator(str(temp_vault))
    return generator


class TestCloudEmailWatcher:
    """Test cloud email watcher functionality."""

    def test_watcher_initialization(self, cloud_watcher):
        """Test cloud email watcher initializes correctly."""
        assert cloud_watcher is not None
        assert cloud_watcher.cloud_agent_id == "cloud-agent-001"
        assert cloud_watcher.needs_action.exists()

    def test_check_for_updates_finds_email_actions(self, cloud_watcher, test_action_file):
        """Test watcher finds email actions in Needs_Action."""
        items = cloud_watcher.check_for_updates()

        # Should find email action
        assert len(items) > 0
        email_items = [item for item in items if item['type'] == 'email']
        assert len(email_items) == 1

        item = email_items[0]
        assert item['id'] == 'test_email_001'
        assert item['source'] == 'cloud-agent-001'
        assert item['priority'] == 'high'

    def test_create_draft_action(self, cloud_watcher):
        """Test draft action creation with proper metadata."""
        test_item = {
            'id': 'test_email_123',
            'source': 'cloud-agent-001',
            'priority': 'high',
            'content': 'Test email content',
            'timestamp': '2026-01-20T10:00:00Z'
        }

        action_file = cloud_watcher.create_action_file(test_item)

        # Verify file created
        assert action_file.exists()

        # Verify content
        content = action_file.read_text()
        assert 'DRAFT_MODE: true' in content
        assert 'HANDOVER REQUIRED' in content
        assert 'cloud_draft: true' in content
        assert 'requires_handover: true' in content


class TestDraftReplyGenerator:
    """Test draft email reply generation."""

    def test_generator_initialization(self, draft_generator, temp_vault):
        """Test draft generator initializes with correct paths."""
        assert draft_generator.vault_path == temp_vault
        assert draft_generator.drafts_folder.exists()

    def test_select_template(self, draft_generator):
        """Test template selection based on action type."""
        # Invoice action
        action = {'type': 'invoice', 'content': 'test'}
        template = draft_generator._select_template(action, {})
        assert template == 'invoice_response'

        # Payment action
        action = {'type': 'payment', 'content': 'test'}
        template = draft_generator._select_template(action, {})
        assert template == 'payment_confirmation'

        # Urgent action
        action = {'type': 'urgent', 'content': 'test'}
        template = draft_generator._select_template(action, {})
        assert template == 'urgent_reply'

    def test_generate_subject(self, draft_generator):
        """Test subject generation."""
        # With subject in action
        action = {'subject': 'Invoice #123'}
        subject = draft_generator._generate_subject(action, {})
        assert subject == "RE: Invoice #123"

        # With title in action
        action = {'title': 'Urgent Request'}
        subject = draft_generator._generate_subject(action, {})
        assert subject == "Re: Urgent Request"

        # Default based on type
        action = {'type': 'invoice'}
        subject = draft_generator._generate_subject(action, {})
        assert subject == "Invoice Response"

    def test_generate_draft_creates_file(self, draft_generator, temp_vault, test_action_file):
        """Test draft generation creates proper file with metadata."""
        # Load action
        action_content = test_action_file.read_text()
        action = yaml.safe_load(action_content.split('---')[1])

        # Set context
        context = {
            'recipient': 'test@example.com',
            'sender_name': 'AI Employee'
        }

        # Generate draft
        draft_path = draft_generator.generate_draft(action, context)

        # Verify file created
        assert draft_path.exists()
        assert draft_path.parent == temp_vault / "Pending_Approval"

        # Verify metadata
        draft_content = draft_path.read_text()
        assert 'type: email_draft' in draft_content
        assert 'mode: DRAFT' in draft_content
        assert 'requires_approval: true' in draft_content
        assert 'cloud_environment: true' in draft_content


class TestLocalApprovalHandler:
    """Test local approval handler functionality."""

    @pytest.fixture
    def approval_handler(self, temp_vault):
        """Create local approval handler for testing."""
        handler = LocalApprovalHandler(temp_vault)
        return handler

    @pytest.fixture
    def test_draft_file(self, draft_generator, temp_vault, test_action_file):
        """Create a test draft file for approval."""
        # Load action and generate draft
        action_content = test_action_file.read_text()
        action = yaml.safe_load(action_content.split('---')[1])
        context = {'recipient': 'test@example.com'}

        draft_path = draft_generator.generate_draft(action, context)
        return draft_path

    def test_handler_initialization(self, approval_handler, temp_vault):
        """Test handler initializes correctly."""
        assert approval_handler.vault_path == temp_vault
        assert approval_handler.local_agent_id == 'local-agent-001'
        assert approval_handler.pending_approval.exists()
        assert approval_handler.approved.exists()
        assert approval_handler.rejected.exists()

    def test_scan_drafts(self, approval_handler, test_draft_file):
        """Test scanning for pending drafts."""
        drafts = approval_handler.scan_pending_drafts()

        assert len(drafts) > 0
        assert test_draft_file in drafts

    def test_has_email_credentials(self, approval_handler, monkeypatch):
        """Test email credential validation."""
        # Should return False when no credentials
        assert approval_handler._has_email_credentials() is False

        # Set credentials and test
        monkeypatch.setenv('EMAIL_USERNAME', 'test@example.com')
        monkeypatch.setenv('EMAIL_APP_PASSWORD', 'test_password')
        monkeypatch.setenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')

        # Reload handler to pick up env vars
        handler = LocalApprovalHandler(approval_handler.vault_path)
        assert handler._has_email_credentials() is True


class TestEndToEndWorkflow:
    """Test complete email MCP workflow: cloud watcher → draft → local approval."""

    def test_complete_workflow(self, temp_vault):
        """Test complete cloud to local email workflow."""
        # Step 1: Create initial email action
        action_content = """---
action_id: workflow_test_001
type: email
source: client_inquiry
priority: medium
timestamp: 2026-01-20T11:00:00Z
title: Inquiry about Services
---

Dear AI Assistant,

I would like to inquire about your services for next quarter.

Best,
John Doe
"""
        action_file = temp_vault / "Needs_Action" / "workflow_test_001.yaml"
        action_file.write_text(action_content)

        # Step 2: Cloud watcher detects and creates draft action
        cloud_watcher = CloudEmailWatcher(temp_vault)
        items = cloud_watcher.check_for_updates()

        assert len(items) > 0
        assert 'test' in items[0]['id']

        draft_action_file = cloud_watcher.create_action_file(items[0])
        assert draft_action_file.exists()

        # Step 3: Draft generator creates email draft
        draft_gen = DraftReplyGenerator(str(temp_vault))
        action = yaml.safe_load(action_content.split('---')[1])
        context = {
            'recipient': 'client@example.com',
            'sender_name': 'AI Employee'
        }
        draft_file = draft_gen.generate_draft(action, context)
        assert draft_file.exists()

        # Step 4: Local approval handler processes draft
        # (Note: Can't actually send in test without credentials)
        handler = LocalApprovalHandler(temp_vault)
        assert draft_file in handler.scan_pending_drafts()

        # Clean up
        if action_file.exists():
            action_file.unlink()
        if draft_action_file.exists():
            draft_action_file.unlink()
        if draft_file.exists():
            draft_file.unlink()

    def test_draft_rejection_workflow(self, temp_vault, draft_generator):
        """Test draft rejection workflow."""
        # Create and generate draft
        action = {
            'action_id': 'reject_test',
            'type': 'test',
            'title': 'Test',
            'content': 'Test content'
        }
        context = {'recipient': 'test@example.com'}
        draft_file = draft_generator.generate_draft(action, context)

        # Reject draft
        handler = LocalApprovalHandler(temp_vault)
        result = handler.reject_draft(draft_file)

        assert result['action'] == 'rejected'
        assert not draft_file.exists()  # Should be moved

        # Check it's in rejected folder
        rejected_files = list((temp_vault / "Rejected").glob("*.yaml"))
        assert len(rejected_files) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
