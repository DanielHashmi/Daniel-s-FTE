#!/usr/bin/env python3
"""Social Media Suite - Gold Tier Skill

Post to Facebook, Instagram, and Twitter/X with platform-specific formatting.
Supports HITL approval workflow for all posts.
"""
import argparse
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env")

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
PENDING_APPROVAL = VAULT_ROOT / "Pending_Approval"
LOGS_DIR = VAULT_ROOT / "Logs"
SOCIAL_LOG = LOGS_DIR / "Social_Posts.log"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"

# Platform character limits
PLATFORM_LIMITS = {
    "facebook": 63206,
    "instagram": 2200,
    "twitter": 280,
    "linkedin": 3000  # Already exists in social-ops
}


def setup_dirs():
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "social_media",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "social_media_suite_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


def check_credentials(platform: str) -> bool:
    """Check if platform credentials are configured."""
    cred_map = {
        "facebook": ["META_ACCESS_TOKEN", "META_PAGE_ID"],
        "instagram": ["META_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
        "twitter": ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"],
    }
    required = cred_map.get(platform, [])
    return all(os.getenv(var) for var in required)


def truncate_message(message: str, platform: str) -> tuple[str, bool]:
    """Truncate message to platform limit, return (message, was_truncated)."""
    limit = PLATFORM_LIMITS.get(platform, 1000)
    if len(message) <= limit:
        return message, False

    # Smart truncate: preserve hashtags at end if present
    truncated = message[:limit - 3]
    if "#" in message[limit:]:
        # Try to fit at least one hashtag
        hashtags = [w for w in message.split() if w.startswith("#")]
        if hashtags:
            last_hashtag = hashtags[-1]
            if len(truncated) + len(last_hashtag) + 4 <= limit:
                truncated = truncated[:limit - len(last_hashtag) - 4] + "... " + last_hashtag
            else:
                truncated += "..."
        else:
            truncated += "..."
    else:
        truncated += "..."

    return truncated, True


def create_approval_request(platform: str, message: str, image: Optional[str] = None,
                           hashtags: Optional[str] = None) -> Path:
    """Create HITL approval request for social media post."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    post_id = hashlib.md5(f"{platform}{timestamp}{message[:50]}".encode()).hexdigest()[:8]

    # Check for truncation
    final_message, was_truncated = truncate_message(message, platform)

    content = f"""---
id: SOCIAL-{platform.upper()}-{post_id}
type: approval_request
action: social_post
platform: {platform}
created: {datetime.now().isoformat()}
actor: social_media_suite_skill
priority: normal
status: pending
---

# Social Media Post Approval Request

## Platform
**{platform.capitalize()}** (Character limit: {PLATFORM_LIMITS.get(platform, 'N/A')})

## Content
{final_message}

{"## Image" if image else ""}
{f"Attachment: {image}" if image else ""}

{"## Hashtags" if hashtags else ""}
{hashtags if hashtags else ""}

{"## ⚠️ NOTICE: Content was truncated to fit platform limits" if was_truncated else ""}

## Approval Criteria
- [ ] Content appropriate for platform
- [ ] No sensitive information
- [ ] Links verified (if any)
- [ ] Image appropriate (if any)

## To Approve
Move this file to `/Approved/` folder.

## To Reject
Move this file to `/Rejected/` folder.

---
*Created by social-media-suite skill*
"""

    filepath = PENDING_APPROVAL / f"SOCIAL_{platform}_{timestamp}.md"
    filepath.write_text(content)
    return filepath


def post_to_platform(platform: str, message: str, image: Optional[str] = None,
                     link: Optional[str] = None, hashtags: Optional[str] = None,
                     force_dry_run: bool = False):
    """Post to specified platform (creates approval request in dry-run)."""
    dry_run = force_dry_run or os.getenv("DRY_RUN", "true").lower() == "true"
    has_creds = check_credentials(platform)

    # Always require approval first
    approval_file = create_approval_request(platform, message, image, hashtags)

    if dry_run or not has_creds:
        # Log the dry run
        log_entry = f"[{datetime.now().isoformat()}] [DRY RUN] {platform.upper()}: {message[:100]}...\n"
        with open(SOCIAL_LOG, "a") as f:
            f.write(log_entry)

        mode = "DRY RUN" if dry_run else "PENDING CREDENTIALS"
        print(f"✓ Approval request created ({mode})")
        print(f"  Platform: {platform.capitalize()}")
        print(f"  File: {approval_file.name}")
        audit_log("post_request", platform, f"approval_created ({mode.lower()})",
                 {"message_length": len(message), "has_image": bool(image)})
        return True

    # Real posting would happen here after approval
    print("✗ Real posting requires approved file in /Approved folder.")
    return False


def multi_platform_post(message: str, image: Optional[str] = None,
                        platforms: list = None):
    """Create approval requests for multiple platforms."""
    platforms = platforms or ["facebook", "instagram", "twitter"]

    print(f"Creating approval requests for {len(platforms)} platforms...")
    for platform in platforms:
        post_to_platform(platform, message, image, force_dry_run=True)

    print(f"\n✓ Created {len(platforms)} approval request(s)")
    print("  Review files in: AI_Employee_Vault/Pending_Approval/")
    return True


def check_status():
    """Check status of all social media integrations."""
    print("Social Media Suite Status:")
    print("-" * 40)

    for platform in ["facebook", "instagram", "twitter"]:
        has_creds = check_credentials(platform)
        status = "✓ Configured" if has_creds else "✗ Not configured"
        print(f"  {platform.capitalize():12} {status}")

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    print(f"\n  Mode: {'DRY RUN (simulated)' if dry_run else 'LIVE'}")

    # Count pending posts
    pending = list(PENDING_APPROVAL.glob("SOCIAL_*.md"))
    print(f"  Pending approval: {len(pending)}")

    return True


def generate_summary(days: int = 7):
    """Generate social media posting summary for CEO Briefing."""
    if not SOCIAL_LOG.exists():
        print("No social media activity recorded.")
        return True

    lines = SOCIAL_LOG.read_text().strip().split("\n") if SOCIAL_LOG.exists() else []

    # Count posts per platform
    platforms = {"facebook": 0, "instagram": 0, "twitter": 0, "linkedin": 0}
    for line in lines:
        for platform in platforms:
            if platform.upper() in line:
                platforms[platform] += 1

    print(f"Social Media Summary (Last {days} days):")
    print("-" * 40)
    total = 0
    for platform, count in platforms.items():
        print(f"  {platform.capitalize():12} {count} post(s)")
        total += count

    print(f"\n  Total: {total} post(s)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Social Media Suite Operations")
    parser.add_argument("--platform", choices=["facebook", "instagram", "twitter", "all"],
                       help="Target platform")
    parser.add_argument("--action", required=True,
                       choices=["post", "status", "summary"])
    parser.add_argument("--message", help="Post message content")
    parser.add_argument("--image", help="Path to image file")
    parser.add_argument("--link", help="URL to include")
    parser.add_argument("--caption", help="Caption for Instagram")
    parser.add_argument("--hashtags", help="Comma-separated hashtags")
    parser.add_argument("--days", type=int, default=7, help="Days for summary")

    args = parser.parse_args()
    setup_dirs()

    if args.action == "post":
        if not args.message and not args.caption:
            print("Error: --message or --caption required for post")
            sys.exit(1)

        message = args.message or args.caption

        if args.platform == "all":
            if not multi_platform_post(message, args.image):
                sys.exit(1)
        elif args.platform:
            if not post_to_platform(args.platform, message, args.image,
                                   args.link, args.hashtags):
                sys.exit(1)
        else:
            print("Error: --platform required for post action")
            sys.exit(1)

    elif args.action == "status":
        check_status()

    elif args.action == "summary":
        generate_summary(args.days)


if __name__ == "__main__":
    main()
