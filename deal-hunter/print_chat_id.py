#!/usr/bin/env python3
"""Read a Telegram getUpdates JSON payload from stdin and print chat id(s).

Used by the get-telegram-chat-id helper workflow so the owner can discover the
chat id to put in the TELEGRAM_CHAT_ID secret. Never prints the bot token.
"""

import json
import sys


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Could not parse Telegram response.")
        return 1

    if not data.get("ok"):
        print("Telegram error:", data.get("description", "unknown"))
        return 1

    seen: dict = {}
    for upd in data.get("result", []):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat") or {}
        cid = chat.get("id")
        if cid is None:
            continue
        who = chat.get("username") or chat.get("title") or chat.get("first_name") or ""
        seen[cid] = who

    if not seen:
        print("No messages yet. Open your bot in Telegram, press Start / send")
        print("it a message, then run this workflow again.")
        return 0

    print("Found chat id(s) — use the one that is you:")
    for cid, who in seen.items():
        print(f"  chat_id = {cid}   ({who})")
    print("")
    print("Now add it as the repo secret TELEGRAM_CHAT_ID.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
