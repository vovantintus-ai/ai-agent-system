"""
Reminder & Notes Tools - напоминания, заметки, задачи
"""
import json
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / "ai-agent" / "data"
NOTES_FILE = DATA_DIR / "notes.json"
TODOS_FILE = DATA_DIR / "todos.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"


def _load(path: Path) -> list:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class ReminderTools:

    def __init__(self, bot=None):
        self.bot = bot  # Telegram bot instance for sending reminders
        self._reminder_task = None

    # ── NOTES ─────────────────────────────────────────────────────────────────

    def add_note(self, title: str, content: str) -> str:
        """Add a note"""
        notes = _load(NOTES_FILE)
        note = {
            "id": len(notes) + 1,
            "title": title,
            "content": content,
            "created": datetime.now().isoformat()
        }
        notes.append(note)
        _save(NOTES_FILE, notes)
        return f"✅ Note saved: '{title}'"

    def list_notes(self) -> str:
        """List all notes"""
        notes = _load(NOTES_FILE)
        if not notes:
            return "No notes yet."
        result = "📝 Notes:\n"
        for n in notes[-20:]:
            result += f"\n#{n['id']} {n['title']}\n   {n['content'][:80]}\n"
        return result

    def get_note(self, title_or_id: str) -> str:
        """Get a specific note"""
        notes = _load(NOTES_FILE)
        for n in notes:
            if str(n['id']) == str(title_or_id) or title_or_id.lower() in n['title'].lower():
                return f"📝 {n['title']}\n\n{n['content']}\n\nCreated: {n['created'][:10]}"
        return f"Note not found: {title_or_id}"

    def delete_note(self, title_or_id: str) -> str:
        """Delete a note"""
        notes = _load(NOTES_FILE)
        before = len(notes)
        notes = [n for n in notes if str(n['id']) != str(title_or_id)
                 and title_or_id.lower() not in n['title'].lower()]
        _save(NOTES_FILE, notes)
        return f"✅ Deleted {before - len(notes)} note(s)"

    # ── TO-DO ─────────────────────────────────────────────────────────────────

    def add_todo(self, task: str, priority: str = "normal") -> str:
        """Add a task to To-Do list"""
        todos = _load(TODOS_FILE)
        todo = {
            "id": len(todos) + 1,
            "task": task,
            "priority": priority,
            "done": False,
            "created": datetime.now().isoformat()
        }
        todos.append(todo)
        _save(TODOS_FILE, todos)
        return f"✅ Task added: '{task}'"

    def list_todos(self, show_done: bool = False) -> str:
        """List To-Do tasks"""
        todos = _load(TODOS_FILE)
        if not todos:
            return "No tasks yet."
        icons = {"high": "🔴", "normal": "🟡", "low": "🟢"}
        result = "📋 Tasks:\n"
        for t in todos:
            if t['done'] and not show_done:
                continue
            status = "✅" if t['done'] else icons.get(t['priority'], "⬜")
            result += f"{status} #{t['id']} {t['task']}\n"
        return result or "All tasks done! ✅"

    def complete_todo(self, task_id: str) -> str:
        """Mark task as done"""
        todos = _load(TODOS_FILE)
        for t in todos:
            if str(t['id']) == str(task_id):
                t['done'] = True
                t['completed'] = datetime.now().isoformat()
                _save(TODOS_FILE, todos)
                return f"✅ Task #{task_id} done: '{t['task']}'"
        return f"Task #{task_id} not found"

    def delete_todo(self, task_id: str) -> str:
        """Delete a task"""
        todos = _load(TODOS_FILE)
        before = len(todos)
        todos = [t for t in todos if str(t['id']) != str(task_id)]
        _save(TODOS_FILE, todos)
        return f"✅ Task #{task_id} deleted" if len(todos) < before else "Task not found"

    # ── REMINDERS ─────────────────────────────────────────────────────────────

    def add_reminder(self, text: str, when: str, user_id: str = "") -> str:
        """Add reminder. when: '10min', '2h', '2026-03-01 15:00'"""
        reminders = _load(REMINDERS_FILE)
        remind_at = self._parse_time(when)
        if not remind_at:
            return f"Could not parse time: '{when}'. Use: '10min', '2h', '30min', or '2026-03-01 15:00'"
        reminder = {
            "id": len(reminders) + 1,
            "text": text,
            "remind_at": remind_at.isoformat(),
            "user_id": user_id,
            "sent": False,
            "created": datetime.now().isoformat()
        }
        reminders.append(reminder)
        _save(REMINDERS_FILE, reminders)
        return f"⏰ Reminder set: '{text}' at {remind_at.strftime('%H:%M %d.%m.%Y')}"

    def list_reminders(self) -> str:
        """List active reminders"""
        reminders = _load(REMINDERS_FILE)
        active = [r for r in reminders if not r['sent']]
        if not active:
            return "No active reminders."
        result = "⏰ Reminders:\n"
        for r in active:
            dt = datetime.fromisoformat(r['remind_at'])
            result += f"#{r['id']} {dt.strftime('%H:%M %d.%m')} — {r['text']}\n"
        return result

    def delete_reminder(self, reminder_id: str) -> str:
        """Delete reminder"""
        reminders = _load(REMINDERS_FILE)
        before = len(reminders)
        reminders = [r for r in reminders if str(r['id']) != str(reminder_id)]
        _save(REMINDERS_FILE, reminders)
        return f"✅ Reminder #{reminder_id} deleted" if len(reminders) < before else "Not found"

    def _parse_time(self, when: str) -> datetime:
        """Parse time expression"""
        when = when.strip().lower()
        now = datetime.now()
        try:
            if 'min' in when:
                mins = int(''.join(filter(str.isdigit, when)))
                return now + timedelta(minutes=mins)
            elif when.endswith('h') or 'hour' in when:
                hours = int(''.join(filter(str.isdigit, when)))
                return now + timedelta(hours=hours)
            elif 'day' in when or 'завтра' in when:
                return now + timedelta(days=1)
            else:
                for fmt in ['%Y-%m-%d %H:%M', '%d.%m.%Y %H:%M', '%H:%M']:
                    try:
                        dt = datetime.strptime(when, fmt)
                        if fmt == '%H:%M':
                            dt = dt.replace(year=now.year, month=now.month, day=now.day)
                            if dt < now:
                                dt += timedelta(days=1)
                        return dt
                    except ValueError:
                        continue
        except Exception:
            pass
        return None

    async def check_reminders(self, bot, user_id: int):
        """Check and send due reminders — call this in background"""
        reminders = _load(REMINDERS_FILE)
        now = datetime.now()
        changed = False
        for r in reminders:
            if r['sent']:
                continue
            remind_at = datetime.fromisoformat(r['remind_at'])
            if now >= remind_at:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"⏰ *Reminder!*\n\n{r['text']}",
                        parse_mode='Markdown'
                    )
                    r['sent'] = True
                    changed = True
                except Exception as e:
                    print(f"Reminder send error: {e}")
        if changed:
            _save(REMINDERS_FILE, reminders)
