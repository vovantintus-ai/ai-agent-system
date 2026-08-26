#!/usr/bin/env python3
"""One-shot Telegram self-test.

Reads TELEGRAM_TOKEN from the environment, finds the most recent chat that has
messaged the bot (via getUpdates), and sends a test message to it. Prints the
resolved chat id so it can be saved as TELEGRAM_CHAT_ID. Never prints the token.

Run from GitHub Actions (open network) — this environment cannot reach Telegram.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"


def call(token: str, method: str, params: dict | None = None) -> dict:
    url = API.format(token=token, method=method)
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(url, data=data if params else None)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main() -> int:
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if not token:
        print("::error::TELEGRAM_TOKEN secret is not set. Add it first.")
        return 1

    # Prefer an explicit chat id if provided; else discover from getUpdates.
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not chat_id:
        updates = call(token, "getUpdates")
        if not updates.get("ok"):
            print("Telegram error on getUpdates:", updates.get("description"))
            return 1
        for upd in reversed(updates.get("result", [])):
            msg = upd.get("message") or upd.get("edited_message") or {}
            cid = (msg.get("chat") or {}).get("id")
            if cid is not None:
                chat_id = str(cid)
                break

    if not chat_id:
        print("No chat found. Open @Awtyt_Bot in Telegram, press Start / send")
        print("it any message, then run this workflow again.")
        return 0  # not a failure — just needs a message first

    resp = call(token, "sendMessage", {
        "chat_id": chat_id,
        "text": "✅ Тест Deal Hunter: бот на связи. Сюда будут приходить "
                "оповещения о найденных сделках/вакансиях.",
        "disable_web_page_preview": "true",
    })
    if resp.get("ok"):
        print(f"Sent a test message to chat_id = {chat_id}")
        print(f"Save this as the secret TELEGRAM_CHAT_ID: {chat_id}")
        return 0
    print("Telegram error on sendMessage:", resp.get("description"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
