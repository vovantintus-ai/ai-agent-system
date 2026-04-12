"""
Monitor Tools - мониторинг цен, погоды, новостей
"""
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / "ai-agent" / "data"
MONITORS_FILE = DATA_DIR / "monitors.json"


def _load() -> list:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if MONITORS_FILE.exists():
        try:
            return json.loads(MONITORS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(data: list):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MONITORS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class MonitorTools:

    # ── WEATHER ───────────────────────────────────────────────────────────────

    async def get_weather(self, city: str = "Amsterdam") -> str:
        """Get current weather for a city"""
        try:
            url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return f"Could not get weather for {city}"
                    data = await resp.json()
                    current = data['current_condition'][0]
                    temp_c = current['temp_C']
                    feels = current['FeelsLikeC']
                    desc = current['weatherDesc'][0]['value']
                    humidity = current['humidity']
                    wind = current['windspeedKmph']
                    return (
                        f"🌤️ Weather in {city}:\n"
                        f"🌡️ Temperature: {temp_c}°C (feels like {feels}°C)\n"
                        f"☁️ {desc}\n"
                        f"💧 Humidity: {humidity}%\n"
                        f"💨 Wind: {wind} km/h"
                    )
        except Exception as e:
            return f"Weather error: {e}"

    async def get_weather_forecast(self, city: str = "Amsterdam") -> str:
        """Get 3-day weather forecast"""
        try:
            url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    result = f"📅 3-day forecast for {city}:\n\n"
                    for day in data.get('weather', []):
                        date = day['date']
                        max_t = day['maxtempC']
                        min_t = day['mintempC']
                        desc = day['hourly'][4]['weatherDesc'][0]['value']
                        result += f"📅 {date}: {min_t}°C–{max_t}°C, {desc}\n"
                    return result
        except Exception as e:
            return f"Forecast error: {e}"

    # ── CURRENCY ──────────────────────────────────────────────────────────────

    async def get_exchange_rate(self, from_currency: str = "USD", to_currency: str = "EUR") -> str:
        """Get exchange rate"""
        try:
            url = f"https://open.er-api.com/v6/latest/{from_currency.upper()}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    rates = data.get('rates', {})
                    to = to_currency.upper()
                    if to in rates:
                        rate = rates[to]
                        return f"💱 1 {from_currency.upper()} = {rate:.4f} {to}\nUpdated: {data.get('time_last_update_utc', 'N/A')[:16]}"
                    return f"Currency not found: {to}"
        except Exception as e:
            return f"Exchange rate error: {e}"

    async def get_crypto_price(self, coin: str = "bitcoin") -> str:
        """Get cryptocurrency price"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd,eur"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    if coin.lower() in data:
                        prices = data[coin.lower()]
                        return (
                            f"₿ {coin.capitalize()}:\n"
                            f"💵 ${prices.get('usd', 'N/A'):,.2f}\n"
                            f"💶 €{prices.get('eur', 'N/A'):,.2f}"
                        )
                    return f"Coin not found: {coin}"
        except Exception as e:
            return f"Crypto error: {e}"

    # ── AUTO MONITORING ───────────────────────────────────────────────────────

    def add_monitor(self, monitor_type: str, target: str, interval_hours: int = 1) -> str:
        """Add auto-monitor (weather/crypto/currency)"""
        monitors = _load()
        monitor = {
            "id": len(monitors) + 1,
            "type": monitor_type,
            "target": target,
            "interval_hours": interval_hours,
            "active": True,
            "last_run": None,
            "created": datetime.now().isoformat()
        }
        monitors.append(monitor)
        _save(monitors)
        return f"✅ Monitor added: {monitor_type} '{target}' every {interval_hours}h"

    def list_monitors(self) -> str:
        """List active monitors"""
        monitors = _load()
        active = [m for m in monitors if m.get('active')]
        if not active:
            return "No active monitors."
        result = "🔔 Active monitors:\n"
        for m in active:
            result += f"#{m['id']} {m['type']}: {m['target']} (every {m['interval_hours']}h)\n"
        return result

    def remove_monitor(self, monitor_id: str) -> str:
        """Remove monitor"""
        monitors = _load()
        before = len(monitors)
        monitors = [m for m in monitors if str(m['id']) != str(monitor_id)]
        _save(monitors)
        return f"✅ Monitor #{monitor_id} removed" if len(monitors) < before else "Not found"

    async def run_monitors(self, bot, user_id: int):
        """Run all due monitors and send results"""
        monitors = _load()
        now = datetime.now()
        changed = False
        for m in monitors:
            if not m.get('active'):
                continue
            last = m.get('last_run')
            if last:
                from datetime import timedelta
                elapsed = (now - datetime.fromisoformat(last)).total_seconds() / 3600
                if elapsed < m['interval_hours']:
                    continue
            try:
                result = await self._run_one(m)
                if result:
                    await bot.send_message(chat_id=user_id, text=f"🔔 Monitor update:\n\n{result}")
                m['last_run'] = now.isoformat()
                changed = True
            except Exception as e:
                print(f"Monitor error: {e}")
        if changed:
            _save(monitors)

    async def _run_one(self, monitor: dict) -> str:
        t = monitor['type'].lower()
        target = monitor['target']
        if 'weather' in t:
            return await self.get_weather(target)
        elif 'crypto' in t or 'bitcoin' in t:
            return await self.get_crypto_price(target)
        elif 'currency' in t or 'exchange' in t:
            parts = target.split('/')
            return await self.get_exchange_rate(parts[0], parts[1] if len(parts) > 1 else 'EUR')
        return None
