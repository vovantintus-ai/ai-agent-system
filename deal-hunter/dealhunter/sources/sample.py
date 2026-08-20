"""Offline sample source.

Ships a fixed set of listings so the agent can be run and demoed end-to-end
with zero network access (and so tests are deterministic). Use it to see the
pipeline work before wiring real sources.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from ..models import Listing
from .base import Source


def _iso(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


class SampleSource(Source):
    name = "sample"

    def fetch(self) -> Iterable[Listing]:
        return [
            # --- power tools: reference median will be ~200 ---
            Listing("s1", "Makita drill, barely used", "https://example.com/s1",
                    self.name, "tools", price=95, posted_at=_iso(2),
                    description="Moving out, quick sale"),
            Listing("s2", "Bosch professional drill", "https://example.com/s2",
                    self.name, "tools", price=210, posted_at=_iso(20)),
            Listing("s3", "DeWalt drill set", "https://example.com/s3",
                    self.name, "tools", price=200, posted_at=_iso(40)),
            Listing("s4", "Hilti drill, new", "https://example.com/s4",
                    self.name, "tools", price=260, posted_at=_iso(5)),
            Listing("s5", "Generic drill", "https://example.com/s5",
                    self.name, "tools", price=190, posted_at=_iso(60)),
            # --- laptops: reference median will be ~600 ---
            Listing("s6", "ThinkPad X1, urgent sale", "https://example.com/s6",
                    self.name, "laptops", price=380, posted_at=_iso(1),
                    description="Need cash today"),
            Listing("s7", "MacBook Air M1", "https://example.com/s7",
                    self.name, "laptops", price=650, posted_at=_iso(30)),
            Listing("s8", "Dell XPS 13", "https://example.com/s8",
                    self.name, "laptops", price=600, posted_at=_iso(50)),
            Listing("s9", "HP Spectre", "https://example.com/s9",
                    self.name, "laptops", price=620, posted_at=_iso(10)),
            # --- no price: should be ignored, never crash ---
            Listing("s10", "Bundle of tools, ask me", "https://example.com/s10",
                    self.name, "tools", price=None, posted_at=_iso(3)),
        ]
