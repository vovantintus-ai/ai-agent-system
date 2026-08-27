"""The end-to-end run: fetch -> price -> score -> dedup -> digest.

Kept free of I/O side effects except through the injected ``SeenStore`` and the
returned digest string, so it is straightforward to test.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional, Sequence

from . import pricing, scoring
from .config import Config
from .digest import render_digest
from .memory import SeenStore
from .models import Deal, Listing
from .sources.base import Source


def balance_by_category(deals: list[Deal], per_category: int,
                        total: int) -> list[Deal]:
    """Give each category fair space in the digest: take up to ``per_category``
    highest-scoring deals from each category (so a flood of cheap items in one
    category cannot crowd the others out), capped at ``total`` overall."""
    ordered = sorted(deals, key=lambda d: d.score, reverse=True)
    counts: dict[str, int] = defaultdict(int)
    out: list[Deal] = []
    for d in ordered:
        cat = d.listing.category
        if counts[cat] < per_category:
            out.append(d)
            counts[cat] += 1
        if len(out) >= total:
            break
    return out


@dataclass
class RunResult:
    listings_fetched: int
    deals_found: int
    new_deals: list[Deal]
    digest_markdown: str
    source_errors: dict[str, str]


def collect_listings(
    sources: Sequence[Source],
) -> tuple[list[Listing], dict[str, str]]:
    """Fetch from every source, isolating failures so one bad source cannot
    abort the whole run."""
    listings: list[Listing] = []
    errors: dict[str, str] = {}
    for src in sources:
        name = getattr(src, "name", src.__class__.__name__)
        try:
            items = list(src.fetch())
            listings.extend(items)
            print(f"[deal-hunter] {name}: {len(items)} listings",
                  file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - deliberate isolation boundary
            errors[name] = str(exc)
            print(f"[deal-hunter] {name}: ERROR {exc}", file=sys.stderr)
    return listings, errors


def run(
    sources: Sequence[Source],
    config: Config,
    store: SeenStore,
    now: Optional[datetime] = None,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    translator: Optional[Callable[[str], str]] = None,
) -> RunResult:
    now = now or clock()

    listings, errors = collect_listings(sources)

    max_price = getattr(config, "max_price", 0) or 0
    min_price = getattr(config, "min_price", 0) or 0
    if max_price > 0:
        # "List everything in this price band" mode (e.g. real estate): no
        # discount logic — keep priced listings between min and max, cheapest
        # first. min_price keeps rentals out of the for-sale feed.
        matched = [
            l for l in listings
            if l.has_price() and min_price <= l.price <= max_price
        ]
        matched.sort(key=lambda l: float(l.price))
        # Diagnosis: if nothing fell in the band, show a sample of what came
        # back (real price or "no-price") so we can see why.
        if not matched and listings:
            print(f"[deal-hunter] 0 in band {min_price:.0f}-{max_price:.0f}; "
                  f"sample of {len(listings)} fetched:", file=sys.stderr)
            for l in listings[:8]:
                p = f"{l.price:.0f}" if l.has_price() else "no-price"
                print(f"[deal-hunter]   {p} {l.currency} | {l.title[:45]}",
                      file=sys.stderr)
        deals = [
            Deal(
                listing=l,
                reference_price=float(max_price),
                discount_pct=0.0,
                score=0.0,
                reasons=[f"at/under {max_price:.0f} {l.currency}"],
            )
            for l in matched
        ]
    else:
        refs = pricing.reference_prices(
            listings, baselines=config.baselines, min_samples=config.min_samples
        )
        deals = scoring.find_deals(
            listings,
            refs,
            now=now,
            watch_terms=config.watch_terms,
            min_discount=config.min_discount,
            min_score=config.min_score,
        )

    # Only surface deals we have not reported before.
    fresh = [d for d in deals if store.is_new(d.listing.id)]

    # Give every category fair space so one (e.g. tablets) can't crowd out the
    # others (phones, laptops, computers).
    per_cat = getattr(config, "max_per_category", 0)
    if per_cat and per_cat > 0:
        new_deals = balance_by_category(fresh, per_cat, config.max_deals)
    else:
        new_deals = fresh[:config.max_deals]

    # Mark only the deals we actually show, so the rest can appear next run.
    for d in new_deals:
        store.mark(d.listing.id, now.isoformat())

    digest = render_digest(
        new_deals, generated_at=now, limit=config.max_deals,
        translator=translator,
    )

    return RunResult(
        listings_fetched=len(listings),
        deals_found=len(deals),
        new_deals=new_deals,
        digest_markdown=digest,
        source_errors=errors,
    )
