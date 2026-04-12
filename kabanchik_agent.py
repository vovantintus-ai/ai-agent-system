"""
🐗 KABANCHIK AGENT — поиск исполнителей на Kabanchik.ua
=====================================================
Ищет 3D/аниме/анимация исполнителей на kabanchik.ua
Отправляет лучших кандидатов в Telegram
Запускать каждые несколько часов

Требует: pip install playwright requests python-dotenv
После установки: playwright install chromium
"""

import json
import time
import os
import re
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── НАСТРОЙКИ ─────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ALLOWED_USER_ID")

DATA_DIR   = Path(__file__).parent / "data"
SEEN_FILE  = DATA_DIR / "seen_kabanchik.json"

# Категории для поиска исполнителей
SEARCH_QUERIES = [
    "3D анімація",
    "аніме персонаж",
    "3D дизайн",
    "персонаж для мультфільму",
    "2D анімація",
    "character design",
    "3d animation",
    "anime character",
]

# URL поиска исполнителей на kabanchik.ua
BASE_SEARCH_URL = "https://kabanchik.ua/ua/freelance?q={query}"

# ── УТИЛИТЫ ───────────────────────────────────────────────────────────────────

def load_seen() -> set:
    DATA_DIR.mkdir(exist_ok=True)
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_seen(seen: set):
    DATA_DIR.mkdir(exist_ok=True)
    SEEN_FILE.write_text(
        json.dumps(list(seen), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def send_telegram(text: str):
    """Отправить сообщение в Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Нет Telegram токена/chat_id")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"❌ Telegram error: {r.text}")
    except Exception as e:
        print(f"❌ Telegram exception: {e}")

# ── СКРАПИНГ С PLAYWRIGHT ─────────────────────────────────────────────────────

def search_performers(query: str) -> list:
    """
    Ищет исполнителей на kabanchik.ua через Playwright (headless браузер)
    Возвращает список исполнителей: [{name, rating, reviews, price, url, description}]
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright не установлен. Запусти: pip install playwright && playwright install chromium")
        return []

    performers = []
    url = BASE_SEARCH_URL.format(query=requests.utils.quote(query))

    print(f"🔍 Ищу исполнителей: '{query}'")
    print(f"   URL: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page.goto(url, timeout=30000, wait_until="networkidle")
            time.sleep(2)

            # Ищем карточки исполнителей
            # Kabanchik использует разные классы — пробуем несколько селекторов
            selectors = [
                ".performer-card",
                ".kb-performer-card",
                "[data-testid='performer-card']",
                ".freelancer-card",
                ".kb-freelancer",
                ".search-result-item",
            ]

            cards = []
            for selector in selectors:
                cards = page.query_selector_all(selector)
                if cards:
                    print(f"   ✅ Нашёл карточки по селектору: {selector}")
                    break

            if not cards:
                # Попробуем получить весь HTML и распарсить вручную
                html = page.content()
                performers = parse_html_fallback(html, query)
                browser.close()
                return performers

            for card in cards[:10]:  # Берём первые 10
                try:
                    performer = {}

                    # Имя
                    name_el = card.query_selector("h3, .name, .performer-name, .kb-name")
                    performer["name"] = name_el.inner_text().strip() if name_el else "Неизвестно"

                    # Рейтинг
                    rating_el = card.query_selector(".rating, .kb-rating, .stars")
                    performer["rating"] = rating_el.inner_text().strip() if rating_el else "—"

                    # Количество отзывов
                    reviews_el = card.query_selector(".reviews-count, .kb-reviews, .review-count")
                    performer["reviews"] = reviews_el.inner_text().strip() if reviews_el else "0"

                    # Цена
                    price_el = card.query_selector(".price, .kb-price, .cost")
                    performer["price"] = price_el.inner_text().strip() if price_el else "—"

                    # Описание
                    desc_el = card.query_selector(".description, .kb-description, .about, p")
                    performer["description"] = desc_el.inner_text().strip()[:150] if desc_el else ""

                    # Ссылка
                    link_el = card.query_selector("a")
                    href = link_el.get_attribute("href") if link_el else ""
                    performer["url"] = f"https://kabanchik.ua{href}" if href and href.startswith("/") else href

                    performer["query"] = query
                    performer["id"] = performer["url"] or performer["name"]

                    if performer["name"] != "Неизвестно":
                        performers.append(performer)

                except Exception as e:
                    print(f"   ⚠️  Ошибка парсинга карточки: {e}")
                    continue

            browser.close()

    except Exception as e:
        print(f"❌ Playwright ошибка: {e}")

    return performers


def parse_html_fallback(html: str, query: str) -> list:
    """
    Запасной парсинг HTML если селекторы не сработали.
    Ищет ссылки на профили исполнителей.
    """
    performers = []

    # Ищем ссылки на профили вида /ua/user/... или /ua/performer/...
    pattern = r'href="(/ua/(?:user|performer|freelancer)/[^"]+)"[^>]*>([^<]+)<'
    matches = re.findall(pattern, html)

    seen_urls = set()
    for href, name in matches:
        url = f"https://kabanchik.ua{href}"
        if url not in seen_urls and len(name.strip()) > 2:
            seen_urls.add(url)
            performers.append({
                "name": name.strip(),
                "url": url,
                "rating": "—",
                "reviews": "—",
                "price": "—",
                "description": "",
                "query": query,
                "id": url
            })
            if len(performers) >= 5:
                break

    return performers


# ── ФОРМАТИРОВАНИЕ ────────────────────────────────────────────────────────────

def format_performer(p: dict) -> str:
    """Форматировать карточку исполнителя для Telegram"""
    msg = f"🎨 <b>{p['name']}</b>\n"
    if p.get("rating") and p["rating"] != "—":
        msg += f"⭐ Рейтинг: {p['rating']}\n"
    if p.get("reviews") and p["reviews"] not in ("—", "0"):
        msg += f"💬 Отзывов: {p['reviews']}\n"
    if p.get("price") and p["price"] != "—":
        msg += f"💰 Цена: {p['price']}\n"
    if p.get("description"):
        msg += f"📝 {p['description'][:100]}...\n"
    msg += f"🔑 Запрос: {p['query']}\n"
    if p.get("url"):
        msg += f"🔗 <a href='{p['url']}'>Открыть профиль</a>\n"
    return msg


# ── ГЛАВНАЯ ФУНКЦИЯ ───────────────────────────────────────────────────────────

def run_kabanchik_search():
    """Основной цикл поиска исполнителей"""
    print(f"\n{'='*50}")
    print(f"🐗 KABANCHIK AGENT — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*50}")

    seen = load_seen()
    new_performers = []

    for query in SEARCH_QUERIES:
        performers = search_performers(query)

        for p in performers:
            pid = p.get("id", "")
            if pid and pid not in seen:
                seen.add(pid)
                new_performers.append(p)

        time.sleep(2)  # Пауза между запросами

    save_seen(seen)

    if new_performers:
        print(f"\n✅ Найдено новых исполнителей: {len(new_performers)}")

        # Отправляем в Telegram по одному
        header = (
            f"🐗 <b>KABANCHIK — Новые исполнители</b>\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"👥 Найдено: {len(new_performers)}\n"
            f"{'─'*30}"
        )
        send_telegram(header)
        time.sleep(1)

        for p in new_performers[:15]:  # Максимум 15 за раз
            msg = format_performer(p)
            send_telegram(msg)
            time.sleep(0.5)

    else:
        print("ℹ️  Новых исполнителей не найдено")

    print(f"\n✅ Готово. Всего в базе: {len(seen)} исполнителей")
    return len(new_performers)


# ── ЗАПУСК ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Проверка зависимостей
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright установлен")
    except ImportError:
        print("❌ Playwright не установлен!")
        print("   Запусти в терминале:")
        print("   pip install playwright")
        print("   playwright install chromium")
        sys.exit(1)

    run_kabanchik_search()
