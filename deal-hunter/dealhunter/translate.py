"""Free NL->RU translation for the digest — no API key, no Groq, no cost.

Uses `deep-translator`, which talks to Google Translate's free public endpoint.
It needs outbound network (works on GitHub runners / your PC, not in a locked
environment). Everything fails soft: if the library or network is unavailable,
the translator is simply absent and the digest shows the original text only.
"""

from __future__ import annotations

from typing import Callable, Optional


def get_translator(source: str = "nl", target: str = "ru") -> Optional[Callable[[str], str]]:
    """Return a `translate(text)->str` function, or None if unavailable."""
    try:
        from deep_translator import GoogleTranslator
    except Exception:
        return None

    try:
        engine = GoogleTranslator(source=source, target=target)
    except Exception:
        return None

    import time

    def translate(text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        # One retry with a short pause — the free endpoint rate-limits when many
        # calls come in a row.
        for attempt in range(2):
            try:
                return engine.translate(text[:4800]) or ""
            except Exception:
                if attempt == 0:
                    time.sleep(1.5)
                else:
                    return ""  # fail soft — never break the run
        return ""

    return translate
