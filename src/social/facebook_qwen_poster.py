"""
Facebook Qwen Poster.

Generates Facebook post copy using Qwen CLI and publishes via Playwright.
This module is intentionally CLI-friendly so orchestration layers can execute
it as a terminal command.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional


def _load_env() -> None:
    """Load .env values when python-dotenv is available."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # dotenv is optional at runtime
        pass


def _resolve_qwen_path() -> str:
    default_bin = "qwen.cmd" if os.name == "nt" else "qwen"
    configured = os.getenv("QWEN_PATH", default_bin)
    resolved = shutil.which(configured)

    if resolved:
        return resolved

    if os.name == "nt":
        npm_path = os.path.expandvars(r"%APPDATA%\npm\qwen.cmd")
        if os.path.exists(npm_path):
            return npm_path

    return configured


def _normalize_qwen_output(raw_output: str) -> str:
    """Clean common assistant wrappers and keep plain post text."""
    text = raw_output.strip()
    if not text:
        return ""

    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        lowered = stripped.lower()
        if lowered in {"facebook post:", "post:", "caption:"}:
            continue
        if lowered.startswith("here is") or lowered.startswith("here's"):
            continue
        cleaned_lines.append(line.rstrip())

    cleaned = "\n".join(cleaned_lines).strip()
    if len(cleaned) > 2200:
        cleaned = cleaned[:2197].rstrip() + "..."
    return cleaned


def build_qwen_facebook_prompt(topic_prompt: str, seed_content: Optional[str] = None) -> str:
    seed = (seed_content or "").strip()
    seed_block = f"\nSeed content:\n{seed}\n" if seed else ""
    return (
        "You are a social media strategist.\n"
        "Write ONE Facebook post in plain text.\n"
        "Rules:\n"
        "- No markdown fences.\n"
        "- No labels like 'Facebook Post:'.\n"
        "- Max 1200 characters.\n"
        "- Clear CTA.\n"
        "- Professional but human tone.\n"
        f"{seed_block}"
        f"Prompt: {topic_prompt.strip()}\n"
        "Output ONLY the final post text."
    )


def generate_facebook_post_with_qwen(
    topic_prompt: str,
    seed_content: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate Facebook post text via Qwen CLI."""
    prompt = build_qwen_facebook_prompt(topic_prompt, seed_content)
    qwen_path = _resolve_qwen_path()
    timeout = timeout_seconds or int(os.getenv("QWEN_TIMEOUT_SECONDS", "120"))
    cmd = [qwen_path, "-y", "--input-format", "text"]

    started = time.time()
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Qwen CLI not found at '{qwen_path}'.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Qwen CLI timed out after {timeout}s.") from exc

    duration_ms = int((time.time() - started) * 1000)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"Qwen CLI failed ({result.returncode}): {stderr}")

    generated = _normalize_qwen_output(result.stdout or "")
    if not generated:
        raise RuntimeError("Qwen CLI returned empty output.")

    return {
        "success": True,
        "prompt": topic_prompt,
        "command": cmd,
        "duration_ms": duration_ms,
        "generated_content": generated,
    }


def post_to_facebook_with_playwright(
    content: str,
    dry_run: bool,
    headless: bool,
) -> Dict[str, Any]:
    """Publish generated post text to Facebook via Playwright."""
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "message": "[DRY RUN] Facebook post skipped.",
            "posted_content_preview": content[:200],
        }

    composer_url = os.getenv("FACEBOOK_COMPOSER_URL", "").strip()
    if not composer_url:
        raise RuntimeError("FACEBOOK_COMPOSER_URL is required for live posting.")

    session_dir = Path(os.getenv("FACEBOOK_SESSION_DIR", "facebook_session")).resolve()
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except Exception as exc:
        raise RuntimeError(
            "Playwright is not available. Install with 'pip install playwright' "
            "and run 'playwright install chromium'."
        ) from exc

    login_wait_seconds = int(os.getenv("FACEBOOK_LOGIN_WAIT_SECONDS", "600"))
    browser_channel = os.getenv("FACEBOOK_BROWSER_CHANNEL", "").strip() or None

    def _looks_like_login_url(url: str) -> bool:
        lowered = (url or "").lower()
        return "facebook.com/login" in lowered or "/login" in lowered

    def _looks_like_login_page() -> bool:
        """
        Facebook sometimes serves login forms on URLs that are not clearly /login.
        Detect by either URL pattern or presence of login form fields.
        """
        if _looks_like_login_url(page.url):
            return True
        try:
            has_email = page.locator("input[name='email'], input#email").count() > 0
            has_pass = (
                page.locator("input[name='pass'], input#pass, input[type='password']").count() > 0
            )
            return bool(has_email and has_pass)
        except Exception:
            return False

    with sync_playwright() as p:
        launch_kwargs: Dict[str, Any] = {
            "user_data_dir": str(session_dir),
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--lang=en-US",
            ],
            "locale": "en-US",
            "viewport": {"width": 1280, "height": 900},
        }
        if browser_channel:
            launch_kwargs["channel"] = browser_channel

        context = p.chromium.launch_persistent_context(**launch_kwargs)
        # Always open a new tab in the persistent browser context for each post attempt.
        page = context.new_page()
        if not headless:
            try:
                page.bring_to_front()
            except Exception:
                pass

        try:
            page.goto(composer_url, wait_until="domcontentloaded", timeout=60000)
            if not headless:
                try:
                    page.bring_to_front()
                except Exception:
                    pass

            # If redirected to login, local session is not authenticated.
            if _looks_like_login_page():
                if headless:
                    raise RuntimeError(
                        "Facebook session is not logged in. "
                        "Run with FACEBOOK_HEADLESS=false and complete login."
                    )

                # Keep the same browser tab open so the user can authenticate.
                deadline = time.time() + max(10, login_wait_seconds)
                while time.time() < deadline:
                    if not _looks_like_login_page():
                        break
                    page.wait_for_timeout(2000)

                if _looks_like_login_page():
                    raise RuntimeError(
                        f"Facebook login not completed within {login_wait_seconds}s. "
                        "Please login in the opened browser tab and retry."
                    )

                # Re-open composer in the same tab after login.
                page.goto(composer_url, wait_until="domcontentloaded", timeout=60000)
                if not headless:
                    try:
                        page.bring_to_front()
                    except Exception:
                        pass

            def _first_visible(selectors, timeout_ms=4500):
                for selector in selectors:
                    try:
                        loc = page.locator(selector).first
                        loc.wait_for(state="visible", timeout=timeout_ms)
                        return loc
                    except PlaywrightTimeoutError:
                        continue
                return None

            page.wait_for_timeout(2000)

            # 1) Try direct textbox in feed/dialog.
            composer = _first_visible(
                [
                    "div[role='dialog'] div[role='textbox'][contenteditable='true']",
                    "div[role='dialog'] div[contenteditable='true'][data-lexical-editor='true']",
                    "div[role='textbox'][contenteditable='true']",
                    "div[aria-label*='Write something'][role='textbox']",
                ]
            )

            # 2) If missing, click feed composer trigger, then look again in modal.
            if not composer:
                trigger = _first_visible(
                    [
                        "div[role='button'][aria-label*=\"What's on your mind\"]",
                        "div[role='button'][aria-label*='on your mind']",
                        "div[role='button']:has-text(\"What's on your mind\")",
                        "div[role='button']:has-text('on your mind')",
                        "span:has-text(\"What's on your mind\")",
                        "div[aria-label='Create post']",
                        "div[aria-label='Create a post']",
                    ],
                    timeout_ms=3500,
                )
                if trigger:
                    try:
                        trigger.click()
                    except Exception:
                        page.keyboard.press("Tab")
                    page.wait_for_timeout(1800)

                composer = _first_visible(
                    [
                        "div[role='dialog'] div[role='textbox'][contenteditable='true']",
                        "div[role='dialog'] div[contenteditable='true'][data-lexical-editor='true']",
                        "div[role='textbox'][contenteditable='true']",
                    ],
                    timeout_ms=5000,
                )

            if not composer:
                debug_dir = session_dir / "debug_screenshots"
                debug_dir.mkdir(parents=True, exist_ok=True)
                shot = debug_dir / f"facebook_composer_not_found_{int(time.time())}.png"
                try:
                    page.screenshot(path=str(shot), full_page=True)
                except Exception:
                    pass
                raise RuntimeError(f"Could not find Facebook post composer textbox. Screenshot: {shot}")

            composer.click()
            page.keyboard.press("Control+A")
            page.keyboard.type(content, delay=18)

            post_button = _first_visible(
                [
                    "div[role='dialog'] div[aria-label='Post'][role='button']",
                    "div[role='dialog'] div[role='button']:has-text('Post')",
                    "div[aria-label='Post'][role='button']",
                    "div[role='button']:has-text('Post')",
                    "button:has-text('Post')",
                    "button[type='submit']",
                ],
                timeout_ms=7000,
            )

            if not post_button:
                raise RuntimeError("Could not find Facebook Post button.")

            post_button.click(force=True)
            page.wait_for_timeout(5000)
            keep_open_seconds = int(os.getenv("FACEBOOK_KEEP_OPEN_SECONDS", "0"))
            if keep_open_seconds > 0 and not headless:
                page.wait_for_timeout(keep_open_seconds * 1000)

            return {
                "success": True,
                "dry_run": False,
                "message": "Facebook post submitted via Playwright.",
                "composer_url": composer_url,
                "keep_open_seconds": keep_open_seconds,
            }
        finally:
            context.close()


def generate_and_post_facebook(
    topic_prompt: str,
    seed_content: Optional[str],
    dry_run: bool,
    headless: bool,
) -> Dict[str, Any]:
    """Generate with Qwen then publish via Playwright."""
    generation = generate_facebook_post_with_qwen(topic_prompt, seed_content=seed_content)
    posting = post_to_facebook_with_playwright(
        content=generation["generated_content"],
        dry_run=dry_run,
        headless=headless,
    )
    return {
        "success": True,
        "generation": generation,
        "posting": posting,
    }


def prepare_facebook_session() -> Dict[str, Any]:
    """
    Open persistent browser profile so the user can log in once.

    This is an operator setup action and intentionally non-headless.
    """
    composer_url = os.getenv("FACEBOOK_COMPOSER_URL", "").strip()
    if not composer_url:
        raise RuntimeError("FACEBOOK_COMPOSER_URL is required.")

    session_dir = Path(os.getenv("FACEBOOK_SESSION_DIR", "facebook_session")).resolve()
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError(
            "Playwright is not available. Install with 'pip install playwright' "
            "and run 'playwright install chromium'."
        ) from exc

    with sync_playwright() as p:
        browser_channel = os.getenv("FACEBOOK_BROWSER_CHANNEL", "").strip() or None
        launch_kwargs: Dict[str, Any] = {
            "user_data_dir": str(session_dir),
            "headless": False,
            "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            "viewport": {"width": 1280, "height": 900},
        }
        if browser_channel:
            launch_kwargs["channel"] = browser_channel

        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(composer_url, wait_until="domcontentloaded", timeout=60000)
        print(
            "Facebook login session window opened.\n"
            "Sign in manually, then press Enter here to save session and close."
        )
        input()
        context.close()

    return {
        "success": True,
        "session_dir": str(session_dir),
        "message": "Facebook session captured.",
    }


def main() -> int:
    _load_env()

    parser = argparse.ArgumentParser(description="Qwen + Playwright Facebook automation")
    parser.add_argument(
        "--mode",
        choices=["generate", "post", "generate-and-post", "login"],
        default="generate-and-post",
    )
    parser.add_argument("--prompt", help="Topic prompt for Qwen generation")
    parser.add_argument("--content", help="Existing content (for post mode or as seed)")
    parser.add_argument("--dry-run", action="store_true", help="Do not publish live")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Use headless browser mode for live posting",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON response")
    args = parser.parse_args()

    dry_run = args.dry_run or os.getenv("DRY_RUN", "false").lower() == "true"
    headless = args.headless or os.getenv("FACEBOOK_HEADLESS", "false").lower() == "true"

    try:
        if args.mode == "generate":
            if not args.prompt:
                raise RuntimeError("--prompt is required for generate mode.")
            result = generate_facebook_post_with_qwen(args.prompt, seed_content=args.content)
        elif args.mode == "post":
            if not args.content:
                raise RuntimeError("--content is required for post mode.")
            result = post_to_facebook_with_playwright(args.content, dry_run=dry_run, headless=headless)
        elif args.mode == "login":
            result = prepare_facebook_session()
        else:
            if not args.prompt:
                raise RuntimeError("--prompt is required for generate-and-post mode.")
            result = generate_and_post_facebook(
                topic_prompt=args.prompt,
                seed_content=args.content,
                dry_run=dry_run,
                headless=headless,
            )

        if args.json:
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        error_payload = {"success": False, "error": str(exc)}
        if args.json:
            print(json.dumps(error_payload))
        else:
            print(json.dumps(error_payload, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
