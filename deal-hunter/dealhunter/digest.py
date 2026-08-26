"""Render a scored deal list into a readable Markdown digest."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional, Sequence

from .models import Deal

# Small NL->RU map for the condition field so it reads nicely without a call.
_COND_RU = {
    "nieuw": "новое",
    "gebruikt": "б/у",
    "zo goed als nieuw": "как новое",
    "als nieuw": "как новое",
    "nieuwstaat": "идеальное состояние",
    "refurbished": "восстановленное",
}


def render_digest(
    deals: Sequence[Deal],
    generated_at: datetime,
    title: str = "Deal Hunter — daily digest",
    limit: int = 25,
    translator: Optional[Callable[[str], str]] = None,
) -> str:
    """Render deals as Markdown. If ``translator`` is given (e.g. NL->RU), each
    listing shows the original title/description plus its translation."""
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
            if deal.absolute_saving > 0 and deal.score > 0
            else ""
        )
        lines.append(f"## {i}. {l.title}")
        lines.append("")
        # Russian translation of the title (NL -> RU) when a translator is set.
        if translator:
            title_ru = translator(l.title)
            if title_ru and title_ru.strip().lower() != l.title.strip().lower():
                lines.append(f"- 🇷🇺 **Перевод:** {title_ru}")
        lines.append(f"- **Price:** {price}{saving}")
        # Discount/score line only makes sense for the deal-scoring mode; in the
        # "list under a price cap" mode (real estate) it is meaningless, so skip.
        if deal.score > 0 or deal.discount_pct != 0:
            lines.append(
                f"- **Reference:** {deal.reference_price:.0f} {l.currency} "
                f"· **Discount:** {deal.discount_pct * 100:.0f}% "
                f"· **Score:** {deal.score:.0f}"
            )
        if l.location:
            lines.append(f"- **Location:** {l.location}")
        if getattr(l, "condition", ""):
            ru = _COND_RU.get(l.condition.strip().lower(), "")
            lines.append(
                f"- **Состояние:** {l.condition}" + (f" ({ru})" if ru else "")
            )
        lines.append(f"- **Source:** {l.source} · **Category:** {l.category}")
        if l.posted_at:
            lines.append(f"- **Posted:** {l.posted_at}")
        lines.append(f"- **Link:** {l.url}")
        # Dutch description + its Russian translation, when available.
        if l.description:
            snippet = l.description.strip()[:300]
            lines.append(f"- 🇳🇱 **Beschrijving:** {snippet}")
            if translator:
                desc_ru = translator(snippet)
                if desc_ru:
                    lines.append(f"- 🇷🇺 **Описание:** {desc_ru}")
        if deal.reasons:
            lines.append(f"- **Why flagged:** {'; '.join(deal.reasons)}")
        lines.append("")

    lines.append("---")
    lines.append(
        "_Signals only — verify the item and seller before buying. "
        "Prices and availability change fast._"
    )
    return "\n".join(lines) + "\n"
