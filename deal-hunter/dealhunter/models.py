"""Core data types shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Listing:
    """A single item offered for sale, normalized from any source."""

    id: str
    title: str
    url: str
    source: str
    category: str
    price: Optional[float] = None
    currency: str = "EUR"
    posted_at: Optional[str] = None  # ISO-8601 string, if known
    description: str = ""
    location: str = ""  # city / area, when the source provides it

    def has_price(self) -> bool:
        return self.price is not None and self.price > 0


@dataclass
class Deal:
    """A listing that scored well enough to be worth surfacing."""

    listing: Listing
    reference_price: float
    discount_pct: float  # 0.35 == 35% below reference
    score: float
    reasons: list[str] = field(default_factory=list)

    @property
    def absolute_saving(self) -> float:
        if not self.listing.has_price():
            return 0.0
        return max(0.0, self.reference_price - float(self.listing.price))
