"""Source adapters. Import lazily so a missing optional dep (feedparser,
requests) only fails when that particular source is actually used."""

from .base import Source
from .sample import SampleSource

__all__ = ["Source", "SampleSource", "build_source"]


def build_source(spec: dict) -> Source:
    """Construct a Source from a config dict: ``{"type": ..., ...}``."""
    kind = (spec.get("type") or "").lower()
    if kind == "sample":
        return SampleSource()
    if kind == "rss":
        from .rss import RssSource
        return RssSource(
            url=spec["url"],
            category=spec.get("category", "misc"),
            name=spec.get("name"),
            currency=spec.get("currency", "EUR"),
        )
    if kind == "reddit":
        from .reddit import RedditSource
        return RedditSource(
            subreddit=spec["subreddit"],
            category=spec.get("category", "misc"),
            user_agent=spec.get("user_agent", "deal-hunter/0.1 (personal use)"),
            limit=int(spec.get("limit", 50)),
            currency=spec.get("currency", "EUR"),
        )
    raise ValueError(f"Unknown source type: {spec.get('type')!r}")
