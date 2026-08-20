"""Persistent dedup memory so the agent never alerts on the same listing twice.

State is a small JSON file committed to the repo (or written to Drive) — the
container is ephemeral, so the memory must live somewhere durable. Keyed by a
stable listing id; the value records when we first saw it.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Iterable


class SeenStore:
    def __init__(self, path: str):
        self.path = path
        self._seen: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    self._seen = {str(k): str(v) for k, v in data.items()}
            except (json.JSONDecodeError, OSError):
                # A corrupt store must not crash the run; start clean but keep
                # the bad file for inspection by renaming it.
                try:
                    os.replace(self.path, self.path + ".corrupt")
                except OSError:
                    pass
                self._seen = {}

    def is_new(self, listing_id: str) -> bool:
        return listing_id not in self._seen

    def filter_new(self, ids: Iterable[str]) -> list[str]:
        return [i for i in ids if self.is_new(i)]

    def mark(self, listing_id: str, when: str | None = None) -> None:
        if listing_id not in self._seen:
            self._seen[listing_id] = when or datetime.now(timezone.utc).isoformat()

    def prune(self, keep: int = 5000) -> None:
        """Bound the file size: keep the most recently-seen ``keep`` ids."""
        if len(self._seen) <= keep:
            return
        ordered = sorted(self._seen.items(), key=lambda kv: kv[1], reverse=True)
        self._seen = dict(ordered[:keep])

    def save(self) -> None:
        self.prune()
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        # Atomic write: never leave a half-written state file behind.
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(self.path) or ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._seen, fh, ensure_ascii=False, indent=0)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def __len__(self) -> int:
        return len(self._seen)
