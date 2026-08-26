"""Marktplaats source adapter.

HONEST CAVEATS — read before relying on this:
  * Marktplaats has NO official public API and its Terms of Service prohibit
    automated access. This adapter reads the same search endpoint the website's
    own frontend uses; treat it as a gray area and use it gently, for personal
    use, at your own risk.
  * The site is bot-protected and BLOCKS datacenter IP ranges, so it generally
    returns nothing from GitHub Actions runners. Run this from your own machine
    (a residential IP) for it to work.
  * Phone numbers are NOT in search results — they are hidden behind a
    "show phone number" action on each listing's page — so phone is not
    available through this adapter.

What it does return per listing: title, price, city (location), direct URL, and
a description snippet (in Dutch) that the digest can translate to Russian.
"""

from __future__ import annotations

from typing import Iterable, Optional

from ..models import Listing
from .base import Source

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

SEARCH_URL = "https://www.marktplaats.nl/lrp/api/search"


class MarktplaatsSource(Source):
    def __init__(self, query: str, category: str = "marktplaats",
                 limit: int = 30, currency: str = "EUR",
                 user_agent: Optional[str] = None):
        self.query = query
        self.category = category
        self.limit = int(limit)
        self.currency = currency
        self.name = f"marktplaats:{query}"
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; deal-hunter/0.1; personal use)"
        )

    def fetch(self) -> Iterable[Listing]:
        if requests is None:
            raise RuntimeError("requests is not installed; run `pip install requests`")
        resp = requests.get(
            SEARCH_URL,
            params={"query": self.query, "limit": self.limit, "offset": 0},
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()

        listings: list[Listing] = []
        for item in data.get("listings", []):
            title = (item.get("title") or "").strip()
            price_info = item.get("priceInfo") or {}
            cents = price_info.get("priceCents")
            price = (round(cents / 100, 2)
                     if isinstance(cents, (int, float)) and cents > 0 else None)
            city = (item.get("location") or {}).get("cityName", "") or ""
            vip = item.get("vipUrl", "") or ""
            link = vip if vip.startswith("http") else f"https://www.marktplaats.nl{vip}"
            desc = (item.get("description") or "").strip()
            item_id = str(item.get("itemId") or item.get("id") or link or title)
            listings.append(
                Listing(
                    id=item_id,
                    title=title,
                    url=link,
                    source=self.name,
                    category=self.category,
                    price=price,
                    currency=self.currency,
                    posted_at=None,
                    location=city,
                    description=desc[:600],
                )
            )
        return listings
