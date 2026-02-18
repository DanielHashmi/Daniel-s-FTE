#!/usr/bin/env python3
"""
Claim-by-move validator (Platinum Tier).

Implements the hackathon rule:
First agent to move an item from Needs_Action -> In_Progress/<agent>/ owns it.

This module is imported by integration tests and can also be used by orchestration code.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import yaml


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_frontmatter(text: str) -> Optional[Dict[str, Any]]:
    if not text or not text.lstrip().startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return None


def _extract_action_id(frontmatter: Dict[str, Any]) -> Optional[str]:
    # Support both legacy `action_id` and current `id`.
    for key in ("action_id", "id"):
        value = frontmatter.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


@dataclass
class ClaimResult:
    ok: bool
    message: str
    claimed_path: Optional[Path] = None
    action_id: Optional[str] = None


class ClaimValidator:
    def __init__(self, vault_path: str, agent_id: str):
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id

        self.needs_action = self.vault_path / "Needs_Action"
        self.in_progress_base = self.vault_path / "In_Progress"
        self.claimed_path = self.in_progress_base / agent_id
        self.claimed_path.mkdir(parents=True, exist_ok=True)

    def validate_action_file(self, action_file: Path) -> Tuple[bool, str]:
        """Validate that the file exists and contains YAML frontmatter with an id."""
        if not action_file.exists():
            return False, "File does not exist"

        try:
            content = action_file.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return False, f"Unreadable file: {exc}"

        frontmatter = _parse_frontmatter(content)
        if frontmatter is None:
            return False, "Missing YAML frontmatter"

        action_id = _extract_action_id(frontmatter)
        if not action_id:
            return False, "Missing required fields in frontmatter"

        return True, "Valid"

    def _extract_action_id_from_file(self, action_file: Path) -> Optional[str]:
        try:
            content = action_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
        fm = _parse_frontmatter(content)
        if not fm:
            return None
        return _extract_action_id(fm)

    def is_action_claimed_by_other(self, action_file: Path) -> bool:
        """Return True if another agent already claimed the same action_id."""
        action_id = None
        if action_file.exists():
            action_id = self._extract_action_id_from_file(action_file)
            if not action_id:
                return False

        if not self.in_progress_base.exists():
            return False

        for agent_folder in self.in_progress_base.iterdir():
            if not agent_folder.is_dir():
                continue
            if agent_folder.name == self.agent_id:
                continue

            for f in agent_folder.iterdir():
                if not f.is_file():
                    continue
                # Preferred: action_id prefix match when we know the id.
                if action_id and f.name.startswith(action_id):
                    return True
                # Fallback for missing source file: match original filename suffix.
                if not action_id and f.name.endswith(f"_{action_file.name}"):
                    return True

        return False

    def claim(self, action_file_path: str) -> Tuple[bool, str]:
        """
        Claim an action by moving it to In_Progress/<agent_id>/.

        Returns (success, message)
        """
        action_file = Path(action_file_path)

        # If the file is already gone, treat it as "claimed" when another agent moved it.
        if not action_file.exists():
            if self.is_action_claimed_by_other(action_file):
                return False, "Action already claimed by another agent"
            return False, "File does not exist"

        valid, message = self.validate_action_file(action_file)
        if not valid:
            return False, f"Validation failed: {message}"

        if self.is_action_claimed_by_other(action_file):
            return False, "Action already claimed by another agent"

        action_id = self._extract_action_id_from_file(action_file)
        if not action_id:
            return False, "Could not extract action_id"

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest_name = f"{action_id}_{timestamp}_{action_file.name}"
        dest_path = self.claimed_path / dest_name

        try:
            shutil.move(str(action_file), str(dest_path))
        except Exception as exc:
            return False, f"Failed to claim: {exc}"

        # Write a machine-readable claim record.
        record = {
            "timestamp": _utc_now_iso(),
            "action_id": action_id,
            "source_file": str(action_file),
            "agent_id": self.agent_id,
            "claimed_file": str(dest_path),
        }
        record_file = self.claimed_path / f"{action_id}_{timestamp}_claim.json"
        try:
            record_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
        except Exception:
            # Non-fatal; claim already happened.
            pass

        return True, f"Claimed action {action_id} to {dest_path}"
