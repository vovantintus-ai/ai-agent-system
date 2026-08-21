"""Generic RSS/Atom source.

Many marketplaces, deal aggregators and classifieds expose feeds (search-result
RSS, subreddit .rss, price-tracker feeds). This adapter reads any such feed and
extracts a price from the title/summary with a currency-aware regex.

Using an official feed is the polite, ToS-friendly way to ingest a site — always
prefer a published feed or API over scraping HTML.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from ..models import Listing
from .base import Source

try:  # feedparser is optional at import time so tests without it still run
    import feedparser  # type: ignore
except Exception:  # pragma: no cover - exercised only when dep is missing
    feedparser = None  # type: ignore


_PRICE_RE = re.compile(
    r"(?:€|eur|\$|usd|£|gbp)\s*([0-9][0-9\.\s]*[0-9]|[0-9])"
    r"|([0-9][0-9\.\s]*[0-9]|[0-9])\s*(?:€|eur|\$|usd|£|gbp)",
    re.IGNORECASE,
)


def parse_price(text: str) -> Optional[float]:
    """Extract the first plausible price from free text, or None."""
    if not text:
        return None
    m = _PRICE_RE.search(text)
    if not m:
        return None
    raw = m.group(1) or m.group(2) or ""
    cleaned = raw.replace(" ", "").replace(".", "")
    if not cleaned.isdigit():
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if value > 0 else None


class RssSource(Source):
    def __init__(self, url: str, category: str, name: Optional[str] = None,
                 currency: str = "EUR"):
        self.url = url
        self.category = category
        self.name = name or f"rss:{category}"
        self.currency = currency

    def fetch(self) -> Iterable[Listing]:
        if feedparser is None:
            raise RuntimeError(
                "feedparser is not installed; run `pip install feedparser`"
            )
        feed = feedparser.parse(self.url)
        listings: list[Listing] = []
        for entry in getattr(feed, "entries", []):
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            link = getattr(entry, "link", "") or ""
            entry_id = getattr(entry, "id", "") or link or title
            posted = None
            if getattr(entry, "published", None):
                posted = entry.published
            price = parse_price(title) or parse_price(summary)
            listings.append(
                Listing(
                    id=str(entry_id),
                    title=title.strip(),
                    url=link,
                    source=self.name,
                    category=self.category,
                    price=price,
                    currency=self.currency,
                    posted_at=posted,
                    description=summary[:500],
                )
            )
        return listings
