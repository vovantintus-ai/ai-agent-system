"""Very simple scam / red-flag detector for listing text.

These are HEURISTICS, not proof. They catch common Dutch rental/job scam
phrases (pay upfront, off-platform payment, no viewing, money-transfer apps).
A clean scan does NOT mean a listing is safe — always verify the person,
reviews and KvK, use a contract, and never pay before seeing/agreeing.
"""

from __future__ import annotations

# phrase -> short Russian warning
_FLAGS = {
    "vooruitbetaling": "просят предоплату",
    "vooraf betalen": "просят платить вперёд",
    "vooraf overmaken": "просят перевести вперёд",
    "aanbetaling": "просят задаток",
    "borg overmaken": "просят перевести залог",
    "zonder bezichtiging": "без осмотра",
    "geen bezichtiging": "без осмотра",
    "sleutel opsturen": "ключ «вышлют почтой»",
    "western union": "оплата Western Union",
    "moneygram": "оплата MoneyGram",
    "bitcoin": "оплата криптой",
    "cryptomunt": "оплата криптой",
    "buiten marktplaats": "оплата вне площадки",
    "inschrijfgeld": "просят плату за регистрацию",
    "registratiekosten": "просят плату за регистрацию",
    "startkosten": "просят стартовый взнос",
    "per direct overmaken": "требуют срочный перевод",
}


def scan(*texts: str) -> list[str]:
    """Return a list of red-flag warnings found across the given texts."""
    blob = " ".join(t for t in texts if t).lower()
    out = []
    for phrase, warn in _FLAGS.items():
        if phrase in blob and warn not in out:
            out.append(warn)
    return out
