"""Парсинг сайтов конкурентов"""
import urllib.request, re, json
from pathlib import Path
from datetime import datetime

DATA = Path.home() / "ai-agent" / "data" / "scraped.json"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def _fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"ERROR:{e}"

def _clean(html: str) -> str:
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'\s+', ' ', html)
    return html.strip()[:5000]

def _load():
    try:
        if DATA.exists(): return json.loads(DATA.read_text(encoding="utf-8"))
    except: pass
    return {"sites": {}}

def _save(d):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

class ScraperTools:
    def scrape_site(self, url: str, name: str = "") -> str:
        """Scrape a website and extract key info"""
        html = _fetch(url)
        if html.startswith("ERROR:"): return f"❌ {html}"

        # Extract title
        title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = re.sub(r'\s+',' ', title_m.group(1)).strip() if title_m else "No title"

        # Extract meta description
        desc_m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.IGNORECASE)
        description = desc_m.group(1).strip() if desc_m else ""

        # Extract all prices
        prices = list(set(re.findall(r'[\€\$\£]\s*\d+[\.,]\d{2}|\d+[\.,]\d{2}\s*[\€\$\£]', html)))[:10]

        # Extract emails
        emails = list(set(re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', html)))[:5]

        # Extract phone numbers
        phones = list(set(re.findall(r'[\+]?[\d\s\-\(\)]{10,15}', html)))[:3]

        # Extract links count
        links = len(re.findall(r'<a\s+href=', html))

        # Save result
        d = _load()
        key = name or url[:50]
        d['sites'][key] = {
            "url": url, "title": title, "description": description,
            "prices": prices, "emails": emails,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text_preview": _clean(html)[:500]
        }
        _save(d)

        lines = [f"🔍 **Scraped: {title}**\n",
                 f"🔗 {url}"]
        if description: lines.append(f"📝 {description[:200]}")
        if prices: lines.append(f"💰 Prices found: {', '.join(prices[:5])}")
        if emails: lines.append(f"📧 Emails: {', '.join(emails)}")
        if phones: lines.append(f"📞 Phones: {', '.join(p.strip() for p in phones[:2])}")
        lines.append(f"🔗 Links on page: {links}")
        lines.append(f"\n📄 **Content preview:**\n{_clean(html)[:400]}...")
        return "\n".join(lines)

    def compare_competitors(self, urls: list) -> str:
        """Scrape multiple competitor sites and compare"""
        results = []
        for url in urls[:5]:
            html = _fetch(url)
            if html.startswith("ERROR:"): 
                results.append({"url": url, "error": html}); continue
            title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
            title = title_m.group(1).strip() if title_m else url
            prices = re.findall(r'[\€\$\£]\s*\d+[\.,]\d{2}', html)[:3]
            emails = re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', html)[:2]
            results.append({"url": url, "title": title, "prices": prices, "emails": emails})

        lines = [f"📊 **Competitor Analysis ({len(results)} sites)**\n"]
        for r in results:
            if 'error' in r:
                lines.append(f"❌ {r['url']}: {r['error']}")
            else:
                lines.append(f"**{r['title'][:50]}**")
                lines.append(f"  🔗 {r['url']}")
                if r['prices']: lines.append(f"  💰 {', '.join(r['prices'][:3])}")
                if r['emails']: lines.append(f"  📧 {', '.join(r['emails'][:2])}")
            lines.append("")
        return "\n".join(lines)

    def monitor_changes(self, url: str, name: str) -> str:
        """Check if site content changed since last scrape"""
        d = _load()
        html = _fetch(url)
        if html.startswith("ERROR:"): return f"❌ {html}"
        text = _clean(html)[:1000]
        key = name or url[:50]
        if key in d['sites']:
            old_text = d['sites'][key].get('text_preview','')
            if old_text and old_text[:200] != text[:200]:
                d['sites'][key]['text_preview'] = text
                d['sites'][key]['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                _save(d)
                return f"🔔 **CHANGES DETECTED on {name or url}!**\nSite content has changed since last check."
            d['sites'][key]['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _save(d)
            return f"✅ No changes on {name or url}"
        # First time
        d['sites'][key] = {"url":url,"text_preview":text,"scraped_at":datetime.now().strftime("%Y-%m-%d %H:%M")}
        _save(d)
        return f"✅ Now monitoring: {name or url}"

    def saved_sites(self) -> str:
        d = _load()
        if not d['sites']: return "📭 No scraped sites saved."
        lines = [f"🗃️ **Saved sites ({len(d['sites'])}):**\n"]
        for key, site in d['sites'].items():
            lines.append(f"• **{key}**")
            lines.append(f"  🔗 {site.get('url','')}")
            lines.append(f"  ⏰ {site.get('scraped_at','')}")
        return "\n".join(lines)
