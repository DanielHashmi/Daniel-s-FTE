#!/usr/bin/env python3
"""social-ops skill

Silver/Gold tier expectation:
- Create LinkedIn (and other) social posts via HITL approval files
- Local executor posts via MCP after approval

This skill can:
- create a Pending_Approval item (default)
- optionally post immediately via social-mcp (use with care)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[5]
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.logging import get_logger
from src.lib.vault import vault
from src.mcp.stdio_client import call_node_mcp_tool

logger = get_logger("social_ops_skill")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_for_actions() -> Dict[str, str]:
    env = {**os.environ}
    if os.getenv("DEV_MODE", "false").lower() == "true":
        env["DRY_RUN"] = "true"
    return env


def _write_pending_approval(platform: str, content: str, domain: str = "business") -> Path:
    vault.ensure_structure()

    ts = int(time.time())
    filename = f"{ts}_SOCIAL_{platform}_manual.md"

    frontmatter: Dict[str, Any] = {
        "type": "approval_request",
        "action": "social_post",
        "platform": platform,
        "created": _utc_now_iso(),
        "status": "pending",
        "domain": domain,
        "source_action_id": f"manual_{ts}",
    }

    body = (
        f"# Social Post Approval Request ({platform})\n\n"
        "## Content\n"
        f"{content.strip()}\n\n"
        "---\n\n"
        "Move this file to `Approved/` to post, or `Rejected/` to cancel.\n"
    )

    dir_path = vault.get_domain_dir("pending_approval", domain)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / filename
    path.write_text("---\n" + yaml.safe_dump(frontmatter, sort_keys=False).strip() + "\n---\n\n" + body, encoding="utf-8")

    logger.log_action(
        action_type="social_approval_created",
        result="success",
        target=str(path),
        parameters={"platform": platform},
        approval_status="pending",
    )

    return path


def _post_now(platform: str, content: str, visibility: str = "PUBLIC") -> int:
    mcp_path = Path("mcp-servers/social-mcp/index.js")
    if not mcp_path.exists():
        raise FileNotFoundError(f"social-mcp server not found: {mcp_path}")

    tool_map = {
        "twitter": "post_to_twitter",
        "linkedin": "post_to_linkedin",
        "facebook": "post_to_facebook",
    }
    tool = tool_map.get(platform)
    if not tool:
        raise ValueError(f"Unsupported platform: {platform}")

    args: Dict[str, Any] = {"content": content}
    if platform == "linkedin":
        args["visibility"] = visibility

    res = call_node_mcp_tool(
        entrypoint=mcp_path,
        tool_name=tool,
        arguments=args,
        timeout_seconds=int(os.getenv("MCP_TIMEOUT_SECONDS", "60")),
        env=_env_for_actions(),
    )

    if not res.ok:
        raise RuntimeError(res.stderr or res.stdout or "MCP call failed")

    logger.log_action(
        action_type=f"{platform}_post",
        result="success",
        target=platform,
        parameters={"content_preview": content[:120]},
        approval_status="approved",
        approved_by="policy",
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Social operations")
    parser.add_argument("--action", required=True, choices=["request", "post-now"])
    parser.add_argument("--platform", required=True, choices=["linkedin", "twitter", "facebook"])
    parser.add_argument("--content", required=True, help="Post content")
    parser.add_argument("--domain", default=os.getenv("SOCIAL_DOMAIN", "business"))
    parser.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])

    args = parser.parse_args()
    vault.ensure_structure()

    platform = str(args.platform).strip().lower()

    if args.action == "request":
        path = _write_pending_approval(platform, args.content, domain=str(args.domain).strip().lower() or "business")
        print(str(path))
        return 0

    if args.action == "post-now":
        return _post_now(platform, args.content, visibility=args.visibility)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
