"""Render a scored deal list into a readable Markdown digest."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from .models import Deal


def render_digest(
    deals: Sequence[Deal],
    generated_at: datetime,
    title: str = "Deal Hunter — daily digest",
    limit: int = 25,
) -> str:
    ts = generated_at.strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [f"# {title}", "", f"_Generated {ts}_", ""]

    if not deals:
        lines.append(
            "No new under-priced listings cleared the thresholds this run. "
            "That is normal on quiet days — the agent will keep watching."
        )
        return "\n".join(lines) + "\n"

    shown = list(deals)[:limit]
    lines.append(
        f"**{len(deals)} new deal(s)** found; showing top {len(shown)}."
    )
    lines.append("")

    for i, deal in enumerate(shown, start=1):
        l = deal.listing
        price = f"{l.price:.0f} {l.currency}" if l.has_price() else "n/a"
        saving = (
            f" (~{deal.absolute_saving:.0f} {l.currency} below ref)"
            if deal.absolute_saving > 0
            else ""
        )
        lines.append(f"## {i}. {l.title}")
        lines.append("")
        lines.append(f"- **Price:** {price}{saving}")
        lines.append(
            f"- **Reference:** {deal.reference_price:.0f} {l.currency} "
            f"· **Discount:** {deal.discount_pct * 100:.0f}% "
            f"· **Score:** {deal.score:.0f}"
        )
        lines.append(f"- **Source:** {l.source} · **Category:** {l.category}")
        if l.posted_at:
            lines.append(f"- **Posted:** {l.posted_at}")
        lines.append(f"- **Link:** {l.url}")
        if deal.reasons:
            lines.append(f"- **Why flagged:** {'; '.join(deal.reasons)}")
        lines.append("")

    lines.append("---")
    lines.append(
        "_Signals only — verify the item and seller before buying. "
        "Prices and availability change fast._"
    )
    return "\n".join(lines) + "\n"
