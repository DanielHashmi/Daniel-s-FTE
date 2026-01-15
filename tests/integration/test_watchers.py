"""
Integration Tests for Watchers.

Verifies that watchers can be instantiated and follow the BaseWatcher contract.
External APIs are mocked.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.watchers.gmail import GmailWatcher
from src.watchers.whatsapp import WhatsAppWatcher
from src.watchers.linkedin import LinkedInWatcher
from src.lib.vault import Vault

@pytest.fixture
def mock_vault():
    with patch('src.watchers.base.vault') as mock:
        yield mock

class TestWatchers:

    @patch('src.watchers.gmail.Credentials')
    @patch('src.watchers.gmail.build')
    def test_gmail_watcher_init(self, mock_build, mock_creds, mock_vault):
        """Test Gmail watcher initialization and auth flow."""
        watcher = GmailWatcher()
        watcher.check_for_updates()

        # Verify it tries to use service if auth succeeds
        # (Mocking specifics depends on how deep we want to go)
        assert watcher.name == "gmail_watcher"

    @patch('src.watchers.whatsapp.sync_playwright')
    def test_whatsapp_watcher_init(self, mock_playwright, mock_vault):
        """Test WhatsApp watcher initialization."""
        watcher = WhatsAppWatcher(headless=True)
        assert watcher.name == "whatsapp_watcher"

        # Test check loop triggers browser setup
        watcher.check_for_updates()
        mock_playwright.return_value.start.assert_called_once()

    def test_linkedin_watcher_init(self, mock_vault):
        """Test LinkedIn watcher initialization."""
        watcher = LinkedInWatcher()
        assert watcher.name == "linkedin_watcher"
        watcher.check_for_updates() # Should not raise error

