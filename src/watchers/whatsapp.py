"""
WhatsApp Watcher.

Monitors WhatsApp Web for new messages using Playwright.
Extracts unread messages, creates Action Files, and handles session persistence.
"""

import time
import os
import re
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseWatcher
from src.lib.vault import vault

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, interval: int = 60, headless: bool = True):
        # Safety: WhatsApp can detect robotic intervals. We will apply jitter.
        super().__init__("whatsapp_watcher", interval, domain=os.getenv("WHATSAPP_DOMAIN", "personal"))
        self.headless = headless
        self.session_path = Path("session-data/whatsapp")
        self.browser = None
        self.context = None
        self.page = None
        
        # Selectors (Subject to change by WhatsApp, maintain these)
        self.SELECTORS = {
            'unread_badge': 'span[aria-label*="unread"]', 
            'chat_list_item': 'div[role="listitem"]',
            'message_bubble': 'div[class*="message-in"]',
            'message_text': 'span.selectable-text',
            'sender_name': 'span[dir="auto"]', # In header
            'header': 'header',
        }

    def _setup_browser(self):
        """Initialize Playwright browser with persistent context."""
        try:
            from playwright.sync_api import sync_playwright

            self.p = sync_playwright().start()
            
            # Ensure absolute path for session
            abs_session_path = self.session_path.resolve()
            
            self.logger.info(f"Launching browser (Headless: {self.headless})...")
            self.context = self.p.chromium.launch_persistent_context(
                user_data_dir=str(abs_session_path),
                headless=self.headless,
                # Safety: specific args to avoid basic bot detection
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-infobars',
                ], 
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.page.goto("https://web.whatsapp.com")
            
            self.logger.info("Waiting for WhatsApp Web to load...")
            # specific selector for the chat list pane
            try:
                self.page.wait_for_selector('div[id="pane-side"]', timeout=60000)
                self.logger.info("WhatsApp Web loaded successfully.")
            except Exception:
                self.logger.warning("Timeout waiting for WhatsApp load. Scan QR code if running with head.")

        except Exception as e:
            self.logger.error(f"Failed to setup Playwright: {e}")
            # Graceful degradation: raise an alert instead of crashing the watcher loop.
            try:
                vault.ensure_structure()
                alert_path = vault.dirs["alerts"] / f"{int(time.time())}_whatsapp_watcher_playwright_error.md"
                alert_path.write_text(
                    f"# WhatsApp Watcher Error\n\n"
                    f"Timestamp: {datetime.utcnow().isoformat()}Z\n\n"
                    f"Error: {e}\n\n"
                    "Watcher will keep running but cannot monitor WhatsApp until this is fixed.\n",
                    encoding="utf-8",
                )
                self.logger.log_action(
                    action_type="watcher_error",
                    result="error",
                    target=str(alert_path),
                    details={"watcher": "whatsapp", "error": str(e)[:200]},
                )
            except Exception:
                pass

    def check_for_updates(self):
        """Check for unread chats and process them."""
        # Safety: Random jitter to poll interval to appear human
        # We handle this by sleeping randomly BEFORE the check logic if called in a tight loop,
        # but since BaseWatcher handles the main sleep, we'll just add small human-like delays inside.
        
        if not self.page:
            self._setup_browser()
            if not self.page: 
                return

        try:
            # Look for unread badges in the DOM
            # Note: query_selector_all is fast
            unread_badges = self.page.query_selector_all(self.SELECTORS['unread_badge'])
            
            if unread_badges:
                self.logger.info(f"Found {len(unread_badges)} unread conversations.")
                
                # Safety: Don't process everything instantly. 
                # Pick one, process it, then wait a bit.
                
                badge = unread_badges[0]
                
                # Safety: Human reaction time
                time.sleep(random.uniform(1.0, 3.0))
                
                # Go up to the chat row
                try:
                    chat_row = badge.xpath("ancestor::div[@role='row']")[0]
                    chat_row.click()
                    
                    # Safety: Wait for chat load and animation
                    self.page.wait_for_timeout(random.randint(2000, 4000))
                    
                    # Process the open chat
                    self._process_open_chat()
                    
                    # Safety: Return to neutral state occasionally
                    if random.random() > 0.7:
                        self.page.keyboard.press("Escape")
                        
                except Exception as e:
                    self.logger.error(f"Error interacting with chat row: {e}")
                
        except Exception as e:
            self.logger.error(f"Error checking WhatsApp updates: {e}")

    def _process_open_chat(self):
        """Scrape messages from the currently open chat."""
        try:
            # Get sender name from header
            header = self.page.query_selector("header")
            sender_name = "Unknown"
            if header:
                title_elem = header.query_selector('span[dir="auto"]')
                if title_elem:
                    sender_name = title_elem.inner_text()
            
            # Get last few messages
            # We look for "message-in" (received messages)
            # This selector is heuristic; WA classes are obfuscated often.
            # Usually div[role="application"] contains the messages.
            
            # Get all message text elements
            msgs = self.page.query_selector_all("span.selectable-text")
            
            if not msgs:
                self.logger.warning(f"No text found in chat with {sender_name}")
                return

            # Grab the last message
            last_msg = msgs[-1].inner_text()
            
            # Check if we already processed this message? 
            # Ideally we'd use a hash of (sender + message + timestamp).
            # For this 'Strict' implementation, we will hash the content and check.
            
            import hashlib
            msg_hash = hashlib.md5(f"{sender_name}:{last_msg}".encode()).hexdigest()
            
            if msg_hash in self.processed_ids:
                self.logger.info(f"Message from {sender_name} already processed.")
                return
            
            self.logger.info(f"New message from {sender_name}: {last_msg[:50]}...")
            
            # Create Action File
            content = f"# Incoming WhatsApp Message\n\n**From:** {sender_name}\n\n## Message\n{last_msg}"
            
            self.create_action_file(
                type="message",
                content=content,
                metadata={
                    "platform": "whatsapp",
                    "sender": sender_name,
                    "hash": msg_hash
                },
                priority="high" # Assume WA is high priority
            )
            
            self.processed_ids.add(msg_hash)
            
        except Exception as e:
            self.logger.error(f"Error processing open chat: {e}")

    def stop(self):
        """Cleanup."""
        super().stop()
        if self.context:
            self.context.close()
        if self.p:
            self.p.stop()

if __name__ == "__main__":
    # Debug run
    watcher = WhatsAppWatcher(interval=30, headless=False)
    watcher.start()
