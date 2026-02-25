"""
LinkedIn Watcher.

Monitors LinkedIn for Notifications and Messages using Playwright.
Extracts unread counts and details.
"""

import time
import hashlib
import random
import os
from pathlib import Path

from .base import BaseWatcher
from src.lib.vault import vault

class LinkedInWatcher(BaseWatcher):
    def __init__(self, interval: int = 600, headless: bool = True):
        # Safety: LinkedIn is very strict. Default interval increased to 10 mins (600s).
        # We will also add randomization to this interval in the main loop if possible,
        # but here we rely on internal sleeps.
        super().__init__("linkedin_watcher", interval, domain=os.getenv("LINKEDIN_DOMAIN", "business"))
        self.headless = headless
        self.session_path = Path("session-data/linkedin")
        self.browser = None
        self.context = None
        self.page = None

    def _setup_browser(self):
        try:
            from playwright.sync_api import sync_playwright

            self.p = sync_playwright().start()
            abs_session_path = self.session_path.resolve()
            
            self.logger.info(f"Launching LinkedIn Browser (Headless: {self.headless})...")
            self.context = self.p.chromium.launch_persistent_context(
                user_data_dir=str(abs_session_path),
                headless=self.headless,
                # Safety: Disable automation flags and set realistic User Agent
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ],
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            # Safety: Random start delay
            time.sleep(random.uniform(2, 5))
            
            self.page.goto("https://www.linkedin.com/feed/")
            
            # Check if logged in
            try:
                self.page.wait_for_selector('.global-nav__nav', timeout=15000)
                self.logger.info("LinkedIn Feed loaded.")
            except:
                self.logger.warning("LinkedIn not logged in. Please login manually in non-headless mode.")
                
        except Exception as e:
            self.logger.error(f"LinkedIn Browser Setup Failed: {e}")
            # Graceful degradation: alert and keep watcher alive.
            try:
                vault.ensure_structure()
                alert_path = vault.dirs["alerts"] / f"{int(time.time())}_linkedin_watcher_playwright_error.md"
                alert_path.write_text(
                    f"# LinkedIn Watcher Error\n\n"
                    f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n\n"
                    f"Error: {e}\n\n"
                    "Watcher will keep running but cannot monitor LinkedIn until this is fixed.\n",
                    encoding="utf-8",
                )
                self.logger.log_action(
                    action_type="watcher_error",
                    result="error",
                    target=str(alert_path),
                    details={"watcher": "linkedin", "error": str(e)[:200]},
                )
            except Exception:
                pass

    def check_for_updates(self):
        if not self.page:
            self._setup_browser()
            if not self.page: return

        try:
            # Safety: Human-like delay before acting
            time.sleep(random.uniform(5.0, 15.0))

            # 1. Check Messaging Badge
            # Safety: Only check messaging if we are "lucky" or every cycle? 
            # Let's check badges (low cost) but only navigate if badge > 0.
            
            msg_badge = self.page.query_selector('.global-nav__nav-item--messaging .notification-badge__count')
            if msg_badge:
                count = msg_badge.inner_text()
                if int(count) > 0:
                    self.logger.info(f"Found {count} unread LinkedIn messages.")
                    # Safety: Pause before clicking
                    time.sleep(random.uniform(2, 4))
                    self._process_messages()
            
            # Safety: Random pause between checks
            time.sleep(random.uniform(3, 8))

            # 2. Check Notifications Badge
            notif_badge = self.page.query_selector('.global-nav__nav-item--notifications .notification-badge__count')
            if notif_badge:
                count = notif_badge.inner_text()
                if int(count) > 0:
                    self.logger.info(f"Found {count} unread LinkedIn notifications.")
                    time.sleep(random.uniform(2, 4))
                    self._process_notifications()

        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")

    def _process_messages(self):
        """Go to messaging and scrape latest unread."""
        try:
            self.page.goto("https://www.linkedin.com/messaging/")
            
            # Safety: Human reading time
            self.page.wait_for_timeout(random.randint(3000, 6000))
            
            self.page.wait_for_selector(".msg-conversation-listitem", timeout=10000)
            
            # Find unread conversations (usually have a blue dot or specific class)
            # Selector for unread indicator: .msg-conversation-card__unread-count or similar
            # Or check for 'font-weight: bold' classes.
            
            # For stability, we will grab the first conversation, check if it's new.
            
            first_conv = self.page.query_selector(".msg-conversation-listitem")
            if first_conv:
                first_conv.click()
                
                # Safety: Wait for message load
                self.page.wait_for_timeout(random.randint(2000, 4000))
                
                self.page.wait_for_selector(".msg-s-message-list-content", timeout=5000)
                
                # Get last message text
                msgs = self.page.query_selector_all(".msg-s-event-listitem__body")
                if msgs:
                    last_msg_text = msgs[-1].inner_text()
                    
                    # Get Sender
                    sender_elem = self.page.query_selector(".msg-entity-lockup__content-title")
                    sender_name = sender_elem.inner_text() if sender_elem else "Unknown"
                    
                    # Dedup
                    msg_hash = hashlib.md5(f"{sender_name}:{last_msg_text}".encode()).hexdigest()
                    if msg_hash not in self.processed_ids:
                        
                        content = f"# Incoming LinkedIn Message\n\n**From:** {sender_name}\n\n## Message\n{last_msg_text}"
                        self.create_action_file(
                            type="message",
                            content=content,
                            metadata={"platform": "linkedin", "sender": sender_name},
                            priority="medium"
                        )
                        self.processed_ids.add(msg_hash)
                        self.logger.info(f"Processed LinkedIn message from {sender_name}")

        except Exception as e:
            self.logger.error(f"Error processing LinkedIn messages: {e}")

    def _process_notifications(self):
        """Go to notifications page and scrape."""
        try:
            self.page.goto("https://www.linkedin.com/notifications/")
            
            # Safety: Wait for load and "read"
            self.page.wait_for_timeout(random.randint(4000, 8000))
            
            self.page.wait_for_selector(".nt-card", timeout=10000)
            
            # Get first notification
            first_notif = self.page.query_selector(".nt-card")
            if first_notif:
                text = first_notif.inner_text()
                
                notif_hash = hashlib.md5(text.encode()).hexdigest()
                if notif_hash not in self.processed_ids:
                    
                    self.create_action_file(
                        type="notification",
                        content=f"# LinkedIn Notification\n\n{text}",
                        metadata={"platform": "linkedin", "type": "notification"},
                        priority="low"
                    )
                    self.processed_ids.add(notif_hash)
                    self.logger.info("Processed LinkedIn notification")
                    
        except Exception as e:
            self.logger.error(f"Error processing LinkedIn notifications: {e}")

    def stop(self):
        super().stop()
        if self.context: self.context.close()
        if self.p: self.p.stop()

if __name__ == "__main__":
    watcher = LinkedInWatcher(interval=60, headless=False)
    watcher.start()
