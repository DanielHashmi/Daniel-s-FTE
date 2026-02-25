"""
File System Watcher (Bronze Tier option).

Monitors `AI_Employee_Vault/Inbox/` for local file drops and converts them into
Needs_Action items for planning/execution.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

from src.lib.vault import vault
from src.watchers.base import BaseWatcher


class FileSystemWatcher(BaseWatcher):
    def __init__(self, interval: int = 30):
        super().__init__("filesystem_watcher", interval, domain=os.getenv("FILESYSTEM_DOMAIN", "personal"))
        self.inbox = vault.dirs["inbox"]
        self.processed = self.inbox / ".processed"
        self.processed.mkdir(parents=True, exist_ok=True)

        self.supported_extensions = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}

    def check_for_updates(self):
        for p in sorted(self.inbox.glob("*")):
            if not p.is_file():
                continue
            if p.parent.name == ".processed":
                continue
            if p.suffix.lower() not in self.supported_extensions:
                continue

            stat = p.stat()
            dedup_key = hashlib.md5(f"{p.name}|{stat.st_size}|{int(stat.st_mtime)}".encode("utf-8")).hexdigest()
            if dedup_key in self.processed_ids:
                continue

            # Best-effort text preview for planning (binary files will be ignored safely).
            preview = ""
            try:
                preview = p.read_text(encoding="utf-8", errors="ignore")[:800]
            except Exception:
                preview = ""

            self.create_action_file(
                type="file_drop",
                content=(
                    "# New File Dropped for Processing\n\n"
                    f"- Original name: {p.name}\n"
                    f"- Size (bytes): {stat.st_size}\n\n"
                    "## Preview\n\n"
                    f"{preview}\n"
                ),
                metadata={
                    "original_name": p.name,
                    "size": stat.st_size,
                    "path": str(p),
                },
                priority="high" if any(k in p.name.lower() for k in ("urgent", "invoice", "payment")) else "normal",
            )

            self.processed_ids.add(dedup_key)

            # Move to processed to avoid reprocessing.
            dest = self.processed / p.name
            if dest.exists():
                dest = self.processed / f"{p.stem}_{int(time.time())}{p.suffix}"
            try:
                p.rename(dest)
            except Exception:
                # If move fails, keep the dedup key so we don't spin.
                pass

