"""Send text to a Telegram chat, split into Telegram-sized chunks.

Stdlib only (urllib). Token and chat id are passed in by the caller (read from
env by run.py) — never hardcoded here.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/sendMessage"
LIMIT = 4000  # Telegram hard cap is 4096; leave headroom.


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
