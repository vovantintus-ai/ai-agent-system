"""Estimate a 'fair' reference price for a group of comparable listings.

Strategy (deliberately simple and explainable):
  * Group listings by category.
  * Within a group, the reference price is the median of the priced listings.
  * A user-supplied baseline (config) overrides the computed median when present,
    which is useful for thin categories where a few listings are not enough.

Median is used rather than mean because marketplace prices are noisy and
right-skewed (a few very high asking prices would drag a mean upward and hide
genuine bargains).
"""

from __future__ import annotations

from statistics import median
from typing import Iterable, Optional

from .models import Listing


def _median_price(listings: Iterable[Listing]) -> Optional[float]:
    prices = [float(l.price) for l in listings if l.has_price()]
    if not prices:
        return None
    return float(median(prices))


def reference_prices(
    listings: Iterable[Listing],
    baselines: Optional[dict[str, float]] = None,
    min_samples: int = 3,
) -> dict[str, float]:
    """Return {category: reference_price}.

    A category gets a computed median only if it has at least ``min_samples``
    priced listings; otherwise it falls back to a configured baseline if one is
    given. Categories with neither are omitted (callers treat a missing
    reference as 'cannot judge').
    """
    baselines = baselines or {}
    listings = list(listings)

    by_category: dict[str, list[Listing]] = {}
    for l in listings:
        by_category.setdefault(l.category, []).append(l)

    refs: dict[str, float] = {}
    for category, group in by_category.items():
        priced = [l for l in group if l.has_price()]
        if len(priced) >= min_samples:
            med = _median_price(priced)
            if med and med > 0:
                refs[category] = med
                continue
        if category in baselines and baselines[category] > 0:
            refs[category] = float(baselines[category])

    # Baselines for categories not present in this batch are still useful.
    for category, price in baselines.items():
        refs.setdefault(category, float(price))

    return refs
