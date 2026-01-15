"""
WhatsApp Watcher.

Monitors WhatsApp Web for new messages using Playwright.
Requires an authorized WhatsApp Web session (user must scan QR code once).
"""

import time
from typing import Dict, Any
from .base import BaseWatcher
from playwright.sync_api import sync_playwright

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, interval: int = 60, headless: bool = True):
        super().__init__("whatsapp_watcher", interval)
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    def _setup_browser(self):
        """Initialize browser and load WhatsApp Web."""
        try:
            self.p = sync_playwright().start()
            # Use persistent context to save session
            user_data_dir = "whatsapp_session"
            self.context = self.p.chromium.launch_persistent_context(
                user_data_dir,
                headless=self.headless,
                # args to mimic real browser/bypass some detections could go here
            )
            self.page = self.context.new_page()
            self.page.goto("https://web.whatsapp.com")

            # Wait for load - in real impl, wait for specific element indicating login
            # self.page.wait_for_selector("#pane-side", timeout=30000)
            self.logger.info("WhatsApp Web loaded. waiting for login if needed.")

        except Exception as e:
            self.logger.error(f"Failed to setup Playwright for WhatsApp: {e}")

    def check_for_updates(self):
        """Check for unread indicators."""
        if not self.page:
            self._setup_browser()
            if not self.page:
                return

        try:
            # Look for unread badges
            # Selector strategies change often on WA Web, this is fragile and needs maintenance
            # Common selector for unread badge: span[aria-label*="unread"]

            unread_chats = self.page.query_selector_all('span[aria-label*="unread"]')

            if unread_chats:
                self.logger.info(f"Found {len(unread_chats)} unread chats.")

                # For each unread:
                # 1. Click chat (careful not to mark read if we want to preserve state?
                # WA marks read on click. Maybe just extract preview text from sidebar?)

                # Extracting preview from sidebar is safer to avoid marking as read unintendedly
                # But to get full content we must open it.
                # Project requirement: Monitor urgent messages.

                # For MVP: Just log we found unread count.
                # Future: Click, scrape, back.

                pass

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")

    def stop(self):
        """Cleanup browser."""
        super().stop()
        if self.context:
            self.context.close()
        if self.p:
            self.p.stop()

if __name__ == "__main__":
    watcher = WhatsAppWatcher(interval=30, headless=False) # Headless False for debugging/login
    watcher.start()
