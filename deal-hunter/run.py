#!/usr/bin/env python3
"""Entry point for a single Deal Hunter run.

Designed to be invoked by a scheduled cloud agent (a "Routine") or by hand:

    python run.py --config config.yaml

It fetches, scores, dedups, writes the Markdown digest to disk, updates the seen
store, and prints a one-line summary to stdout (so a Routine's log is useful).
Exit code is non-zero only on a hard failure (bad config), not when a run simply
finds no deals.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from dealhunter.config import load_config, Config
from dealhunter.memory import SeenStore
from dealhunter.pipeline import run
from dealhunter.sources import build_source


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deal Hunter — one run")
    parser.add_argument("--config", default=None,
                        help="Path to config .yaml/.json (defaults to sample)")
    parser.add_argument("--output", default=None,
                        help="Override digest output path")
    parser.add_argument("--print", action="store_true",
                        help="Also print the digest to stdout")
    parser.add_argument("--telegram", action="store_true",
                        help="Send the digest to Telegram (reads TELEGRAM_TOKEN "
                             "and TELEGRAM_CHAT_ID from the environment)")
    parser.add_argument("--query", default=None,
                        help="Override the search query for marktplaats/rss/"
                             "reddit sources (handy on a phone — no file edit)")
    args = parser.parse_args(argv)

    try:
        config: Config = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"[deal-hunter] config error: {exc}", file=sys.stderr)
        return 2

    if args.output:
        config.output_path = args.output

    # Allow ~ and $VARS in paths so runs can write state/digest OUTSIDE the repo
    # (keeps `git pull` clean on the phone).
    config.state_path = os.path.expanduser(os.path.expandvars(config.state_path))
    config.output_path = os.path.expanduser(os.path.expandvars(config.output_path))

    sources = []
    for spec in config.sources:
        if args.query:
            # Let a phone user change what to hunt without editing the file.
            spec = dict(spec)
            if "query" in spec or (spec.get("type") == "marktplaats"):
                spec["query"] = args.query
            elif spec.get("type") == "reddit":
                spec["subreddit"] = args.query
        try:
            sources.append(build_source(spec))
        except Exception as exc:  # noqa: BLE001
            print(f"[deal-hunter] skipping bad source {spec!r}: {exc}",
                  file=sys.stderr)
    if not sources:
        print("[deal-hunter] no valid sources configured", file=sys.stderr)
        return 2

    store = SeenStore(config.state_path)
    now = datetime.now(timezone.utc)

    # Free NL->RU translator (deep-translator); None if the lib/network is
    # unavailable, in which case the digest simply shows originals only.
    translator = None
    if getattr(config, "translate", False):
        from dealhunter.translate import get_translator
        translator = get_translator(
            source=getattr(config, "translate_from", "nl"),
            target=getattr(config, "translate_to", "ru"),
        )

    result = run(sources, config, store, now=now, translator=translator)
    store.save()

    os.makedirs(os.path.dirname(config.output_path) or ".", exist_ok=True)
    with open(config.output_path, "w", encoding="utf-8") as fh:
        fh.write(result.digest_markdown)

    if args.print:
        print(result.digest_markdown)

    # Optional: push the digest straight to Telegram (used on a phone via Termux).
    if args.telegram:
        tg_token = os.environ.get("TELEGRAM_TOKEN", "").strip()
        tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        if not tg_token or not tg_chat:
            print("[deal-hunter] --telegram set but TELEGRAM_TOKEN / "
                  "TELEGRAM_CHAT_ID env vars are missing", file=sys.stderr)
        elif not result.new_deals:
            print("[deal-hunter] no new deals — nothing sent to Telegram")
        else:
            from dealhunter.notify_telegram import send
            try:
                n = send(tg_token, tg_chat, result.digest_markdown)
                print(f"[deal-hunter] sent {n} Telegram message(s)")
            except Exception as exc:  # noqa: BLE001
                print(f"[deal-hunter] Telegram send failed: {exc}",
                      file=sys.stderr)

    err_note = ""
    if result.source_errors:
        err_note = f" | source errors: {len(result.source_errors)}"
    print(
        f"[deal-hunter] fetched={result.listings_fetched} "
        f"deals={result.deals_found} new={len(result.new_deals)} "
        f"-> {config.output_path}{err_note}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
