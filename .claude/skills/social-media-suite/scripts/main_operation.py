#!/usr/bin/env python3
"""social-media-suite skill (Gold Tier)

Creates HITL approval request files for Facebook, Instagram, Twitter/X (and optionally LinkedIn)
and provides a simple summary based on the audit logs.

Execution happens after human approval via the local orchestrator + MCP (social-mcp).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger
from src.lib.vault import vault

logger = get_logger("social_media_suite_skill")

PLATFORM_LIMITS = {
    "facebook": 63206,
    "instagram": 2200,
    "twitter": 280,
    "linkedin": 3000,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate(platform: str, text: str) -> str:
    limit = PLATFORM_LIMITS.get(platform, 1000)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _write_approval(frontmatter: Dict[str, Any], body: str, domain: str) -> Path:
    vault.ensure_structure()
    dir_path = vault.get_domain_dir("pending_approval", domain)
    dir_path.mkdir(parents=True, exist_ok=True)

    ts = int(time.time())
    platform = str(frontmatter.get("platform") or "unknown").lower()
    filename = f"{ts}_SOCIAL_{platform}_{frontmatter.get('id','manual')}.md"
    path = dir_path / filename

    content = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False).strip() + "\n---\n\n" + body.strip() + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def create_social_approval(
    platform: str,
    message: str,
    domain: str,
    *,
    instagram_image_url: Optional[str] = None,
    instagram_caption: Optional[str] = None,
    hashtags: Optional[str] = None,
) -> Path:
    platform = platform.strip().lower()
    if platform not in PLATFORM_LIMITS:
        raise ValueError(f"Unsupported platform: {platform}")

    ts = int(time.time())
    req_id = f"SOCIAL-{platform.upper()}-{ts}"

    frontmatter: Dict[str, Any] = {
        "id": req_id,
        "type": "approval_request",
        "action": "social_post",
        "platform": platform,
        "created": _utc_now_iso(),
        "status": "pending",
        "domain": domain,
        "source_action_id": f"manual_{ts}",
    }

    if platform == "instagram":
        # social-mcp posts to Instagram via Graph API which requires a public image URL.
        if not instagram_image_url:
            raise ValueError("Instagram requires --image-url (public URL)")
        caption = instagram_caption or message
        frontmatter["image_url"] = instagram_image_url
        frontmatter["caption"] = _truncate("instagram", caption)
        if hashtags:
            frontmatter["hashtags"] = hashtags

        body = (
            "# Social Post Approval Request (instagram)\n\n"
            "## Caption\n"
            f"{frontmatter['caption']}\n\n"
            "## Image URL\n"
            f"{instagram_image_url}\n\n"
            "---\n\n"
            "Move this file to `Approved/` to post, or `Rejected/` to cancel.\n"
        )
    else:
        text = _truncate(platform, message)
        body = (
            f"# Social Post Approval Request ({platform})\n\n"
            "## Content\n"
            f"{text}\n\n"
            "---\n\n"
            "Move this file to `Approved/` to post, or `Rejected/` to cancel.\n"
        )

    path = _write_approval(frontmatter, body, domain=domain)

    logger.log_action(
        action_type="social_approval_created",
        result="success",
        target=str(path),
        parameters={"platform": platform, "domain": domain},
        approval_status="pending",
    )

    return path


def _log_files_for_days(days: int) -> list[Path]:
    vault.ensure_structure()
    base = vault.dirs["logs"]
    out = []
    now = datetime.now(timezone.utc).date()
    for i in range(days):
        d = now - timedelta(days=i)
        p = base / f"{d.isoformat()}.json"
        if p.exists():
            out.append(p)
    return out


def summary(days: int = 7) -> int:
    counts = {"facebook": 0, "instagram": 0, "twitter": 0, "linkedin": 0}

    for p in _log_files_for_days(days):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            at = str(obj.get("action_type") or "")
            if at == "facebook_post":
                counts["facebook"] += 1
            elif at == "instagram_post":
                counts["instagram"] += 1
            elif at == "twitter_post":
                counts["twitter"] += 1
            elif at == "linkedin_post":
                counts["linkedin"] += 1

    print(f"Social Media Summary (last {days} days)")
    for k, v in counts.items():
        print(f"- {k}: {v}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Social Media Suite")
    parser.add_argument("--action", required=True, choices=["post", "summary"])
    parser.add_argument("--platform", choices=["facebook", "instagram", "twitter", "linkedin", "all"])
    parser.add_argument("--message", help="Post content (caption for Instagram if --caption not provided)")
    parser.add_argument("--domain", default=os.getenv("SOCIAL_DOMAIN", "business"))

    # Instagram specifics
    parser.add_argument("--image-url", help="Instagram public image URL")
    parser.add_argument("--caption", help="Instagram caption")
    parser.add_argument("--hashtags", help="Comma-separated hashtags")

    parser.add_argument("--days", type=int, default=7)

    args = parser.parse_args()
    domain = str(args.domain).strip().lower() or "business"

    if args.action == "summary":
        return summary(days=int(args.days))

    if args.action == "post":
        if not args.platform:
            print("--platform is required for post")
            return 1
        if not args.message and not args.caption:
            print("--message (or --caption) is required")
            return 1

        msg = args.message or ""
        platforms = [args.platform]
        if args.platform == "all":
            platforms = ["facebook", "instagram", "twitter", "linkedin"]

        created = []
        for plat in platforms:
            created.append(
                create_social_approval(
                    plat,
                    msg,
                    domain,
                    instagram_image_url=args.image_url,
                    instagram_caption=args.caption,
                    hashtags=args.hashtags,
                )
            )

        for p in created:
            print(str(p))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
