"""
Price Monitor - отслеживает цены на сайтах и уведомляет об изменениях
"""
import json, re, time, threading
from pathlib import Path
from datetime import datetime

DATA_FILE = Path.home() / "ai-agent" / "data" / "price_monitors.json"

def _load():
    try:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception: pass
    return {}

def _save(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _extract_price(html: str) -> float | None:
    """Extract price from HTML — looks for common price patterns"""
    patterns = [
        r'[\€\$\£\₽]\s*(\d+[\.,]\d{2})',
        r'(\d+[\.,]\d{2})\s*[\€\$\£\₽]',
        r'"price"[:\s"]+(\d+[\.,]\d*)',
        r'price["\s:]+(\d+[\.,]\d*)',
        r'(\d{1,6}[.,]\d{2})',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(',', '.'))
            except: pass
    return None

def _fetch_price(url: str) -> tuple[float | None, str]:
    """Fetch page and extract price"""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
        price = _extract_price(html)
        return price, html[:200]
    except Exception as e:
        return None, str(e)


class PriceMonitor:

    def add_monitor(self, name: str, url: str, target_price: float = None) -> str:
        """Add price monitor for a URL"""
        data = _load()
        price, _ = _fetch_price(url)
        if price is None:
            return f"❌ Could not extract price from {url}\nTry a direct product page URL."
        
        data[name] = {
            "url": url,
            "initial_price": price,
            "current_price": price,
            "target_price": target_price,
            "added": datetime.now().isoformat(),
            "last_check": datetime.now().isoformat(),
            "history": [{"price": price, "time": datetime.now().isoformat()}]
        }
        _save(data)
        msg = f"✅ Monitoring: **{name}**\n💰 Current price: €{price:.2f}"
        if target_price:
            msg += f"\n🎯 Alert when below: €{target_price:.2f}"
        return msg

    def check_price(self, name: str) -> str:
        """Check current price for a monitor"""
        data = _load()
        if name not in data:
            return f"❌ Monitor '{name}' not found. Use /prices to see all monitors."
        
        item = data[name]
        price, _ = _fetch_price(item["url"])
        if price is None:
            return f"❌ Could not fetch price for {name}"
        
        old = item["current_price"]
        diff = price - old
        diff_pct = (diff / old * 100) if old else 0
        
        item["current_price"] = price
        item["last_check"] = datetime.now().isoformat()
        item["history"].append({"price": price, "time": datetime.now().isoformat()})
        item["history"] = item["history"][-50:]  # keep last 50
        _save(data)
        
        arrow = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
        msg = f"{arrow} **{name}**\n"
        msg += f"💰 Price: €{price:.2f}"
        if diff != 0:
            msg += f" ({'+' if diff>0 else ''}{diff:.2f}, {diff_pct:+.1f}%)"
        msg += f"\n📌 Initial: €{item['initial_price']:.2f}"
        
        if item.get("target_price") and price <= item["target_price"]:
            msg += f"\n🔔 **TARGET REACHED!** Target was €{item['target_price']:.2f}"
        
        return msg

    def check_all(self) -> str:
        """Check all monitors"""
        data = _load()
        if not data:
            return "📭 No price monitors set up.\nUse: /addprice <name> <url> [target_price]"
        
        results = []
        alerts = []
        for name in data:
            result = self.check_price(name)
            results.append(result)
            if "TARGET REACHED" in result:
                alerts.append(name)
        
        out = "\n\n".join(results)
        if alerts:
            out += f"\n\n🔔 ALERTS: {', '.join(alerts)}"
        return out

    def list_monitors(self) -> str:
        """List all active monitors"""
        data = _load()
        if not data:
            return "📭 No price monitors.\nAdd one: /addprice <name> <url>"
        
        lines = ["📊 **Price Monitors:**\n"]
        for name, item in data.items():
            lines.append(f"• **{name}**")
            lines.append(f"  💰 €{item['current_price']:.2f} (initial: €{item['initial_price']:.2f})")
            lines.append(f"  🔗 {item['url'][:60]}...")
            if item.get("target_price"):
                lines.append(f"  🎯 Target: €{item['target_price']:.2f}")
            lines.append(f"  ⏰ Last check: {item['last_check'][:16]}")
            lines.append("")
        return "\n".join(lines)

    def remove_monitor(self, name: str) -> str:
        """Remove a price monitor"""
        data = _load()
        if name in data:
            del data[name]
            _save(data)
            return f"✅ Removed monitor: {name}"
        return f"❌ Monitor '{name}' not found"

    def price_history(self, name: str) -> str:
        """Show price history"""
        data = _load()
        if name not in data:
            return f"❌ Monitor '{name}' not found"
        
        history = data[name]["history"][-10:]
        lines = [f"📈 **Price history: {name}**\n"]
        for entry in reversed(history):
            lines.append(f"  {entry['time'][:16]}  €{entry['price']:.2f}")
        return "\n".join(lines)
