# Deal Hunter

An autonomous agent that watches classifieds / marketplaces / deal feeds and
surfaces **under-priced listings** — items offered well below their category's
going rate — as a ranked daily digest. It is built to run as a scheduled cloud
agent (a "Routine"): it wakes up, fetches, scores, dedups, writes a digest, and
goes back to sleep.

It produces **signals, not purchases**. The agent never buys, sells, or messages
anyone. It finds the opportunity and explains why; the decision and the action
stay with you.

## How it works

```
sources ──▶ pricing ──▶ scoring ──▶ dedup (memory) ──▶ digest
(RSS,       (median      (discount    (never alert       (ranked
 Reddit,     reference    + freshness   twice on the       Markdown)
 sample)     per          + keyword     same listing)
             category)    bonus)
```

1. **Sources** fetch normalized `Listing`s. Prefer official feeds/APIs over
   HTML scraping (politer and ToS-friendly). Ships with:
   - `sample` — offline demo data, no network (use it first).
   - `rss` — any RSS/Atom feed; extracts price from title/summary.
   - `reddit` — a public subreddit's newest posts.
2. **Pricing** computes a fair *reference price* per category as the **median**
   of comparable priced listings (robust to a few very high asking prices).
   Thin categories fall back to `baselines` you set in config.
3. **Scoring** rates each listing 0–100: discount vs reference (dominant),
   plus small freshness and watch-term bonuses. Discount is a hard gate — a
   fresh, keyword-matching item is never flagged unless it is genuinely cheap.
4. **Memory** (`state/seen.json`) guarantees you never see the same listing
   twice. Atomic writes; self-heals a corrupt file; size-bounded.
5. **Digest** renders the new deals as Markdown with a *why flagged* line each.

## Quick start

```bash
pip install -r requirements.txt          # or just run the sample with no deps
python run.py --print                     # runs the offline sample source
```

You'll get a digest at `digests/latest.md` and a dedup store at
`state/seen.json`. Run it twice — the second run reports nothing new.

## Configure real sources

Copy `config.example.yaml` to `config.yaml` and edit, then:

```bash
python run.py --config config.yaml --print
```

A minimal real config:

```yaml
sources:
  - type: rss
    name: my-classifieds-tools
    url: "https://<site>/search.rss?q=makita"
    category: tools
  - type: reddit
    subreddit: buildapcsales
    category: laptops
watch_terms: [makita, bosch, urgent, "quick sale"]
baselines:   { tools: 200, laptops: 600 }
min_discount: 0.20
```

> **Adding a site without a feed:** implement a `Source` subclass in
> `dealhunter/sources/` returning `Listing`s, and register it in
> `sources/__init__.py:build_source`. Respect each site's terms of service and
> robots.txt; keep polling gentle. Where an official feed or API exists, use it.

## Run it on a schedule (cloud agent)

Point a daily/hourly Routine at:

```bash
python run.py --config config.yaml
```

Commit `state/seen.json` and `digests/latest.md` after each run (or write them
to Google Drive) so memory and history survive the ephemeral container. The
run prints a one-line summary (`fetched=… deals=… new=…`) for the Routine log.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The pure logic (pricing, scoring, memory, digest, pipeline, price parsing) is
fully unit-tested and needs no network.

## Honest limits

- **A signal is not profit.** You still have to act, and the trade carries its
  own risk. Resale schemes need starting capital.
- **Reference price is heuristic.** A median over noisy listings is a rough
  guide, not an appraisal — always eyeball the item and seller.
- **Respect platforms.** Automated collection can violate a site's terms; favor
  official feeds/APIs, and never automate messaging or purchases.

## Layout

```
dealhunter/
  models.py        Listing, Deal
  pricing.py       median reference price per category
  scoring.py       discount + freshness + keyword scoring
  memory.py        durable dedup store (atomic, self-healing)
  digest.py        Markdown rendering
  pipeline.py      fetch -> price -> score -> dedup -> digest
  config.py        YAML/JSON config
  sources/         sample, rss, reddit adapters (+ build_source)
run.py             single-run entry point (for Routines / CLI)
tests/             unit tests (no network)
```

## License

MIT
