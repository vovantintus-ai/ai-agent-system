"""
Learning Tools - система обучения бота
Анализирует прошлые разговоры и адаптируется
"""
import json
from datetime import datetime
from pathlib import Path

DATA_DIR    = Path.home() / "ai-agent" / "data"
FEEDBACK_F  = DATA_DIR / "feedback.json"
KNOWLEDGE_F = DATA_DIR / "knowledge.json"
STYLE_F     = DATA_DIR / "style.json"


def _load(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class LearningTools:

    def rate_good(self, comment: str = "") -> str:
        """User liked the answer"""
        fb = _load(FEEDBACK_F)
        if "good" not in fb:
            fb["good"] = []
        fb["good"].append({"time": datetime.now().isoformat(), "comment": comment})
        fb["good"] = fb["good"][-100:]
        _save(FEEDBACK_F, fb)
        self._update_style("good", comment)
        return "✅ Отлично! Запомнил что тебе понравилось."

    def rate_bad(self, comment: str = "") -> str:
        """User disliked the answer"""
        fb = _load(FEEDBACK_F)
        if "bad" not in fb:
            fb["bad"] = []
        fb["bad"].append({"time": datetime.now().isoformat(), "comment": comment})
        fb["bad"] = fb["bad"][-100:]
        _save(FEEDBACK_F, fb)
        self._update_style("bad", comment)
        return "✅ Понял! Постараюсь ответить лучше в следующий раз."

    def get_feedback_stats(self) -> str:
        """Show feedback statistics"""
        fb    = _load(FEEDBACK_F)
        good  = len(fb.get("good", []))
        bad   = len(fb.get("bad", []))
        total = good + bad
        if total == 0:
            return "Пока нет оценок. Оценивай мои ответы командами /good или /bad!"
        pct = int(good / total * 100)
        return f"📊 Моя статистика:\n👍 Хорошо: {good}\n👎 Плохо: {bad}\n⭐ Рейтинг: {pct}%"

    def add_knowledge(self, topic: str, content: str) -> str:
        """Add to knowledge base"""
        kb = _load(KNOWLEDGE_F)
        if "items" not in kb:
            kb["items"] = {}
        kb["items"][topic] = {
            "content": content,
            "added": datetime.now().isoformat()
        }
        _save(KNOWLEDGE_F, kb)
        return f"✅ Добавлено в базу знаний: '{topic}'"

    def get_knowledge(self, topic: str = None) -> str:
        """Get from knowledge base"""
        kb    = _load(KNOWLEDGE_F)
        items = kb.get("items", {})
        if not items:
            return "База знаний пуста. Добавь информацию командой /learn тема: содержание"
        if topic:
            for k, v in items.items():
                if topic.lower() in k.lower():
                    return f"📚 {k}:\n{v['content']}"
            return f"Ничего не найдено о '{topic}'"
        result = "📚 База знаний:\n\n"
        for k, v in items.items():
            result += f"• {k}: {v['content'][:80]}\n"
        return result

    def remove_knowledge(self, topic: str) -> str:
        """Remove from knowledge base"""
        kb    = _load(KNOWLEDGE_F)
        items = kb.get("items", {})
        deleted = []
        for k in list(items.keys()):
            if topic.lower() in k.lower():
                del items[k]
                deleted.append(k)
        kb["items"] = items
        _save(KNOWLEDGE_F, kb)
        if deleted:
            return f"✅ Удалено: {', '.join(deleted)}"
        return f"Не найдено: '{topic}'"

    def _update_style(self, rating: str, comment: str):
        """Update style based on feedback"""
        style = _load(STYLE_F)
        if "preferences" not in style:
            style["preferences"] = {
                "length": "medium",
                "tone": "friendly",
                "detail": "normal",
                "good_count": 0,
                "bad_count": 0
            }
        prefs = style["preferences"]
        if rating == "good":
            prefs["good_count"] = prefs.get("good_count", 0) + 1
        else:
            prefs["bad_count"] = prefs.get("bad_count", 0) + 1

        c = comment.lower()
        if any(w in c for w in ["коротко", "кратко", "short", "brief"]):
            prefs["length"] = "short"
        if any(w in c for w in ["подробно", "детально", "detailed", "more"]):
            prefs["length"] = "detailed"
        if any(w in c for w in ["просто", "понятно", "simple", "easy"]):
            prefs["detail"] = "simple"
        if any(w in c for w in ["профессионально", "formal", "official"]):
            prefs["tone"] = "professional"

        style["preferences"] = prefs
        _save(STYLE_F, style)

    def get_style_context(self) -> str:
        """Get AI context based on learned preferences + knowledge base"""
        style = _load(STYLE_F)
        prefs = style.get("preferences", {})
        kb    = _load(KNOWLEDGE_F)
        items = kb.get("items", {})
        lines = []

        good = prefs.get("good_count", 0)
        bad  = prefs.get("bad_count", 0)

        if good > 0 or bad > 0:
            lines.append("LEARNED USER PREFERENCES:")
            length = prefs.get("length", "medium")
            tone   = prefs.get("tone", "friendly")
            detail = prefs.get("detail", "normal")
            if length == "short":
                lines.append("- Give SHORT concise answers")
            elif length == "detailed":
                lines.append("- Give DETAILED thorough answers")
            if tone == "professional":
                lines.append("- Use PROFESSIONAL formal tone")
            else:
                lines.append("- Use FRIENDLY casual tone")
            if detail == "simple":
                lines.append("- Use SIMPLE language, avoid technical terms")

        if items:
            lines.append("\nKNOWLEDGE BASE (use when relevant):")
            for k, v in list(items.items())[:10]:
                lines.append(f"- {k}: {v['content'][:150]}")

        return "\n".join(lines) if lines else ""

    def analyze_from_history(self) -> str:
        """Analyze dialog history and extract learning insights"""
        from tools.memory_tools import MemoryTools
        mem     = MemoryTools()
        dialogs = mem._load_raw_dialogs()
        if not dialogs:
            return "Нет истории разговоров для анализа."

        total  = len(dialogs)
        topics = []
        for d in dialogs[-50:]:
            summary = d.get("summary", "")
            if summary:
                topics.append(summary[:100])

        return (
            f"🎓 Анализ {total} разговоров:\n\n"
            f"Последние темы:\n" +
            "\n".join(f"• {t}" for t in topics[-5:])
        )

    def get_learning_summary(self) -> str:
        """Full learning status"""
        fb    = _load(FEEDBACK_F)
        kb    = _load(KNOWLEDGE_F)
        style = _load(STYLE_F)
        good  = len(fb.get("good", []))
        bad   = len(fb.get("bad", []))
        items = len(kb.get("items", {}))
        prefs = style.get("preferences", {})
        return (
            f"🎓 Статус обучения:\n\n"
            f"📊 Оценки: {good} 👍 / {bad} 👎\n"
            f"📚 База знаний: {items} тем\n"
            f"🎨 Длина ответов: {prefs.get('length','medium')}\n"
            f"💬 Тон: {prefs.get('tone','friendly')}\n"
            f"🔍 Детализация: {prefs.get('detail','normal')}"
        )
