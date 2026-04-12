"""
Briefing Tools - ежедневный утренний брифинг
Каждый день в 8:00 присылает сводку
"""
import json
import asyncio
from datetime import datetime, time
from pathlib import Path
from tools.monitor_tools import MonitorTools
from tools.reminder_tools import ReminderTools

DATA_DIR = Path.home() / "ai-agent" / "data"
BRIEF_CFG = DATA_DIR / "briefing.json"


def load_cfg() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if BRIEF_CFG.exists():
        try:
            return json.loads(BRIEF_CFG.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cfg(d: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BRIEF_CFG.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


class BriefingTools:

    def __init__(self):
        self.monitors  = MonitorTools()
        self.reminders = ReminderTools()

    def set_briefing(self, hour: int = 8, city: str = "Amsterdam", enabled: bool = True) -> str:
        """Configure daily briefing time and city"""
        cfg = load_cfg()
        cfg["hour"]    = hour
        cfg["city"]    = city
        cfg["enabled"] = enabled
        cfg["last_sent"] = None
        save_cfg(cfg)
        if enabled:
            return f"✅ Daily briefing set at {hour:02d}:00 for {city}"
        return "✅ Daily briefing disabled"

    def get_briefing_status(self) -> str:
        """Get current briefing settings"""
        cfg = load_cfg()
        if not cfg.get("enabled"):
            return "❌ Daily briefing is disabled. Use /briefing to enable."
        hour = cfg.get("hour", 8)
        city = cfg.get("city", "Amsterdam")
        last = cfg.get("last_sent", "Never")
        if last and last != "Never":
            last = last[:10]
        return f"⏰ Daily briefing: {hour:02d}:00\n🌍 City: {city}\n📅 Last sent: {last}"

    async def build_briefing(self) -> str:
        """Build the morning briefing message"""
        cfg  = load_cfg()
        city = cfg.get("city", "Amsterdam")
        now  = datetime.now()

        lines = []
        lines.append(f"☀️ *Good morning! Daily briefing {now.strftime('%d.%m.%Y')}*\n")

        # Weather
        try:
            weather = await self.monitors.get_weather(city)
            lines.append(f"🌤 *Weather in {city}:*\n{weather}\n")
        except Exception:
            pass

        # Exchange rates
        try:
            usd = await self.monitors.get_exchange_rate("USD", "EUR")
            lines.append(f"💱 *Currency:*\n{usd}\n")
        except Exception:
            pass

        # Todos
        try:
            todos = self.reminders.list_todos()
            if "No tasks" not in todos:
                lines.append(f"📋 *Your tasks:*\n{todos}\n")
        except Exception:
            pass

        # Reminders today
        try:
            reminders = self.reminders.list_reminders()
            if "No active" not in reminders:
                lines.append(f"⏰ *Reminders:*\n{reminders}\n")
        except Exception:
            pass

        lines.append("Have a productive day! 🚀")
        return "\n".join(lines)

    async def check_and_send(self, bot, user_id: int):
        """Check if briefing should be sent now — call every minute"""
        cfg = load_cfg()
        if not cfg.get("enabled", False):
            return
        hour = cfg.get("hour", 8)
        now  = datetime.now()
        # Check if it's time (within the correct hour, not sent today)
        last = cfg.get("last_sent")
        if last:
            last_date = last[:10]
            today = now.strftime("%Y-%m-%d")
            if last_date == today:
                return  # Already sent today
        if now.hour == hour and now.minute < 5:
            try:
                text = await self.build_briefing()
                await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
                cfg["last_sent"] = now.isoformat()
                save_cfg(cfg)
            except Exception as e:
                print(f"Briefing error: {e}")
