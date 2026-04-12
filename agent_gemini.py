import os
os.environ["PYTHONUTF8"] = "1"
"""
Agent - Google Gemini
"""

import os
from datetime import datetime
from tools.file_tools import FileTools
from tools.shell_tools import ShellTools
from tools.browser_tools import BrowserTools
from tools.email_tools import EmailTools

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
BOT_PERSONA  = os.getenv("BOT_PERSONA", "")

SYSTEM = f"""You are an autonomous AI agent. Execute user tasks using available tools.

LANGUAGE: Russian → reply Russian. Ukrainian → reply Ukrainian. English → reply English.
LOCATION: User is in Netherlands (CET, euros €, DD.MM.YYYY).
Always describe what you are doing before each action.
{('PERSONALITY: ' + BOT_PERSONA) if BOT_PERSONA else ''}"""


class Agent:
    def __init__(self):
        self.files   = FileTools()
        self.shell   = ShellTools()
        self.browser = BrowserTools()
        self.email   = EmailTools()
        self.history = []

        import google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            raise ValueError("GEMINI_API_KEY not set in .env")

        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM,
            tools=[
                self._read_file, self._write_file, self._list_directory,
                self._delete_file, self._move_file, self._run_command,
                self._run_python, self._web_search, self._fetch_url,
                self._send_email, self._create_calendar_event,
            ],
        )
        self._new_chat()

    def _new_chat(self):
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

    # ── Tools ─────────────────────────────────────────────────────────────────

    def _read_file(self, path: str) -> str:
        """Read contents of a file. Args: path - file path."""
        return self.files.read_file(path)

    def _write_file(self, path: str, content: str) -> str:
        """Create or overwrite a file. Args: path - file path, content - text to write."""
        return self.files.write_file(path, content)

    def _list_directory(self, path: str = ".") -> str:
        """List files in a directory. Args: path - directory (default: current)."""
        return self.files.list_directory(path)

    def _delete_file(self, path: str) -> str:
        """Delete a file. Args: path - file path."""
        return self.files.delete_file(path)

    def _move_file(self, source: str, destination: str) -> str:
        """Move or rename a file. Args: source - current path, destination - new path."""
        return self.files.move_file(source, destination)

    def _run_command(self, command: str, working_dir: str = "") -> str:
        """Run a PowerShell command. Args: command - the command, working_dir - optional directory."""
        return self.shell.run_command(command, working_dir or None)

    def _run_python(self, code: str) -> str:
        """Execute Python code. Args: code - Python code."""
        return self.shell.run_python(code)

    def _web_search(self, query: str) -> str:
        """Search the internet. Args: query - search query."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.browser.search(query))
        finally:
            loop.close()

    def _fetch_url(self, url: str) -> str:
        """Fetch a web page. Args: url - full URL."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.browser.fetch_url(url))
        finally:
            loop.close()

    def _send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email. Args: to - recipient, subject - subject line, body - message text."""
        return self.email.send_email(to, subject, body)

    def _create_calendar_event(self, title: str, start: str, end: str, description: str = "") -> str:
        """Create a calendar event (.ics). Args: title - name, start - ISO datetime, end - ISO datetime."""
        return self.email.create_calendar_event(title, start, end, description)

    # ── Run ───────────────────────────────────────────────────────────────────

    async def run(self, task: str) -> str:
        self.history.append({"task": task, "timestamp": datetime.now().isoformat()})
        try:
            response = self.chat.send_message(task)
            return response.text or "Done."
        except Exception as e:
            return f"Error: {e}"

    def get_history(self):
        return self.history

    def clear_context(self):
        self._new_chat()
