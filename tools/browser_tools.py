"""
Browser Tools - web search and page fetching
"""

import aiohttp
import json
import os
from urllib.parse import quote_plus
import re


class BrowserTools:
    async def search(self, query: str) -> str:
        """Search the web using DuckDuckGo"""
        try:
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json(content_type=None)

            results = []

            # Abstract (main answer)
            if data.get("AbstractText"):
                results.append(f"📌 {data['AbstractText']}")
                if data.get("AbstractURL"):
                    results.append(f"Источник: {data['AbstractURL']}")

            # Related topics
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"• {topic['Text'][:200]}")

            if not results:
                return f"По запросу '{query}' ничего не найдено через DuckDuckGo. Попробуй fetch_url с конкретным сайтом."

            return f"🔍 Результаты поиска: '{query}'\n\n" + "\n\n".join(results)

        except Exception as e:
            return f"❌ Ошибка поиска: {str(e)}"

    async def fetch_url(self, url: str) -> str:
        """Fetch and parse a web page"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; AIAgent/1.0)"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    content_type = resp.content_type
                    if 'text' not in content_type and 'json' not in content_type:
                        return f"Неподдерживаемый тип контента: {content_type}"
                    text = await resp.text(errors='replace')

            # Strip HTML tags
            clean = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
            clean = re.sub(r'<[^>]+>', '', clean)
            clean = re.sub(r'\n{3,}', '\n\n', clean)
            clean = re.sub(r'  +', ' ', clean)
            clean = clean.strip()

            # Limit output
            if len(clean) > 3000:
                clean = clean[:3000] + "\n...[текст обрезан]"

            return f"🌐 Содержимое {url}:\n\n{clean}"

        except Exception as e:
            return f"❌ Ошибка загрузки {url}: {str(e)}"
