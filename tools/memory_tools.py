"""
Memory Tools - личная память бота
- Факты о пользователе (постоянно)
- Краткие резюме диалогов (автоматически после каждого разговора)
"""
import json
from datetime import datetime
from pathlib import Path

DATA_DIR  = Path.home() / "ai-agent" / "data"
MEM_FILE  = DATA_DIR / "memory.json"


def _load() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if MEM_FILE.exists():
        try:
            return json.loads(MEM_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEM_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class MemoryTools:

    # ── ФАКТЫ О ПОЛЬЗОВАТЕЛЕ ──────────────────────────────────────────────

    def remember(self, key: str, value: str) -> str:
        """Save a fact about the user permanently"""
        mem = _load()
        if "facts" not in mem:
            mem["facts"] = {}
        mem["facts"][key] = {
            "value": value,
            "saved": datetime.now().isoformat()
        }
        _save(mem)
        return f"✅ Remembered: {key} = {value}"

    def recall(self, key: str = None) -> str:
        """Recall facts from memory"""
        mem = _load()
        facts = mem.get("facts", {})
        if not facts:
            return "I don't have any memories yet."
        if key:
            for k, v in facts.items():
                if key.lower() in k.lower():
                    return f"🧠 {k}: {v['value']}"
            return f"Nothing found about '{key}'"
        result = "🧠 Everything I remember about you:\n\n"
        for k, v in facts.items():
            result += f"• {k}: {v['value']}\n"
        return result

    def forget(self, key: str) -> str:
        """Delete a fact from memory"""
        mem = _load()
        facts = mem.get("facts", {})
        deleted = []
        for k in list(facts.keys()):
            if key.lower() in k.lower():
                del facts[k]
                deleted.append(k)
        mem["facts"] = facts
        _save(mem)
        if deleted:
            return f"✅ Forgot: {', '.join(deleted)}"
        return f"Nothing found to forget about '{key}'"

    # ── РЕЗЮМЕ ДИАЛОГОВ ───────────────────────────────────────────────────

    def save_dialog_summary(self, summary: str):
        """Save a summary of the current dialog session"""
        if not summary or len(summary.strip()) < 10:
            return
        mem = _load()
        if "dialogs" not in mem:
            mem["dialogs"] = []
        mem["dialogs"].append({
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "summary": summary.strip()[:500]
        })
        # Keep last 200 summaries
        mem["dialogs"] = mem["dialogs"][-200:]
        _save(mem)

    def get_recent_dialogs(self, count: int = 10) -> str:
        """Get recent dialog summaries"""
        mem = _load()
        dialogs = mem.get("dialogs", [])
        if not dialogs:
            return "No dialog history yet."
        recent = dialogs[-count:]
        result = f"📚 Last {len(recent)} conversations:\n\n"
        for d in reversed(recent):
            result += f"📅 {d['date']}\n{d['summary']}\n\n"
        return result.strip()

    def search_dialogs(self, query: str) -> str:
        """Search through dialog history"""
        mem = _load()
        dialogs = mem.get("dialogs", [])
        results = [d for d in dialogs if query.lower() in d["summary"].lower()]
        if not results:
            return f"Nothing found about '{query}' in dialog history"
        result = f"🔍 Found {len(results)} conversations about '{query}':\n\n"
        for d in results[-10:]:
            result += f"📅 {d['date']}: {d['summary'][:100]}\n\n"
        return result.strip()

    def get_dialog_count(self) -> str:
        """Get total number of saved dialogs"""
        mem = _load()
        count = len(mem.get("dialogs", []))
        facts = len(mem.get("facts", {}))
        return f"🧠 Memory: {facts} facts, {count} dialog summaries"

    # ── КОНТЕКСТ ДЛЯ AI ───────────────────────────────────────────────────

    def _load_raw_dialogs(self) -> list:
        mem = _load()
        return mem.get("dialogs", [])

    def get_memory_summary(self) -> str:
        """Get full memory context to inject into AI system prompt"""
        mem = _load()
        lines = []

        # Facts about user
        facts = mem.get("facts", {})
        if facts:
            lines.append("USER PERSONAL INFO (always remember):")
            for k, v in facts.items():
                lines.append(f"- {k}: {v['value']}")

        # Recent dialog summaries
        dialogs = mem.get("dialogs", [])
        if dialogs:
            recent = dialogs[-5:]  # Last 5 conversations
            lines.append("\nRECENT CONVERSATION HISTORY:")
            for d in recent:
                lines.append(f"- [{d['date']}] {d['summary']}")

        return "\n".join(lines) if lines else ""

    def clear_memory(self) -> str:
        """Clear all memory"""
        _save({})
        return "✅ All memory cleared."

    def clear_dialogs(self) -> str:
        """Clear only dialog history"""
        mem = _load()
        mem["dialogs"] = []
        _save(mem)
        return "✅ Dialog history cleared."
