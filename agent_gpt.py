import os
os.environ["PYTHONUTF8"] = "1"
"""
Agent - OpenAI GPT
"""

import os
import json
from datetime import datetime
from tools.file_tools import FileTools
from tools.shell_tools import ShellTools
from tools.browser_tools import BrowserTools
from tools.email_tools import EmailTools

GPT_MODEL   = os.getenv("GPT_MODEL", "gpt-4o-mini")
BOT_PERSONA = os.getenv("BOT_PERSONA", "")

SYSTEM = f"""You are an autonomous AI agent. Execute user tasks using available tools.

LANGUAGE: Russian → reply Russian. Ukrainian → reply Ukrainian. English → reply English.
LOCATION: User is in Netherlands (CET, euros €, DD.MM.YYYY).
Always describe what you are doing before each action.
{('PERSONALITY: ' + BOT_PERSONA) if BOT_PERSONA else ''}"""

TOOLS = [
    {"type": "function", "function": {
        "name": "read_file", "description": "Read contents of a file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Create or overwrite a file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "list_directory", "description": "List files in a directory",
        "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}}}},
    {"type": "function", "function": {
        "name": "delete_file", "description": "Delete a file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "move_file", "description": "Move or rename a file",
        "parameters": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}}},
    {"type": "function", "function": {
        "name": "run_command", "description": "Run a PowerShell command",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "working_dir": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "run_python", "description": "Execute Python code",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {
        "name": "web_search", "description": "Search the internet",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "fetch_url", "description": "Fetch a web page",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "send_email", "description": "Send an email",
        "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}}},
    {"type": "function", "function": {
        "name": "create_calendar_event", "description": "Create a calendar .ics event",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "start": {"type": "string"}, "end": {"type": "string"}, "description": {"type": "string"}}, "required": ["title", "start", "end"]}}},
]


class Agent:
    def __init__(self):
        self.files   = FileTools()
        self.shell   = ShellTools()
        self.browser = BrowserTools()
        self.email   = EmailTools()
        self.history = []
        self.messages = [{"role": "system", "content": SYSTEM}]

        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise ValueError("OPENAI_API_KEY not set in .env")
        self.client = OpenAI(api_key=key)

    async def run(self, task: str) -> str:
        self.history.append({"task": task, "timestamp": datetime.now().isoformat()})
        self.messages.append({"role": "user", "content": task})

        for _ in range(10):
            resp = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            self.messages.append(msg)

            # No tool calls - return text
            if not msg.tool_calls:
                return msg.content or "Done."

            # Execute tool calls
            for tc in msg.tool_calls:
                params = json.loads(tc.function.arguments)
                result = await self._call(tc.function.name, params)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result)
                })

        return "Done."

    async def _call(self, name, params):
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
        self.messages = [{"role": "system", "content": SYSTEM}]
