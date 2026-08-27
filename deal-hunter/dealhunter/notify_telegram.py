"""Send text to a Telegram chat, split into Telegram-sized chunks.

Stdlib only (urllib). Token and chat id are passed in by the caller (read from
env by run.py) — never hardcoded here.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/sendMessage"
PHOTO_API = "https://api.telegram.org/bot{token}/sendPhoto"
LIMIT = 4000  # Telegram hard cap is 4096; leave headroom.
CAPTION_LIMIT = 1024  # Telegram caption cap.


def _chunks(text: str, size: int = LIMIT):
    """Split on line boundaries so a message never cuts mid-line; a single
    over-long line is hard-split."""
    out, buf = [], ""
    for line in text.splitlines(keepends=True):
        if len(line) > size:
            if buf:
                out.append(buf)
                buf = ""
            for i in range(0, len(line), size):
                out.append(line[i:i + size])
            continue
        if len(buf) + len(line) > size:
            out.append(buf)
            buf = line
        else:
            buf += line
    if buf:
        out.append(buf)
    return out or [""]


def send(token: str, chat_id: str, text: str) -> int:
    """Send text (chunked). Returns the number of messages sent."""
    sent = 0
    for chunk in _chunks(text):
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": "true",
        }).encode()
        req = urllib.request.Request(API.format(token=token), data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
            if payload.get("ok"):
                sent += 1
    return sent


def send_photo(token: str, chat_id: str, photo_url: str, caption: str) -> bool:
    """Send one photo with a caption. Falls back to a text message if the
    photo can't be sent (bad/missing image URL)."""
    caption = caption[:CAPTION_LIMIT]
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
    }).encode()
    try:
        req = urllib.request.Request(PHOTO_API.format(token=token), data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            if json.load(resp).get("ok"):
                return True
    except Exception:
        pass
    # Fallback: send the caption as plain text so the listing isn't lost.
    return send(token, chat_id, caption) > 0


def send_deals_as_photos(token: str, chat_id: str, deals,
                         translator=None) -> int:
    """Send each deal as a photo + caption, GROUPED BY CITY. Before each city's
    listings a header message is sent so the cities are clearly separated."""
    from collections import OrderedDict

    groups: "OrderedDict[str, list]" = OrderedDict()
    for d in deals:
        city = d.listing.category or "Overig"
        groups.setdefault(city, []).append(d)

    sent = 0
    for city, items in groups.items():
        # City separator header.
        send(token, chat_id,
             f"━━━━━━━━━━\n🏙 {city.upper()} — {len(items)}\n━━━━━━━━━━")
        for d in items:
            l = d.listing
            price = f"{l.price:.0f} {l.currency}" if l.has_price() else "n/a"
            lines = [l.title]
            if translator:
                ru = translator(l.title)
                if ru and ru.strip().lower() != l.title.strip().lower():
                    lines.append("🇷🇺 " + ru)
            meta = f"💶 {price}"
            if l.location:
                meta += f" · 📍 {l.location}"
            if l.condition:
                meta += f" · {l.condition}"
            lines.append(meta)
            lines.append(l.url)
            caption = "\n".join(lines)
            if l.image_url:
                ok = send_photo(token, chat_id, l.image_url, caption)
            else:
                ok = send(token, chat_id, caption) > 0
            if ok:
                sent += 1
    return sent
