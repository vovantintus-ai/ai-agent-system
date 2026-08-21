"""Reddit source via the public JSON endpoints.

Reddit exposes ``https://www.reddit.com/r/<sub>/new.json`` publicly. Many
deal/marketplace communities post there (local buy/sell subs, deal subs). This
is a legitimate public API — set a descriptive User-Agent as Reddit requests.

No auth needed for read-only public listings, but heavy use should move to the
official OAuth API. Keep polling gentle.
"""

from __future__ import annotations

from typing import Iterable, Optional

from ..models import Listing
from .base import Source
from .rss import parse_price

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class RedditSource(Source):
    def __init__(self, subreddit: str, category: str,
                 user_agent: str = "deal-hunter/0.1 (personal use)",
                 limit: int = 50, currency: str = "EUR"):
        self.subreddit = subreddit.lstrip("r/").strip("/")
        self.category = category
        self.user_agent = user_agent
        self.limit = limit
        self.currency = currency
        self.name = f"reddit:{self.subreddit}"

    def fetch(self) -> Iterable[Listing]:
        if requests is None:
            raise RuntimeError(
                "requests is not installed; run `pip install requests`"
            )
        url = f"https://www.reddit.com/r/{self.subreddit}/new.json"
        resp = requests.get(
            url,
            params={"limit": self.limit},
            headers={"User-Agent": self.user_agent},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        listings: list[Listing] = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "") or ""
            selftext = post.get("selftext", "") or ""
            permalink = post.get("permalink", "")
            url_full = f"https://www.reddit.com{permalink}" if permalink else \
                post.get("url", "")
            created = post.get("created_utc")
            posted_iso: Optional[str] = None
            if isinstance(created, (int, float)):
                from datetime import datetime, timezone
                posted_iso = datetime.fromtimestamp(
                    created, tz=timezone.utc
                ).isoformat()
            price = parse_price(title) or parse_price(selftext)
            listings.append(
                Listing(
                    id=str(post.get("id") or url_full or title),
                    title=title.strip(),
                    url=url_full,
                    source=self.name,
                    category=self.category,
                    price=price,
                    currency=self.currency,
                    posted_at=posted_iso,
                    description=selftext[:500],
                )
            )
        return listings
