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

# Known Dutch condition values Marktplaats uses in listing attributes.
_CONDITIONS = {
    "nieuw", "gebruikt", "zo goed als nieuw", "refurbished",
    "nieuwstaat", "als nieuw",
}


def _extract_condition(item: dict) -> str:
    """Best-effort pull of the item condition (new/used) from attributes."""
    for attrs_key in ("attributes", "extendedAttributes"):
        for a in item.get(attrs_key) or []:
            if not isinstance(a, dict):
                continue
            key = str(a.get("key", "")).lower()
            val = str(a.get("value", "")).strip()
            if not val:
                continue
            if "condit" in key or "staat" in key:
                return val
            if val.lower() in _CONDITIONS:
                return val
    return ""


class MarktplaatsSource(Source):
    def __init__(self, query: str, category: str = "marktplaats",
                 limit: int = 30, currency: str = "EUR",
                 user_agent: Optional[str] = None,
                 postcode: Optional[str] = None,
                 distance_km: Optional[int] = None,
                 require_path: Optional[str] = None,
                 exclude_paths: Optional[list] = None):
        self.query = query
        self.category = category
        self.limit = int(limit)
        self.currency = currency
        self.postcode = postcode
        self.distance_km = int(distance_km) if distance_km else None
        # Only keep listings whose URL contains this (e.g. "huizen-en-kamers"
        # to restrict to real estate and drop kitchens/appliances/vacation ads).
        self.require_path = (require_path or "").lower() or None
        # Drop listings whose URL contains ANY of these (garages, land, etc.).
        self.exclude_paths = [p.lower() for p in (exclude_paths or []) if p]
        loc = f"@{postcode}+{distance_km}km" if postcode else ""
        self.name = f"marktplaats:{query}{loc}"
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; deal-hunter/0.1; personal use)"
        )

    def fetch(self) -> Iterable[Listing]:
        if requests is None:
            raise RuntimeError("requests is not installed; run `pip install requests`")
        params = {"query": self.query, "limit": self.limit, "offset": 0}
        if self.postcode:
            params["postcode"] = self.postcode
        if self.distance_km:
            params["distanceMeters"] = self.distance_km * 1000
        resp = requests.get(
            SEARCH_URL,
            params=params,
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
            low = link.lower()
            # Restrict to the wanted section (e.g. real estate) by URL path.
            if self.require_path and self.require_path not in low:
                continue
            # Drop explicitly-unwanted sub-sections (garages, land, vacation…).
            if any(bad in low for bad in self.exclude_paths):
                continue
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
                    condition=_extract_condition(item),
                    description=desc[:600],
                )
            )
        return listings
