import os
from datetime import datetime, timezone

from dealhunter.config import Config
from dealhunter.memory import SeenStore
from dealhunter.models import Listing
from dealhunter.pipeline import run, collect_listings
from dealhunter.sources.base import Source
from dealhunter.sources.sample import SampleSource

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class BrokenSource(Source):
    name = "broken"

    def fetch(self):
        raise RuntimeError("network down")


def test_collect_isolates_failures():
    listings, errors = collect_listings([SampleSource(), BrokenSource()])
    assert len(listings) == 10
    assert "broken" in errors


def test_run_finds_and_dedups(tmp_path):
    store = SeenStore(os.path.join(tmp_path, "seen.json"))
    cfg = Config(baselines={}, min_discount=0.20, min_score=10, min_samples=3)

    r1 = run([SampleSource()], cfg, store, now=NOW)
    assert r1.listings_fetched == 10
    assert r1.deals_found >= 2          # the two "urgent" underpriced items
    assert len(r1.new_deals) == r1.deals_found
    assert "# Deal Hunter" in r1.digest_markdown

    # Second run with the same store: nothing new (dedup works).
    r2 = run([SampleSource()], cfg, store, now=NOW)
    assert r2.deals_found == r1.deals_found
    assert r2.new_deals == []
    assert "No new under-priced" in r2.digest_markdown


def test_run_uses_baseline_for_thin_category(tmp_path):
    store = SeenStore(os.path.join(tmp_path, "seen.json"))
    one = [Listing("only", "cheap camera", "http://x", "t", "cameras",
                   price=100, posted_at=NOW.isoformat())]

    class OneSource(Source):
        name = "one"

        def fetch(self):
            return one

    cfg = Config(baselines={"cameras": 400}, min_discount=0.20,
                 min_score=10, min_samples=3)
    r = run([OneSource()], cfg, store, now=NOW)
    assert r.deals_found == 1
    assert r.new_deals[0].discount_pct == 0.75
