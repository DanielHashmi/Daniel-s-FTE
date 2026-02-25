"""
Instagram Playwright Poster.

Posts an image + caption to Instagram using a persistent Playwright session.
This module is CLI-friendly for orchestration/MCP execution.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

INSTAGRAM_FILE_INPUT_SELECTORS: tuple[str, ...] = (
    "input[type='file'][accept*='image']",
    "input[type='file'][accept*='video']",
    "input[type='file']",
)

INSTAGRAM_CREATE_ENTRY_SELECTORS: tuple[str, ...] = (
    "a[href='/create/select/']",
    "a[href='/create/style/']",
    "svg[aria-label='New post']",
    "button[aria-label='New post']",
    "div[role='button'][aria-label='New post']",
    "div[role='button']:has-text('Create')",
    "button:has-text('Create')",
)

INSTAGRAM_POST_PICKER_SELECTORS: tuple[str, ...] = (
    "div[role='menuitem']:has-text('Post')",
    "div[role='dialog'] div[role='button']:has-text('Post')",
    "button:has-text('Post')",
)

INSTAGRAM_DIRECT_CREATE_PATHS: tuple[str, ...] = (
    "/create/select/",
    "/create/style/",
)


def _load_env() -> None:
    """Load .env values when python-dotenv is available."""
    try:
        from dotenv import load_dotenv

        load_dotenv(override=True)
    except Exception:
        pass


def _normalize_hashtags(raw: Optional[str]) -> str:
    if not raw:
        return ""
    tokens = [tok.strip() for tok in raw.replace("\n", " ").replace(",", " ").split(" ") if tok.strip()]
    out = []
    seen = set()
    for token in tokens:
        tag = token if token.startswith("#") else f"#{token}"
        cleaned = "".join(ch for ch in tag if ch.isalnum() or ch in {"#", "_"})
        if cleaned in {"", "#"}:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return " ".join(out[:12])


def _caption_with_hashtags(caption: str, hashtags: Optional[str]) -> str:
    body = (caption or "").strip()
    tags = _normalize_hashtags(hashtags)
    if tags:
        if body:
            body = f"{body}\n\n{tags}"
        else:
            body = tags
    if len(body) > 2200:
        body = body[:2197].rstrip() + "..."
    return body


def _guess_suffix(image_url: str, content_type: str) -> str:
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    parsed = urllib.parse.urlparse(image_url)
    ext = Path(parsed.path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def _download_image(image_url: str, tmp_dir: Path) -> Path:
    if not image_url.strip().lower().startswith(("http://", "https://")):
        raise RuntimeError("Instagram Playwright mode requires an http/https image URL.")

    req = urllib.request.Request(
        image_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
        if not data:
            raise RuntimeError("Failed to download Instagram image: empty response.")
        content_type = str(resp.headers.get("Content-Type", "")).lower()

    suffix = _guess_suffix(image_url, content_type)
    file_path = tmp_dir / f"instagram_upload_{int(time.time() * 1000)}{suffix}"
    file_path.write_bytes(data)
    return file_path


def _has_any_locator(page: Any, selectors: list[str]) -> bool:
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def _looks_like_instagram_login_page(page: Any) -> bool:
    try:
        url = (page.url or "").lower()
    except Exception:
        url = ""

    if "/accounts/login" in url:
        return True

    if _has_any_locator(
        page,
        [
            "input[name='username']",
            "input[name='password']",
            "input[type='password']",
        ],
    ):
        return True

    logged_out_indicators = _has_any_locator(
        page,
        [
            "a[href*='/accounts/login']",
            "button:has-text('Log in')",
            "a:has-text('Log in')",
        ],
    )
    logged_in_indicators = _has_any_locator(
        page,
        [
            "a[href='/create/select/']",
            "a[href='/direct/inbox/']",
            "a[href='/explore/']",
            "a[href*='/accounts/edit/']",
            "svg[aria-label='New post']",
        ],
    )

    return bool(logged_out_indicators and not logged_in_indicators)


def _instagram_auth_marker_path(session_dir: Path) -> Path:
    return session_dir / ".instagram_authenticated"


def _mark_instagram_authenticated(session_dir: Path) -> None:
    try:
        _instagram_auth_marker_path(session_dir).write_text(
            f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\n",
            encoding="utf-8",
        )
    except Exception:
        # Non-fatal: posting can still continue even if marker write fails.
        pass


def _detect_windows_default_chromium_channel() -> Optional[str]:
    if os.name != "nt":
        return None

    def _channel_from_text(raw: str) -> Optional[str]:
        lowered = (raw or "").strip().lower()
        if "msedge.exe" in lowered or "microsoft\\edge" in lowered or "edge" in lowered:
            return "msedge"
        if "chrome.exe" in lowered or "google\\chrome" in lowered or "chrome" in lowered:
            return "chrome"
        return None

    try:
        import winreg

        # Preferred lookup: per-user protocol association.
        for protocol in ("https", "http"):
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    rf"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\{protocol}\UserChoice",
                ) as key:
                    prog_id, _ = winreg.QueryValueEx(key, "ProgId")
                channel = _channel_from_text(str(prog_id))
                if channel:
                    return channel
            except Exception:
                continue

        # Fallback lookup: shell open command resolution.
        for protocol in ("https", "http"):
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CLASSES_ROOT,
                    rf"{protocol}\shell\open\command",
                ) as key:
                    command, _ = winreg.QueryValueEx(key, "")
                channel = _channel_from_text(str(command))
                if channel:
                    return channel
            except Exception:
                continue
    except Exception:
        return None

    return None


def _resolve_browser_channel(env_key: str) -> tuple[Optional[str], bool]:
    """
    Resolve Playwright channel.
    Returns (channel, strict):
    - strict=True means user explicitly set a channel and launch should fail if unavailable.
    - strict=False means channel is auto-selected and may fallback to bundled Chromium.
    """
    raw = os.getenv(env_key, "").strip()
    lowered = raw.lower()

    if raw:
        if lowered in {"none", "bundled", "chromium"}:
            return None, True
        if lowered != "default":
            return raw, True

    detected = _detect_windows_default_chromium_channel()
    if detected:
        return detected, False

    return None, False


def _launch_chromium_context(
    playwright: Any,
    launch_kwargs: Dict[str, Any],
    channel: Optional[str],
    strict_channel: bool,
) -> tuple[Any, str]:
    kwargs = dict(launch_kwargs)

    if channel:
        kwargs["channel"] = channel
        try:
            return playwright.chromium.launch_persistent_context(**kwargs), channel
        except Exception as exc:
            if strict_channel:
                raise RuntimeError(
                    f"Failed to launch browser channel '{channel}'. "
                    f"Set {('INSTAGRAM_BROWSER_CHANNEL')}=default or unset it to auto-fallback. "
                    f"Original error: {exc}"
                ) from exc

    return playwright.chromium.launch_persistent_context(**launch_kwargs), "chromium"


def _short_error(exc: Exception) -> str:
    text = str(exc).strip().replace("\r", " ").replace("\n", " ")
    return text[:320]


def _error_chain_text(exc: Exception) -> str:
    parts: list[str] = []
    seen = set()
    current: Optional[BaseException] = exc
    depth = 0
    while current is not None and depth < 8:
        text = str(current).strip()
        if text and text not in seen:
            parts.append(text)
            seen.add(text)
        next_exc = current.__cause__ or current.__context__
        if next_exc is current:
            break
        current = next_exc
        depth += 1
    return " | ".join(parts)


def _is_profile_lock_error(exc: Exception) -> bool:
    lowered = _error_chain_text(exc).lower()
    return any(
        token in lowered
        for token in (
            "user data directory is already in use",
            "profile appears to be in use",
            "process singleton",
            "singletonlock",
            "profile lock",
            "single_instance",
        )
    )


def _looks_like_profile_store_corruption(exc: Exception) -> bool:
    lowered = _error_chain_text(exc).lower()
    return (
        ("settings version is not" in lowered and "crashpad" in lowered)
        or "exitcode=2147483651" in lowered
        or "exitcode=21" in lowered
    )


def _same_path(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except Exception:
        return str(a) == str(b)


def _rotate_session_dir(session_dir: Path) -> Optional[Path]:
    try:
        if not session_dir.exists():
            session_dir.mkdir(parents=True, exist_ok=True)
            return None
        backup_dir = session_dir.with_name(f"{session_dir.name}_corrupt_{int(time.time())}")
        shutil.move(str(session_dir), str(backup_dir))
        session_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    except Exception:
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return None


def _rotate_crashpad_dir(user_data_dir: Path) -> Optional[Path]:
    crashpad_dir = user_data_dir / "Crashpad"
    try:
        if not crashpad_dir.exists():
            return None
        backup_dir = user_data_dir / f"Crashpad_corrupt_{int(time.time())}"
        shutil.move(str(crashpad_dir), str(backup_dir))
        return backup_dir
    except Exception:
        return None


def _channel_process_names(channel: Optional[str]) -> list[str]:
    normalized = (channel or "").strip().lower()
    if normalized == "msedge":
        return ["msedge.exe"]
    if normalized == "chrome":
        return ["chrome.exe"]
    return ["msedge.exe", "chrome.exe"]


def _close_running_channel_processes(channel: Optional[str]) -> bool:
    if os.name != "nt":
        return False

    attempted = False
    for proc_name in _channel_process_names(channel):
        try:
            subprocess.run(
                ["taskkill", "/IM", proc_name, "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=20,
            )
            attempted = True
        except Exception:
            continue

    delay_raw = os.getenv("INSTAGRAM_BROWSER_CLOSE_RETRY_DELAY_SECONDS", "2").strip()
    try:
        delay_seconds = max(0.0, float(delay_raw))
    except Exception:
        delay_seconds = 2.0
    if attempted and delay_seconds > 0:
        time.sleep(delay_seconds)
    return attempted


def _system_profile_close_retry_enabled() -> bool:
    # Disabled by default: force-closing browser processes is disruptive for normal usage.
    return os.getenv("INSTAGRAM_SYSTEM_PROFILE_CLOSE_RETRY", "false").strip().lower() == "true"


def _system_profile_crashpad_reset_enabled() -> bool:
    return os.getenv("INSTAGRAM_SYSTEM_PROFILE_RESET_CRASHPAD", "false").strip().lower() == "true"


def _connect_existing_browser_enabled() -> bool:
    return os.getenv("INSTAGRAM_CONNECT_EXISTING_BROWSER", "false").strip().lower() == "true"


def _cdp_attach_timeout_ms() -> int:
    try:
        return max(1000, int(os.getenv("INSTAGRAM_CDP_ATTACH_TIMEOUT_MS", "15000")))
    except Exception:
        return 15000


def _cdp_url() -> str:
    return os.getenv("INSTAGRAM_CDP_URL", "http://127.0.0.1:9222").strip() or "http://127.0.0.1:9222"


def _cdp_auto_start_enabled() -> bool:
    return os.getenv("INSTAGRAM_CDP_AUTO_START", "true").strip().lower() == "true"


def _cdp_browser_restart_enabled() -> bool:
    """
    Safety gate for CDP auto-start.

    Restarting a user's primary browser can be disruptive. Keep disabled by
    default unless explicitly opted in.
    """
    return os.getenv("INSTAGRAM_CDP_ALLOW_BROWSER_RESTART", "false").strip().lower() == "true"


def _cdp_start_timeout_seconds() -> float:
    raw = os.getenv("INSTAGRAM_CDP_START_TIMEOUT_SECONDS", "10").strip()
    try:
        return max(1.0, float(raw))
    except Exception:
        return 10.0


def _cdp_port_from_url(cdp_url: str) -> Optional[int]:
    m = re.match(r"^https?://[^:/]+:(\d+)", cdp_url.strip(), re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _cdp_version_endpoint(cdp_url: str) -> str:
    return cdp_url.rstrip("/") + "/json/version"


def _wait_for_cdp_available(cdp_url: str, timeout_seconds: float) -> bool:
    deadline = time.time() + max(1.0, timeout_seconds)
    endpoint = _cdp_version_endpoint(cdp_url)
    while time.time() < deadline:
        try:
            req = urllib.request.Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                if int(getattr(resp, "status", 0) or 0) == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.6)
    return False


def _windows_channel_executable(channel: Optional[str]) -> Optional[str]:
    normalized = (channel or "").strip().lower()
    if normalized == "msedge":
        candidates = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
    elif normalized == "chrome":
        candidates = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    else:
        return None

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def _start_default_browser_with_cdp(
    *,
    channel: Optional[str],
    cdp_url: str,
    user_data_dir: Path,
    profile_directory: Optional[str],
    target_url: str,
) -> bool:
    if os.name != "nt":
        return False
    exe = _windows_channel_executable(channel)
    if not exe:
        return False
    port = _cdp_port_from_url(cdp_url)
    if not port:
        return False

    args = [
        exe,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={str(user_data_dir)}",
    ]
    if profile_directory:
        args.append(f"--profile-directory={profile_directory}")
    args += ["--new-window", target_url]

    try:
        creationflags = 0
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= int(subprocess.DETACHED_PROCESS)  # type: ignore[attr-defined]
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= int(subprocess.CREATE_NEW_PROCESS_GROUP)  # type: ignore[attr-defined]
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
        )
        return True
    except Exception:
        return False


def _default_user_data_dir_for_channel(channel: Optional[str]) -> Optional[Path]:
    local_appdata = os.getenv("LOCALAPPDATA", "").strip()
    if not local_appdata:
        return None

    normalized = (channel or "").strip().lower()
    if normalized == "msedge":
        return Path(local_appdata) / "Microsoft" / "Edge" / "User Data"
    if normalized == "chrome":
        return Path(local_appdata) / "Google" / "Chrome" / "User Data"
    return None


def _detect_last_used_profile(user_data_dir: Path) -> Optional[str]:
    local_state_path = user_data_dir / "Local State"
    if not local_state_path.exists():
        return None

    try:
        raw = local_state_path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        profile = parsed.get("profile", {}) if isinstance(parsed, dict) else {}
        candidate = str(profile.get("last_used", "")).strip()
        return candidate or None
    except Exception:
        return None


def _cookie_db_for_profile(user_data_dir: Path, profile_name: str) -> Optional[Path]:
    profile_dir = user_data_dir / profile_name
    candidates = [
        profile_dir / "Network" / "Cookies",
        profile_dir / "Cookies",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _profile_has_instagram_session(user_data_dir: Path, profile_name: str) -> bool:
    cookie_db = _cookie_db_for_profile(user_data_dir, profile_name)
    if not cookie_db:
        return False

    try:
        uri = f"file:{cookie_db.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=1.0) as conn:
            row = conn.execute(
                """
                SELECT COUNT(1)
                FROM cookies
                WHERE host_key LIKE '%instagram.com%'
                  AND name IN ('sessionid', 'ds_user_id', 'csrftoken')
                """
            ).fetchone()
            return bool(row and int(row[0]) > 0)
    except Exception:
        return False


def _detect_profile_with_instagram_session(user_data_dir: Path) -> Optional[str]:
    try:
        profile_dirs = []
        for child in user_data_dir.iterdir():
            if not child.is_dir():
                continue
            if child.name == "Default" or child.name.startswith("Profile "):
                profile_dirs.append(child.name)
    except Exception:
        return None

    scored: list[tuple[float, str]] = []
    for profile_name in profile_dirs:
        if not _profile_has_instagram_session(user_data_dir, profile_name):
            continue
        cookie_db = _cookie_db_for_profile(user_data_dir, profile_name)
        mtime = cookie_db.stat().st_mtime if cookie_db else 0.0
        scored.append((mtime, profile_name))

    if not scored:
        return None

    scored.sort(reverse=True)
    return scored[0][1]


def _resolve_instagram_profile_settings(
    channel: Optional[str],
    fallback_session_dir: Path,
) -> tuple[Path, Optional[str], str]:
    """
    Decide which browser profile Playwright should use.

    Returns:
      user_data_dir, profile_directory, profile_mode
    profile_mode: "system" | "session"
    """
    mode = os.getenv("INSTAGRAM_PROFILE_MODE", "system").strip().lower()
    configured_user_data_dir = os.getenv("INSTAGRAM_BROWSER_USER_DATA_DIR", "").strip()
    profile_name_raw = os.getenv("INSTAGRAM_PROFILE_NAME", "auto").strip()
    auto_profile_strategy = os.getenv("INSTAGRAM_AUTO_PROFILE_STRATEGY", "last_used").strip().lower()

    wants_system = mode in {"system", "default", "default_profile", "default-profile"}
    if wants_system:
        if configured_user_data_dir:
            user_data_dir = Path(configured_user_data_dir).expanduser().resolve()
        else:
            detected = _default_user_data_dir_for_channel(channel)
            if not detected:
                return fallback_session_dir, None, "session"
            user_data_dir = detected

        profile_name = profile_name_raw
        if not profile_name or profile_name.lower() == "auto":
            last_used = _detect_last_used_profile(user_data_dir)
            instagram_profile = _detect_profile_with_instagram_session(user_data_dir)
            if auto_profile_strategy in {"instagram_first", "instagram-session-first"}:
                profile_name = instagram_profile or last_used or "Default"
            else:
                profile_name = last_used or instagram_profile or "Default"
        else:
            profile_dir = user_data_dir / profile_name
            if not profile_dir.exists():
                profile_name = _detect_last_used_profile(user_data_dir) or "Default"

        return user_data_dir, profile_name, "system"

    return fallback_session_dir, None, "session"


def _pick_live_page_for_instagram(
    context: Any,
    preferred: Any | None = None,
    *,
    allow_new_page: bool,
) -> Any:
    if preferred is not None:
        try:
            if not preferred.is_closed():
                return preferred
        except Exception:
            pass

    for candidate in context.pages:
        try:
            if not candidate.is_closed():
                return candidate
        except Exception:
            continue

    if allow_new_page:
        return context.new_page()

    raise RuntimeError(
        "No live tab available in the attached browser context. "
        "Keep at least one browser tab open and retry."
    )


def _run_instagram_post_flow(
    *,
    context: Any,
    composer_url: str,
    local_image_path: Path,
    final_caption: str,
    headless: bool,
    login_wait_seconds: int,
    keep_open_seconds: int,
    session_dir: Path,
    allow_new_page: bool,
    dedicated_page: Any | None = None,
) -> None:
    if dedicated_page is not None:
        page = dedicated_page
    else:
        page = _pick_live_page_for_instagram(context, None, allow_new_page=allow_new_page)
    if not headless:
        try:
            page.bring_to_front()
        except Exception:
            pass

    def _pick_live_page(preferred: Any | None = None) -> Any:
        if dedicated_page is not None:
            try:
                if not dedicated_page.is_closed():
                    return dedicated_page
            except Exception:
                pass
            raise RuntimeError(
                "Instagram posting tab was closed during execution. "
                "Keep the tab open and retry."
            )
        return _pick_live_page_for_instagram(context, preferred, allow_new_page=allow_new_page)

    def _is_logged_in(current_page: Any) -> bool:
        return not _looks_like_instagram_login_page(current_page)

    def _goto_composer(current_page: Any) -> Any:
        target = _pick_live_page(current_page)
        target.goto(composer_url, wait_until="domcontentloaded", timeout=60000)
        target.wait_for_timeout(2000)
        return target

    def _wait_for_manual_login(current_page: Any) -> Any:
        if _is_logged_in(current_page):
            return current_page
        if headless:
            raise RuntimeError(
                "Instagram session is not logged in. Run with INSTAGRAM_HEADLESS=false and login."
            )

        deadline = time.time() + max(10, login_wait_seconds)
        latest_page = _pick_live_page(current_page)
        while time.time() < deadline:
            if dedicated_page is not None:
                latest_page = _pick_live_page(latest_page)
                if _is_logged_in(latest_page):
                    return latest_page
            else:
                for candidate in context.pages:
                    try:
                        if candidate.is_closed():
                            continue
                    except Exception:
                        continue
                    latest_page = candidate
                    if _is_logged_in(candidate):
                        return candidate
            latest_page.wait_for_timeout(2000)

        raise RuntimeError(
            f"Instagram login not completed within {login_wait_seconds}s. "
            "Please login in the opened browser tab and retry."
        )

    def _first_visible(selectors: list[str], timeout_ms: int = 5000):
        nonlocal page
        for selector in selectors:
            page = _pick_live_page(page)
            try:
                loc = page.locator(selector).first
                loc.wait_for(state="visible", timeout=timeout_ms)
                return loc
            except Exception as exc:
                if "target page, context or browser has been closed" in str(exc).lower():
                    page = _pick_live_page(None)
                    continue
                continue
        return None

    def _find_file_input() -> Any | None:
        nonlocal page
        page = _pick_live_page(page)
        scopes: list[Any] = [page]
        try:
            scopes.extend(list(page.frames))
        except Exception:
            pass

        for scope in scopes:
            for selector in INSTAGRAM_FILE_INPUT_SELECTORS:
                try:
                    candidate = scope.locator(selector).first
                    if candidate.count() > 0:
                        return candidate
                except Exception as exc:
                    if "target page, context or browser has been closed" in str(exc).lower():
                        page = _pick_live_page(None)
                        break
        return None

    def _click_first(selectors: list[str], timeout_ms: int) -> bool:
        loc = _first_visible(selectors, timeout_ms=timeout_ms)
        if not loc:
            return False
        try:
            loc.click()
        except Exception:
            try:
                loc.click(force=True)
            except Exception:
                return False
        page.wait_for_timeout(1200)
        return True

    def _open_create_surface() -> None:
        if not _click_first(list(INSTAGRAM_CREATE_ENTRY_SELECTORS), timeout_ms=9000):
            return
        post_picker = _first_visible(list(INSTAGRAM_POST_PICKER_SELECTORS), timeout_ms=3500)
        if not post_picker:
            return
        try:
            post_picker.click()
        except Exception:
            post_picker.click(force=True)
        page.wait_for_timeout(1200)

    def _try_direct_create_routes() -> bool:
        nonlocal page
        parsed = urllib.parse.urlparse(composer_url)
        base_url = "https://www.instagram.com/"
        if parsed.scheme and parsed.netloc:
            base_url = f"{parsed.scheme}://{parsed.netloc}/"

        for create_path in INSTAGRAM_DIRECT_CREATE_PATHS:
            target_url = urllib.parse.urljoin(base_url, create_path)
            try:
                page = _pick_live_page(page)
                page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1800)
            except Exception:
                continue
            if _find_file_input() is not None:
                return True
        return False

    def _upload_with_file_chooser() -> bool:
        nonlocal page
        for selector in INSTAGRAM_CREATE_ENTRY_SELECTORS:
            page = _pick_live_page(page)
            try:
                trigger = page.locator(selector).first
                if trigger.count() == 0:
                    continue
                trigger.wait_for(state="visible", timeout=2500)
            except Exception:
                continue
            try:
                with page.expect_file_chooser(timeout=3000) as chooser_info:
                    try:
                        trigger.click(timeout=2500)
                    except Exception:
                        trigger.click(timeout=2500, force=True)
                chooser_info.value.set_files(str(local_image_path))
                page.wait_for_timeout(2200)
                return True
            except Exception:
                continue
        return False

    page = _goto_composer(page)
    page = _wait_for_manual_login(page)
    page = _goto_composer(page)
    if _is_logged_in(page):
        _mark_instagram_authenticated(session_dir)

    file_uploaded = False
    file_input = _find_file_input()

    if file_input is None:
        if not _is_logged_in(page):
            page = _wait_for_manual_login(page)
            page = _goto_composer(page)
            _mark_instagram_authenticated(session_dir)
            file_input = _find_file_input()

        if file_input is None and _try_direct_create_routes():
            file_input = _find_file_input()

        if file_input is None:
            _open_create_surface()
            file_input = _find_file_input()

        if file_input is None:
            file_uploaded = _upload_with_file_chooser()

    if not file_uploaded and file_input is None:
        if not _is_logged_in(page):
            raise RuntimeError(
                "Instagram session not authenticated. Please login in the opened browser window and retry."
            )
        current_url = ""
        try:
            current_url = str(page.url)
        except Exception:
            pass
        raise RuntimeError(
            "Could not find Instagram file input. "
            f"Current URL: {current_url or 'unknown'}"
        )

    if not file_uploaded:
        file_input.set_input_files(str(local_image_path))
        file_uploaded = True

    if not file_uploaded:
        raise RuntimeError("Instagram upload did not start.")

    page.wait_for_timeout(2500)

    for _ in range(2):
        next_button = _first_visible(
            [
                "div[role='dialog'] div[role='button']:has-text('Next')",
                "div[role='button']:has-text('Next')",
                "button:has-text('Next')",
            ],
            timeout_ms=8000,
        )
        if not next_button:
            break
        next_button.click()
        page.wait_for_timeout(1600)

    caption_box = _first_visible(
        [
            "div[role='dialog'] textarea[aria-label*='caption']",
            "div[role='dialog'] textarea",
            "textarea[aria-label*='caption']",
            "textarea[placeholder*='caption']",
            "div[role='dialog'] div[contenteditable='true'][aria-label*='caption']",
            "div[contenteditable='true'][aria-label*='caption']",
        ],
        timeout_ms=12000,
    )
    if not caption_box:
        raise RuntimeError("Could not find Instagram caption input.")

    try:
        caption_box.fill(final_caption)
    except Exception:
        caption_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.type(final_caption, delay=12)

    share_button = _first_visible(
        [
            "div[role='dialog'] div[role='button']:has-text('Share')",
            "div[role='button']:has-text('Share')",
            "button:has-text('Share')",
        ],
        timeout_ms=12000,
    )
    if not share_button:
        raise RuntimeError("Could not find Instagram Share button.")

    share_button.click()
    page.wait_for_timeout(7000)
    _mark_instagram_authenticated(session_dir)
    if keep_open_seconds > 0 and not headless:
        page.wait_for_timeout(keep_open_seconds * 1000)


def post_to_instagram_with_playwright(
    image_url: str,
    caption: str,
    hashtags: Optional[str],
    *,
    dry_run: bool,
    headless: bool,
) -> Dict[str, Any]:
    final_caption = _caption_with_hashtags(caption, hashtags)
    if not final_caption:
        raise RuntimeError("Caption is required for Instagram posting.")

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "message": "[DRY RUN] Instagram post skipped.",
            "caption_preview": final_caption[:220],
            "image_url": image_url,
        }

    composer_url = os.getenv("INSTAGRAM_COMPOSER_URL", "").strip() or "https://www.instagram.com/"
    session_dir = Path(os.getenv("INSTAGRAM_SESSION_DIR", "session-data/instagram")).resolve()
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError(
            "Playwright is not available. Install with 'pip install playwright' "
            "and run 'playwright install chromium'."
        ) from exc

    login_wait_seconds = int(os.getenv("INSTAGRAM_LOGIN_WAIT_SECONDS", "600"))
    keep_open_seconds = int(os.getenv("INSTAGRAM_KEEP_OPEN_SECONDS", "0"))
    fallback_to_session = (
        os.getenv("INSTAGRAM_PROFILE_FALLBACK_TO_SESSION", "true").strip().lower() == "true"
    )
    auto_reset_session = (
        os.getenv("INSTAGRAM_SESSION_AUTO_RESET_ON_LAUNCH_ERROR", "true").strip().lower() == "true"
    )
    browser_channel, strict_channel = _resolve_browser_channel("INSTAGRAM_BROWSER_CHANNEL")

    with tempfile.TemporaryDirectory(prefix="instagram_upload_") as tmp:
        local_image_path = _download_image(image_url, Path(tmp))

        with sync_playwright() as p:
            if _connect_existing_browser_enabled():
                cdp_url = _cdp_url()
                cdp_timeout_ms = _cdp_attach_timeout_ms()
                resolved_user_data_dir, resolved_profile_directory, resolved_profile_mode = _resolve_instagram_profile_settings(
                    browser_channel,
                    session_dir,
                )

                browser = None
                attach_exc: Optional[Exception] = None
                try:
                    browser = p.chromium.connect_over_cdp(cdp_url, timeout=cdp_timeout_ms)
                except Exception as exc:
                    attach_exc = exc

                if (
                    browser is None
                    and _cdp_auto_start_enabled()
                    and _cdp_browser_restart_enabled()
                    and resolved_profile_mode == "system"
                ):
                    print("Starting browser with remote debugging for Instagram posting...")
                    if (
                        _start_default_browser_with_cdp(
                            channel=browser_channel,
                            cdp_url=cdp_url,
                            user_data_dir=resolved_user_data_dir,
                            profile_directory=resolved_profile_directory,
                            target_url=composer_url,
                        )
                        and _wait_for_cdp_available(cdp_url, _cdp_start_timeout_seconds())
                    ):
                        try:
                            browser = p.chromium.connect_over_cdp(cdp_url, timeout=cdp_timeout_ms)
                            attach_exc = None
                        except Exception as exc:
                            attach_exc = exc

                if browser is None:
                    raise RuntimeError(
                        "Could not attach to your default browser for Instagram posting. "
                        f"CDP endpoint: {cdp_url}. "
                        "Start Edge/Chrome with remote debugging once, "
                        "or disable INSTAGRAM_CONNECT_EXISTING_BROWSER to use the isolated session profile. "
                        "Automatic browser restart is disabled unless INSTAGRAM_CDP_ALLOW_BROWSER_RESTART=true."
                    ) from attach_exc

                existing_contexts = list(browser.contexts)
                if not existing_contexts:
                    raise RuntimeError(
                        "Attached browser has no active contexts. "
                        "Keep a normal tab open in your default browser and retry."
                    )
                context = None
                for candidate in existing_contexts:
                    try:
                        live_pages = [p for p in candidate.pages if not p.is_closed()]
                    except Exception:
                        live_pages = []
                    if live_pages:
                        context = candidate
                        break
                if context is None:
                    context = existing_contexts[0]

                try:
                    live_pages = [p for p in context.pages if not p.is_closed()]
                except Exception:
                    live_pages = []
                if not live_pages:
                    raise RuntimeError(
                        "Attached browser has no live tabs. "
                        "Open one normal tab in that browser profile and retry."
                    )

                _run_instagram_post_flow(
                    context=context,
                    composer_url=composer_url,
                    local_image_path=local_image_path,
                    final_caption=final_caption,
                    headless=headless,
                    login_wait_seconds=login_wait_seconds,
                    keep_open_seconds=keep_open_seconds,
                    session_dir=session_dir,
                    allow_new_page=False,
                    dedicated_page=None,
                )
                return {
                    "success": True,
                    "dry_run": False,
                    "message": "Instagram post submitted via Playwright (attached to existing browser).",
                    "image_url": image_url,
                    "composer_url": composer_url,
                    "browser_channel": "existing-cdp",
                    "profile_mode": resolved_profile_mode,
                    "profile_directory": resolved_profile_directory,
                    "user_data_dir": str(resolved_user_data_dir),
                    "cdp_url": cdp_url,
                    "keep_open_seconds": keep_open_seconds,
                }

            launch_base: Dict[str, Any] = {
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
            user_data_dir, profile_directory, profile_mode = _resolve_instagram_profile_settings(
                browser_channel,
                session_dir,
            )

            def _build_launch_kwargs(target_user_data_dir: Path, target_profile: Optional[str]) -> Dict[str, Any]:
                kwargs = dict(launch_base)
                args = list(launch_base["args"])
                if target_profile:
                    args.append(f"--profile-directory={target_profile}")
                kwargs["args"] = args
                kwargs["user_data_dir"] = str(target_user_data_dir)
                return kwargs

            primary_kwargs = _build_launch_kwargs(user_data_dir, profile_directory)
            context = None
            active_channel = ""
            primary_exc: Optional[Exception] = None

            try:
                context, active_channel = _launch_chromium_context(
                    p,
                    primary_kwargs,
                    browser_channel,
                    strict_channel or bool(browser_channel),
                )
            except Exception as exc:
                primary_exc = exc

            if (
                context is None
                and profile_mode == "system"
                and primary_exc is not None
                and _system_profile_close_retry_enabled()
            ):
                initial_primary_error = _short_error(primary_exc)
                _close_running_channel_processes(browser_channel)
                retry_kwargs = _build_launch_kwargs(user_data_dir, profile_directory)
                try:
                    context, active_channel = _launch_chromium_context(
                        p,
                        retry_kwargs,
                        browser_channel,
                        strict_channel or bool(browser_channel),
                    )
                    primary_exc = None
                except Exception as retry_exc:
                    primary_exc = RuntimeError(
                        "Default-profile launch retry failed after closing running browser processes. "
                        f"Initial: {initial_primary_error} | Retry: {_short_error(retry_exc)}"
                    )
                    if (
                        _system_profile_crashpad_reset_enabled()
                        and _looks_like_profile_store_corruption(retry_exc)
                    ):
                        _rotate_crashpad_dir(user_data_dir)
                        crashpad_retry_kwargs = _build_launch_kwargs(user_data_dir, profile_directory)
                        try:
                            context, active_channel = _launch_chromium_context(
                                p,
                                crashpad_retry_kwargs,
                                browser_channel,
                                strict_channel or bool(browser_channel),
                            )
                            primary_exc = None
                        except Exception as crashpad_retry_exc:
                            primary_exc = RuntimeError(
                                "Default-profile launch failed after process close + crashpad reset retry. "
                                f"Initial: {initial_primary_error} | Retry: {_short_error(retry_exc)} | "
                                f"Crashpad retry: {_short_error(crashpad_retry_exc)}"
                            )

            if context is None and profile_mode == "system" and fallback_to_session:
                fallback_kwargs = _build_launch_kwargs(session_dir, None)
                try:
                    context, active_channel = _launch_chromium_context(
                        p,
                        fallback_kwargs,
                        browser_channel,
                        strict_channel or bool(browser_channel),
                    )
                    profile_mode = "session"
                    profile_directory = None
                    user_data_dir = session_dir
                except Exception as fallback_exc:
                    if auto_reset_session and _looks_like_profile_store_corruption(fallback_exc):
                        _rotate_session_dir(session_dir)
                        retry_kwargs = _build_launch_kwargs(session_dir, None)
                        try:
                            context, active_channel = _launch_chromium_context(
                                p,
                                retry_kwargs,
                                browser_channel,
                                strict_channel or bool(browser_channel),
                            )
                            profile_mode = "session"
                            profile_directory = None
                            user_data_dir = session_dir
                        except Exception as retry_exc:
                            if primary_exc is not None:
                                raise RuntimeError(
                                    "Failed to launch Instagram with default profile and session fallback. "
                                    f"Default profile error: {_short_error(primary_exc)} | "
                                    f"Session fallback error: {_short_error(fallback_exc)} | "
                                    f"Session reset retry error: {_short_error(retry_exc)}"
                                ) from retry_exc
                            raise
                        else:
                            fallback_exc = None
                    if fallback_exc is None:
                        pass
                    elif primary_exc is not None:
                        raise RuntimeError(
                            "Failed to launch Instagram with default profile and session fallback. "
                            f"Default profile error: {_short_error(primary_exc)} | "
                            f"Session fallback error: {_short_error(fallback_exc)}"
                        ) from fallback_exc
                    else:
                        raise

            if (
                context is None
                and profile_mode == "session"
                and auto_reset_session
                and primary_exc is not None
                and _looks_like_profile_store_corruption(primary_exc)
                and _same_path(user_data_dir, session_dir)
            ):
                _rotate_session_dir(session_dir)
                retry_kwargs = _build_launch_kwargs(session_dir, None)
                try:
                    context, active_channel = _launch_chromium_context(
                        p,
                        retry_kwargs,
                        browser_channel,
                        strict_channel or bool(browser_channel),
                    )
                    profile_directory = None
                    user_data_dir = session_dir
                except Exception as retry_exc:
                    primary_exc = RuntimeError(
                        "Instagram session profile appears corrupted and retry failed. "
                        f"Initial launch error: {_short_error(primary_exc)} | "
                        f"Session reset retry error: {_short_error(retry_exc)}"
                    )

            if context is None:
                if primary_exc is not None:
                    if profile_mode == "system" and _is_profile_lock_error(primary_exc):
                        raise RuntimeError(
                            "Instagram default browser profile is currently locked by another running browser instance. "
                            "Close all Edge/Chrome windows and retry, or set INSTAGRAM_PROFILE_MODE=session."
                        ) from primary_exc
                    if profile_mode == "system":
                        raise RuntimeError(
                            "Failed to launch Instagram with your default browser profile. "
                            f"Details: {_short_error(primary_exc)}. "
                            "Close all Edge/Chrome windows (including background tasks) and retry, "
                            "or set INSTAGRAM_PROFILE_MODE=session."
                        ) from primary_exc
                    raise primary_exc
                raise RuntimeError("Failed to launch Instagram browser context.")
            if profile_mode == "system":
                # Best effort indicator for dashboard/status; doesn't alter Playwright profile storage.
                _mark_instagram_authenticated(session_dir)
            if not context.pages:
                # Open one working tab for isolated Playwright profiles.
                context.new_page()

            try:
                _run_instagram_post_flow(
                    context=context,
                    composer_url=composer_url,
                    local_image_path=local_image_path,
                    final_caption=final_caption,
                    headless=headless,
                    login_wait_seconds=login_wait_seconds,
                    keep_open_seconds=keep_open_seconds,
                    session_dir=session_dir,
                    allow_new_page=False,
                    dedicated_page=None,
                )
                return {
                    "success": True,
                    "dry_run": False,
                    "message": "Instagram post submitted via Playwright.",
                    "image_url": image_url,
                    "composer_url": composer_url,
                    "browser_channel": active_channel,
                    "profile_mode": profile_mode,
                    "profile_directory": profile_directory,
                    "user_data_dir": str(user_data_dir),
                    "keep_open_seconds": keep_open_seconds,
                }
            finally:
                try:
                    context.close()
                except Exception:
                    # Browser may already be closed by the site/user; treat as non-fatal cleanup.
                    pass


def prepare_instagram_session() -> Dict[str, Any]:
    """Open a persistent browser profile so the user can login once."""
    composer_url = os.getenv("INSTAGRAM_COMPOSER_URL", "").strip() or "https://www.instagram.com/"
    session_dir = Path(os.getenv("INSTAGRAM_SESSION_DIR", "session-data/instagram")).resolve()
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError(
            "Playwright is not available. Install with 'pip install playwright' "
            "and run 'playwright install chromium'."
        ) from exc

    with sync_playwright() as p:
        browser_channel, strict_channel = _resolve_browser_channel("INSTAGRAM_BROWSER_CHANNEL")
        fallback_to_session = (
            os.getenv("INSTAGRAM_PROFILE_FALLBACK_TO_SESSION", "true").strip().lower() == "true"
        )
        auto_reset_session = (
            os.getenv("INSTAGRAM_SESSION_AUTO_RESET_ON_LAUNCH_ERROR", "true").strip().lower() == "true"
        )
        launch_base: Dict[str, Any] = {
            "user_data_dir": str(session_dir),
            "headless": False,
            "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            "viewport": {"width": 1280, "height": 900},
        }
        user_data_dir, profile_directory, profile_mode = _resolve_instagram_profile_settings(
            browser_channel,
            session_dir,
        )

        def _build_launch_kwargs(target_user_data_dir: Path, target_profile: Optional[str]) -> Dict[str, Any]:
            kwargs = dict(launch_base)
            args = list(launch_base["args"])
            if target_profile:
                args.append(f"--profile-directory={target_profile}")
            kwargs["args"] = args
            kwargs["user_data_dir"] = str(target_user_data_dir)
            return kwargs

        primary_kwargs = _build_launch_kwargs(user_data_dir, profile_directory)
        context = None
        active_channel = ""
        primary_exc: Optional[Exception] = None

        try:
            context, active_channel = _launch_chromium_context(
                p,
                primary_kwargs,
                browser_channel,
                strict_channel or bool(browser_channel),
            )
        except Exception as exc:
            primary_exc = exc

        if (
            context is None
            and profile_mode == "system"
            and primary_exc is not None
            and _system_profile_close_retry_enabled()
        ):
            initial_primary_error = _short_error(primary_exc)
            _close_running_channel_processes(browser_channel)
            retry_kwargs = _build_launch_kwargs(user_data_dir, profile_directory)
            try:
                context, active_channel = _launch_chromium_context(
                    p,
                    retry_kwargs,
                    browser_channel,
                    strict_channel or bool(browser_channel),
                )
                primary_exc = None
            except Exception as retry_exc:
                primary_exc = RuntimeError(
                    "Default-profile login-window launch retry failed after closing running browser processes. "
                    f"Initial: {initial_primary_error} | Retry: {_short_error(retry_exc)}"
                )
                if (
                    _system_profile_crashpad_reset_enabled()
                    and _looks_like_profile_store_corruption(retry_exc)
                ):
                    _rotate_crashpad_dir(user_data_dir)
                    crashpad_retry_kwargs = _build_launch_kwargs(user_data_dir, profile_directory)
                    try:
                        context, active_channel = _launch_chromium_context(
                            p,
                            crashpad_retry_kwargs,
                            browser_channel,
                            strict_channel or bool(browser_channel),
                        )
                        primary_exc = None
                    except Exception as crashpad_retry_exc:
                        primary_exc = RuntimeError(
                            "Default-profile login-window launch failed after process close + crashpad reset retry. "
                            f"Initial: {initial_primary_error} | Retry: {_short_error(retry_exc)} | "
                            f"Crashpad retry: {_short_error(crashpad_retry_exc)}"
                        )

        if context is None and profile_mode == "system" and fallback_to_session:
            fallback_kwargs = _build_launch_kwargs(session_dir, None)
            try:
                context, active_channel = _launch_chromium_context(
                    p,
                    fallback_kwargs,
                    browser_channel,
                    strict_channel or bool(browser_channel),
                )
                profile_mode = "session"
                profile_directory = None
                user_data_dir = session_dir
            except Exception as fallback_exc:
                if auto_reset_session and _looks_like_profile_store_corruption(fallback_exc):
                    _rotate_session_dir(session_dir)
                    retry_kwargs = _build_launch_kwargs(session_dir, None)
                    try:
                        context, active_channel = _launch_chromium_context(
                            p,
                            retry_kwargs,
                            browser_channel,
                            strict_channel or bool(browser_channel),
                        )
                        profile_mode = "session"
                        profile_directory = None
                        user_data_dir = session_dir
                    except Exception as retry_exc:
                        if primary_exc is not None:
                            raise RuntimeError(
                                "Failed to open Instagram login window with default profile and session fallback. "
                                f"Default profile error: {_short_error(primary_exc)} | "
                                f"Session fallback error: {_short_error(fallback_exc)} | "
                                f"Session reset retry error: {_short_error(retry_exc)}"
                            ) from retry_exc
                        raise
                    else:
                        fallback_exc = None
                if fallback_exc is None:
                    pass
                elif primary_exc is not None:
                    raise RuntimeError(
                        "Failed to open Instagram login window with default profile and session fallback. "
                        f"Default profile error: {_short_error(primary_exc)} | "
                        f"Session fallback error: {_short_error(fallback_exc)}"
                    ) from fallback_exc
                else:
                    raise

        if (
            context is None
            and profile_mode == "session"
            and auto_reset_session
            and primary_exc is not None
            and _looks_like_profile_store_corruption(primary_exc)
            and _same_path(user_data_dir, session_dir)
        ):
            _rotate_session_dir(session_dir)
            retry_kwargs = _build_launch_kwargs(session_dir, None)
            try:
                context, active_channel = _launch_chromium_context(
                    p,
                    retry_kwargs,
                    browser_channel,
                    strict_channel or bool(browser_channel),
                )
                profile_directory = None
                user_data_dir = session_dir
            except Exception as retry_exc:
                primary_exc = RuntimeError(
                    "Instagram session profile appears corrupted and login-window retry failed. "
                    f"Initial launch error: {_short_error(primary_exc)} | "
                    f"Session reset retry error: {_short_error(retry_exc)}"
                )

        if context is None:
            if primary_exc is not None:
                if profile_mode == "system" and _is_profile_lock_error(primary_exc):
                    raise RuntimeError(
                        "Instagram default browser profile is currently locked by another running browser instance. "
                        "Close all Edge/Chrome windows and retry, or set INSTAGRAM_PROFILE_MODE=session."
                    ) from primary_exc
                if profile_mode == "system":
                    raise RuntimeError(
                        "Failed to open Instagram login window with your default browser profile. "
                        f"Details: {_short_error(primary_exc)}. "
                        "Close all Edge/Chrome windows (including background tasks) and retry, "
                        "or set INSTAGRAM_PROFILE_MODE=session."
                    ) from primary_exc
                raise primary_exc
            raise RuntimeError("Failed to launch Instagram browser context.")
        if profile_mode == "system":
            _mark_instagram_authenticated(session_dir)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(composer_url, wait_until="domcontentloaded", timeout=60000)
        print(
            "Instagram session window opened.\n"
            "Sign in manually, then press Enter here to save session and close."
        )
        input()
        try:
            if not _looks_like_instagram_login_page(page):
                _mark_instagram_authenticated(session_dir)
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            # Browser may already be closed by the site/user; treat as non-fatal cleanup.
            pass

    return {
        "success": True,
        "session_dir": str(session_dir),
        "browser_channel": active_channel,
        "profile_mode": profile_mode,
        "profile_directory": profile_directory,
        "user_data_dir": str(user_data_dir),
        "message": "Instagram session captured.",
    }


def main() -> int:
    _load_env()

    parser = argparse.ArgumentParser(description="Instagram Playwright poster")
    parser.add_argument("--mode", choices=["post", "login"], default="post")
    parser.add_argument("--image-url", help="Public image URL for upload")
    parser.add_argument("--caption", help="Caption text", default="")
    parser.add_argument("--hashtags", help="Comma/space-separated hashtags", default="")
    parser.add_argument("--dry-run", action="store_true", help="Skip live posting")
    parser.add_argument("--headless", action="store_true", help="Use headless browser mode")
    parser.add_argument("--json", action="store_true", help="Print JSON response")
    args = parser.parse_args()

    dry_run = args.dry_run or os.getenv("DRY_RUN", "false").lower() == "true"
    headless = args.headless or os.getenv("INSTAGRAM_HEADLESS", "false").lower() == "true"

    try:
        if args.mode == "login":
            result = prepare_instagram_session()
        else:
            if not args.image_url:
                raise RuntimeError("--image-url is required for post mode.")
            result = post_to_instagram_with_playwright(
                image_url=args.image_url,
                caption=args.caption,
                hashtags=args.hashtags,
                dry_run=dry_run,
                headless=headless,
            )
        if args.json:
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        payload = {"success": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload))
        else:
            print(json.dumps(payload, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
