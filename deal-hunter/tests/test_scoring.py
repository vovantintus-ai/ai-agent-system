from datetime import datetime, timedelta, timezone

from dealhunter.models import Listing
from dealhunter.scoring import (
    find_deals,
    freshness_bonus,
    keyword_bonus,
    score_listing,
)

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def iso(hours_ago):
    return (NOW - timedelta(hours=hours_ago)).isoformat()


def L(id, cat, price, title="item", posted=None):
    return Listing(id, title, "http://x", "test", cat, price=price, posted_at=posted)


def test_score_none_without_price():
    assert score_listing(L("1", "tools", None), 200, NOW) is None


def test_score_none_with_bad_reference():
    assert score_listing(L("1", "tools", 100), 0, NOW) is None


def test_discount_drives_score():
    cheap = score_listing(L("1", "tools", 100), 200, NOW)  # 50% off
    mild = score_listing(L("2", "tools", 180), 200, NOW)   # 10% off
    assert cheap.score > mild.score
    assert cheap.discount_pct == 0.5


def test_freshness_bonus_bounds():
    assert freshness_bonus(iso(1), NOW) == 10.0
    assert freshness_bonus(iso(100), NOW) == 0.0
    assert freshness_bonus(None, NOW) == 0.0
    mid = freshness_bonus(iso(39), NOW)
    assert 0 < mid < 10


def test_keyword_bonus_caps():
    assert keyword_bonus("Makita Bosch Hilti drill", ["makita", "bosch", "hilti"]) == 10.0
    assert keyword_bonus("plain drill", ["makita"]) == 0.0


def test_find_deals_applies_discount_gate():
    listings = [
        L("1", "tools", 100, posted=iso(1)),  # 50% off -> in
        L("2", "tools", 190, posted=iso(1)),  # 5% off  -> filtered by discount
    ]
    refs = {"tools": 200}
    deals = find_deals(listings, refs, NOW, min_discount=0.20, min_score=0)
    ids = [d.listing.id for d in deals]
    assert ids == ["1"]


def test_find_deals_sorted_desc():
    listings = [
        L("a", "tools", 150, posted=iso(1)),
        L("b", "tools", 80, posted=iso(1)),
    ]
    refs = {"tools": 200}
    deals = find_deals(listings, refs, NOW, min_discount=0.10, min_score=0)
    assert [d.listing.id for d in deals] == ["b", "a"]


def test_find_deals_skips_unknown_category():
    listings = [L("x", "unknown", 10, posted=iso(1))]
    deals = find_deals(listings, {"tools": 200}, NOW)
    assert deals == []
