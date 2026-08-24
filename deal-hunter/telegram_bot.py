#!/usr/bin/env python3
"""Owner-only Telegram bot for Deal Hunter.

Security model: the bot answers EXACTLY ONE chat — the owner's. Every update
from any other chat id is ignored silently (no reply, no hint that the bot
exists). This is the same allowlist idea as a single-admin check, done at the
very first gate so no command handler ever runs for a stranger.

It has no third-party dependencies — only the Python standard library — so it
runs anywhere Python does. It needs an always-on host (your PC, a small VPS,
a Raspberry Pi): GitHub Actions cannot host a long-running listener.

Environment:
    TELEGRAM_TOKEN     bot token from @BotFather (keep it secret)
    OWNER_CHAT_ID      your numeric chat id — the ONLY chat the bot serves
    DIGEST_PATH        optional, path to the latest digest (default below)

Run:
    TELEGRAM_TOKEN=... OWNER_CHAT_ID=... python3 telegram_bot.py
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"
DIGEST_PATH = os.environ.get("DIGEST_PATH", "digests/latest.md")


def _require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise SystemExit(f"[deal-hunter-bot] missing required env var: {name}")
    return val


class Bot:
    def __init__(self, token: str, owner_chat_id: str):
        self.token = token
        # Store as string for a stable comparison regardless of int/str source.
        self.owner = str(owner_chat_id).strip()
        self.offset = 0

    # --- transport ---------------------------------------------------------
    def _call(self, method: str, params: dict) -> dict:
        url = API.format(token=self.token, method=method)
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=65) as resp:
            return json.load(resp)

    def send(self, text: str) -> None:
        """Only ever sends to the owner — the chat id is not a parameter."""
        # Telegram hard-caps a message at 4096 chars.
        self._call("sendMessage", {
            "chat_id": self.owner,
            "text": text[:4096],
            "disable_web_page_preview": "true",
        })

    # --- command handling --------------------------------------------------
    def handle(self, text: str) -> str:
        cmd = text.strip().split()[0].lower() if text.strip() else ""
        if cmd in ("/start", "/help", "помощь"):
            return (
                "Deal Hunter — пульт (owner-only)\n\n"
                "/status — состояние агента\n"
                "/latest — последняя сводка сделок\n"
                "/help — эта справка\n\n"
                "Бот отвечает только вам; сообщения других игнорируются."
            )
        if cmd in ("/status", "статус"):
            exists = os.path.exists(DIGEST_PATH)
            return (
                "Состояние:\n"
                "• бот: работает, слушает только ваш чат\n"
                f"• последняя сводка: {'есть' if exists else 'ещё не создана'}\n"
                f"• файл: {DIGEST_PATH}"
            )
        if cmd in ("/latest", "последние", "сводка"):
            if os.path.exists(DIGEST_PATH):
                with open(DIGEST_PATH, "r", encoding="utf-8") as fh:
                    body = fh.read().strip()
                return body or "Сводка пуста."
            return "Сводки пока нет — агент ещё не находил сделок."
        return "Неизвестная команда. /help — список."

    # --- main loop ---------------------------------------------------------
    def poll_once(self) -> None:
        resp = self._call("getUpdates", {
            "offset": self.offset,
            "timeout": 50,
        })
        for upd in resp.get("result", []):
            self.offset = upd["update_id"] + 1
            msg = upd.get("message") or upd.get("edited_message")
            if not msg:
                continue
            chat_id = str(msg.get("chat", {}).get("id", ""))
            # THE GATE: anyone who is not the owner is ignored, silently.
            if chat_id != self.owner:
                continue
            text = msg.get("text", "")
            if not text:
                continue
            try:
                self.send(self.handle(text))
            except Exception as exc:  # a bad reply must not kill the loop
                print(f"[deal-hunter-bot] reply failed: {exc}")

    def run(self) -> None:
        print("[deal-hunter-bot] started; serving owner chat "
              f"{self.owner} only. Ctrl-C to stop.")
        try:
            self.send("Deal Hunter бот на связи. /help — команды.")
        except Exception as exc:
            print(f"[deal-hunter-bot] could not send hello: {exc}")
        while True:
            try:
                self.poll_once()
            except Exception as exc:
                print(f"[deal-hunter-bot] poll error: {exc}; retrying in 5s")
                time.sleep(5)


def main() -> None:
    token = _require_env("TELEGRAM_TOKEN")
    owner = _require_env("OWNER_CHAT_ID")
    Bot(token, owner).run()


if __name__ == "__main__":
    main()
