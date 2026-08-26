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

    def translate(text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        try:
            # deep-translator caps a single call around 5000 chars.
            return engine.translate(text[:4800]) or ""
        except Exception:
            return ""  # fail soft — never break the run over a translation

    return translate
