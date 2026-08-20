from dealhunter.models import Listing
from dealhunter.pricing import reference_prices


def L(id, cat, price):
    return Listing(id, f"item {id}", "http://x", "test", cat, price=price)


def test_median_reference_ignores_unpriced():
    listings = [
        L("1", "tools", 100),
        L("2", "tools", 200),
        L("3", "tools", 300),
        L("4", "tools", None),  # ignored
    ]
    refs = reference_prices(listings, min_samples=3)
    assert refs["tools"] == 200


def test_thin_category_falls_back_to_baseline():
    listings = [L("1", "laptops", 500)]  # only 1 sample, below min_samples
    refs = reference_prices(listings, baselines={"laptops": 600}, min_samples=3)
    assert refs["laptops"] == 600


def test_thin_category_without_baseline_is_omitted():
    listings = [L("1", "rare", 500)]
    refs = reference_prices(listings, min_samples=3)
    assert "rare" not in refs


def test_baseline_for_absent_category_is_kept():
    refs = reference_prices([], baselines={"bikes": 250}, min_samples=3)
    assert refs["bikes"] == 250


def test_computed_median_beats_baseline_when_enough_samples():
    listings = [L("1", "tools", 100), L("2", "tools", 110), L("3", "tools", 120)]
    refs = reference_prices(listings, baselines={"tools": 999}, min_samples=3)
    assert refs["tools"] == 110
