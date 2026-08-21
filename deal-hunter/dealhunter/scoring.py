"""Turn priced listings into scored Deals.

The score is a 0..100 number combining:
  * discount magnitude vs the category reference price (the dominant term),
  * a keyword-relevance bonus (title matches the user's watch terms),
  * a freshness bonus (recently posted items are more actionable).

Everything is explainable: each Deal carries a list of human-readable reasons so
the morning digest can say *why* something was flagged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional

from .models import Deal, Listing


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def freshness_bonus(posted_at: Optional[str], now: datetime) -> float:
    """0..10 points; full marks under 6h old, decaying to 0 by 72h."""
    dt = _parse_iso(posted_at)
    if dt is None:
        return 0.0
    age_h = (now - dt).total_seconds() / 3600.0
    if age_h <= 6:
        return 10.0
    if age_h >= 72:
        return 0.0
    return round(10.0 * (72 - age_h) / (72 - 6), 2)


def keyword_bonus(title: str, watch_terms: Iterable[str]) -> float:
    """0..10 points; +5 per matched watch term, capped."""
    t = title.lower()
    hits = sum(1 for term in watch_terms if term.lower() in t)
    return float(min(10, hits * 5))


def score_listing(
    listing: Listing,
    reference_price: float,
    now: datetime,
    watch_terms: Iterable[str] = (),
) -> Optional[Deal]:
    """Score one listing against its reference price.

    Returns None if the listing has no usable price or the reference is invalid
    (we never invent a discount we cannot justify).
    """
    if not listing.has_price() or reference_price <= 0:
        return None

    price = float(listing.price)
    discount = (reference_price - price) / reference_price  # may be negative

    # Discount term: 0 at/above reference, 80 points at 50%+ below reference.
    discount_points = max(0.0, min(80.0, discount * 160.0))

    fb = freshness_bonus(listing.posted_at, now)
    kb = keyword_bonus(listing.title, watch_terms)
    score = round(discount_points + fb + kb, 2)

    reasons: list[str] = []
    if discount > 0:
        reasons.append(
            f"{discount * 100:.0f}% below the {listing.category} reference "
            f"({price:.0f} vs {reference_price:.0f} {listing.currency})"
        )
    else:
        reasons.append(
            f"at or above reference ({price:.0f} vs {reference_price:.0f} "
            f"{listing.currency})"
        )
    if fb >= 7:
        reasons.append("posted very recently")
    if kb > 0:
        reasons.append("matches your watch terms")

    return Deal(
        listing=listing,
        reference_price=reference_price,
        discount_pct=round(discount, 4),
        score=score,
        reasons=reasons,
    )


def find_deals(
    listings: Iterable[Listing],
    refs: dict[str, float],
    now: datetime,
    watch_terms: Iterable[str] = (),
    min_discount: float = 0.20,
    min_score: float = 25.0,
) -> list[Deal]:
    """Score all listings and keep the ones that clear both thresholds.

    ``min_discount`` guards against flagging items that are barely cheap;
    ``min_score`` lets freshness/keywords lift a strong candidate but never
    rescues a non-discounted item (discount is a hard gate).
    """
    watch_terms = list(watch_terms)
    deals: list[Deal] = []
    for listing in listings:
        ref = refs.get(listing.category)
        if ref is None:
            continue
        deal = score_listing(listing, ref, now, watch_terms)
        if deal is None:
            continue
        if deal.discount_pct < min_discount:
            continue
        if deal.score < min_score:
            continue
        deals.append(deal)

    deals.sort(key=lambda d: d.score, reverse=True)
    return deals
