"""
Agent - Ollama (Local AI, FREE)
"""

import os
import json
import aiohttp
from datetime import datetime
from tools.file_tools import FileTools
from tools.shell_tools import ShellTools
from tools.browser_tools import BrowserTools
from tools.email_tools import EmailTools

OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
BOT_PERSONA  = os.getenv("BOT_PERSONA", "")

SYSTEM = f"""You are an autonomous AI agent. Execute user tasks using available tools.

LANGUAGE: Russian → reply Russian. Ukrainian → reply Ukrainian. English → reply English.
LOCATION: User is in Netherlands (CET, euros €, DD.MM.YYYY).
Always describe what you are doing before each action.
{('PERSONALITY: ' + BOT_PERSONA) if BOT_PERSONA else ''}

You have access to these tools. To use a tool, respond ONLY with JSON in this exact format:
{{"tool": "tool_name", "args": {{"arg1": "value1"}}}}

Available tools:
- read_file(path) - read file contents
- write_file(path, content) - create or overwrite file
- list_directory(path) - list files in directory
- delete_file(path) - delete a file
- move_file(source, destination) - move/rename file
- run_command(command) - run PowerShell command
- run_python(code) - execute Python code
- web_search(query) - search the internet
- fetch_url(url) - fetch web page
- send_email(to, subject, body) - send email
- create_calendar_event(title, start, end) - create calendar event

If no tool is needed, just reply normally in plain text."""


class Agent:
    def __init__(self):
        self.files   = FileTools()
        self.shell   = ShellTools()
        self.browser = BrowserTools()
        self.email   = EmailTools()
        self.history = []
        self.messages = []
        self._check_ollama()

    def _check_ollama(self):
        import urllib.request
        try:
            urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
        except Exception:
            raise ConnectionError(
                f"Ollama not running! Start Ollama app first.\n"
                f"Expected at: {OLLAMA_URL}"
            )

    async def run(self, task: str) -> str:
        self.history.append({"task": task, "timestamp": datetime.now().isoformat()})
        self.messages.append({"role": "user", "content": task})

        for _ in range(8):
            reply = await self._chat()
            if not reply:
                return "No response from Ollama."

            # Check if reply is a tool call (JSON)
            tool_result = self._try_tool(reply)
            if tool_result is not None:
                self.messages.append({"role": "assistant", "content": reply})
                self.messages.append({
                    "role": "user",
                    "content": f"Tool result: {tool_result}\n\nContinue or give final answer."
                })
            else:
                # Plain text answer
                self.messages.append({"role": "assistant", "content": reply})
                return reply

        return reply or "Done."

    async def _chat(self) -> str:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "system", "content": SYSTEM}] + self.messages,
            "stream": False
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Ollama error {resp.status}: {text}")
                data = await resp.json()
                return data.get("message", {}).get("content", "")

    def _try_tool(self, text: str):
        """Try to parse tool call from model response"""
        text = text.strip()
        # Find JSON in response
        for start in ['{', '```json\n{', '```\n{']:
            if start in text:
                idx = text.index(start.split('\n')[-1] if '\n' in start else start)
                json_str = text[idx:]
                # Find closing brace
                end = json_str.rfind('}')
                if end != -1:
                    json_str = json_str[:end+1]
                    try:
                        data = json.loads(json_str)
                        if "tool" in data:
                            import asyncio
                            loop = asyncio.get_event_loop()
                            return loop.run_until_complete(
                                self._call(data["tool"], data.get("args", {}))
                            )
                    except Exception:
                        pass
        return None

    async def _call(self, name: str, params: dict):
        try:
            if name == "read_file":         return self.files.read_file(params["path"])
            if name == "write_file":        return self.files.write_file(params["path"], params["content"])
            if name == "list_directory":    return self.files.list_directory(params.get("path", "."))
            if name == "delete_file":       return self.files.delete_file(params["path"])
            if name == "move_file":         return self.files.move_file(params["source"], params["destination"])
            if name == "run_command":       return self.shell.run_command(params["command"], params.get("working_dir"))
            if name == "run_python":        return self.shell.run_python(params["code"])
            if name == "web_search":        return await self.browser.search(params["query"])
            if name == "fetch_url":         return await self.browser.fetch_url(params["url"])
            if name == "send_email":        return self.email.send_email(params["to"], params["subject"], params["body"])
            if name == "create_calendar_event": return self.email.create_calendar_event(
                params["title"], params["start"], params["end"], params.get("description", ""))
            return f"Unknown tool: {name}"
        except Exception as e:
            return f"Tool error: {e}"

    def get_history(self):
        return self.history

    def clear_context(self):
        self.messages = []
