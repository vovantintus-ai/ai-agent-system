"""
🔍 Market Monitor — Агент мониторинга заказов
Платформы: Upwork (RSS), Reddit, FreelanceHunt
Отправляет новые заказы в Telegram
"""

import asyncio
import aiohttp
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(encoding="utf-8-sig")

# ── Конфиг ────────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT   = os.getenv("ALLOWED_USER_ID", "").strip()
CHECK_INTERVAL  = 30 * 60  # каждые 30 минут

DATA_DIR  = Path.home() / "ai-agent" / "data"
SEEN_FILE = DATA_DIR / "seen_jobs.json"

# Ключевые слова для поиска
KEYWORDS = [
    "anime character",
    "3d animation",
    "cartoon character",
    "character design",
    "blender 3d",
    "2d animation",
    "anime art",
    "character illustration",
]

# ── Хранилище просмотренных ───────────────────────────────────────────────────

def load_seen() -> set:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_seen(seen: set):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Храним только последние 1000
    lst = list(seen)[-1000:]
    SEEN_FILE.write_text(json.dumps(lst, ensure_ascii=False), encoding="utf-8")

# ── Telegram ──────────────────────────────────────────────────────────────────

async def send_telegram(text: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print(f"[Telegram] {text[:100]}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    print(f"[Telegram error] {resp.status}")
        except Exception as e:
            print(f"[Telegram error] {e}")

# ── UPWORK RSS ────────────────────────────────────────────────────────────────

async def fetch_upwork(keyword: str, session: aiohttp.ClientSession) -> list:
    """Upwork RSS — работает без авторизации"""
    jobs = []
    try:
        query = keyword.replace(" ", "+")
        url = f"https://www.upwork.com/ab/feed/jobs/rss?q={query}&sort=recency&paging=0%3B10"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; RSS Reader)"}
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()

        root = ET.fromstring(text)
        channel = root.find("channel")
        if channel is None:
            return []

        for item in channel.findall("item"):
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            desc  = item.findtext("description", "").strip()
            pub   = item.findtext("pubDate", "").strip()

            # Очистить HTML из описания
            desc_clean = re.sub(r'<[^>]+>', '', desc)[:300]

            # Бюджет из описания
            budget = "Не указан"
            budget_match = re.search(r'\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?', desc_clean)
            if budget_match:
                budget = budget_match.group()

            jobs.append({
                "id": f"upwork_{link}",
                "platform": "Upwork",
                "title": title,
                "url": link,
                "budget": budget,
                "description": desc_clean,
                "date": pub,
                "keyword": keyword
            })
    except Exception as e:
        print(f"[Upwork] Ошибка для '{keyword}': {e}")
    return jobs

# ── REDDIT ────────────────────────────────────────────────────────────────────

async def fetch_reddit(subreddit: str, session: aiohttp.ClientSession) -> list:
    """Reddit API — открытый, без авторизации"""
    jobs = []
    try:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
        headers = {"User-Agent": "Mozilla/5.0 MarketMonitor/1.0"}
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()

        posts = data.get("data", {}).get("children", [])
        for post in posts:
            p = post.get("data", {})
            title   = p.get("title", "")
            url_p   = f"https://reddit.com{p.get('permalink', '')}"
            text    = p.get("selftext", "")[:300]
            post_id = p.get("id", "")
            flair   = p.get("link_flair_text", "")

            # Фильтр по ключевым словам
            title_lower = title.lower()
            text_lower  = text.lower()
            relevant = any(
                kw in title_lower or kw in text_lower
                for kw in ["anime", "3d", "character", "animation", "blender", "art", "illustration"]
            )
            if not relevant:
                continue

            # Бюджет
            budget = "Не указан"
            budget_match = re.search(r'\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?', title + " " + text)
            if budget_match:
                budget = budget_match.group()

            jobs.append({
                "id": f"reddit_{post_id}",
                "platform": f"Reddit r/{subreddit}",
                "title": title,
                "url": url_p,
                "budget": budget,
                "description": text,
                "date": datetime.fromtimestamp(p.get("created_utc", 0)).strftime("%d.%m.%Y %H:%M"),
                "keyword": flair or subreddit
            })
    except Exception as e:
        print(f"[Reddit r/{subreddit}] Ошибка: {e}")
    return jobs

# ── ФОРМАТИРОВАНИЕ ────────────────────────────────────────────────────────────

def format_job(job: dict) -> str:
    platform = job["platform"]
    emoji = {
        "Upwork": "💼",
        "Reddit r/artcommissions": "🎨",
        "Reddit r/HungryArtists": "🖌️",
        "Reddit r/starvingartists": "🖼️",
    }.get(platform, "📋")

    title = job["title"][:60]
    budget = job["budget"]
    desc = job["description"][:200] + ("..." if len(job["description"]) > 200 else "")
    url = job["url"]
    keyword = job.get("keyword", "")

    return (
        f"{emoji} *{platform}*\n"
        f"📌 *{title}*\n"
        f"💰 Бюджет: `{budget}`\n"
        f"🔑 Ключевое слово: `{keyword}`\n"
        f"📝 {desc}\n"
        f"🔗 [Открыть заказ]({url})"
    )

# ── ОСНОВНОЙ ЦИКЛ ─────────────────────────────────────────────────────────────

async def check_markets():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Проверяю рынок...")

    seen = load_seen()
    new_jobs = []

    async with aiohttp.ClientSession() as session:

        # Upwork — все ключевые слова
        for keyword in KEYWORDS:
            jobs = await fetch_upwork(keyword, session)
            for job in jobs:
                if job["id"] not in seen:
                    new_jobs.append(job)
                    seen.add(job["id"])
            await asyncio.sleep(1)  # пауза между запросами

        # Reddit
        for sub in ["artcommissions", "HungryArtists", "starvingartists"]:
            jobs = await fetch_reddit(sub, session)
            for job in jobs:
                if job["id"] not in seen:
                    new_jobs.append(job)
                    seen.add(job["id"])
            await asyncio.sleep(1)

    save_seen(seen)

    if new_jobs:
        print(f"✅ Найдено новых заказов: {len(new_jobs)}")

        # Отправляем заголовок
        await send_telegram(
            f"🔍 *Новые заказы! ({datetime.now().strftime('%d.%m.%Y %H:%M')})*\n"
            f"Найдено: *{len(new_jobs)}* новых заказов"
        )

        # Отправляем каждый заказ
        for job in new_jobs[:10]:  # максимум 10 за раз
            await send_telegram(format_job(job))
            await asyncio.sleep(0.5)

        if len(new_jobs) > 10:
            await send_telegram(f"📊 И ещё *{len(new_jobs) - 10}* заказов. Следующая проверка через 30 минут.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️ Новых заказов нет")

async def main():
    print("🚀 Market Monitor запущен!")
    print(f"⏱️  Интервал проверки: каждые {CHECK_INTERVAL // 60} минут")
    print(f"🔑 Ключевые слова: {', '.join(KEYWORDS)}")
    print(f"📱 Telegram chat: {TELEGRAM_CHAT}")
    print("-" * 50)

    # Первая проверка сразу
    await check_markets()

    # Затем по расписанию
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        await check_markets()

if __name__ == "__main__":
    asyncio.run(main())
