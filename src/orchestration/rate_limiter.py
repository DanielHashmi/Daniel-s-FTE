"""
Simple file-backed rate limiter (Security & Privacy Architecture).

Hackathon requirement: implement maximum actions per hour (e.g., max 10 emails, max 3 payments).
This module enforces that in a local-first, audit-friendly way.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _floor_to_hour(ts: datetime) -> datetime:
    return ts.replace(minute=0, second=0, microsecond=0)


@dataclass
class RateLimitDecision:
    allowed: bool
    count: int
    limit: int
    window_start_iso: str


class HourlyRateLimiter:
    """
    File-backed hourly limiter.

    State file schema:
    {
      "window_start": "2026-02-15T17:00:00+00:00",
      "counts": {"send_email": 3, "twitter_post": 2}
    }
    """

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict:
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, state: Dict) -> None:
        self.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def check_and_increment(self, key: str, limit: int) -> RateLimitDecision:
        now = _utc_now()
        window_start = _floor_to_hour(now)

        state = self._load()
        state_window_raw = state.get("window_start")
        state_counts = state.get("counts") if isinstance(state.get("counts"), dict) else {}

        state_window = None
        if isinstance(state_window_raw, str) and state_window_raw:
            try:
                state_window = datetime.fromisoformat(state_window_raw)
            except ValueError:
                state_window = None

        # Reset when crossing the hour boundary or if state is missing/corrupt.
        if not state_window or state_window != window_start:
            state_counts = {}
            state_window = window_start

        count = int(state_counts.get(key, 0))
        if count >= limit:
            return RateLimitDecision(
                allowed=False,
                count=count,
                limit=limit,
                window_start_iso=state_window.isoformat(),
            )

        count += 1
        state_counts[key] = count
        self._save({"window_start": state_window.isoformat(), "counts": state_counts})

        return RateLimitDecision(
            allowed=True,
            count=count,
            limit=limit,
            window_start_iso=state_window.isoformat(),
        )

