"""The end-to-end run: fetch -> price -> score -> dedup -> digest.

Kept free of I/O side effects except through the injected ``SeenStore`` and the
returned digest string, so it is straightforward to test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional, Sequence

from . import pricing, scoring
from .config import Config
from .digest import render_digest
from .memory import SeenStore
from .models import Deal, Listing
from .sources.base import Source


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
        try:
            listings.extend(src.fetch())
        except Exception as exc:  # noqa: BLE001 - deliberate isolation boundary
            errors[getattr(src, "name", src.__class__.__name__)] = str(exc)
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
    new_deals = [d for d in deals if store.is_new(d.listing.id)]
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
