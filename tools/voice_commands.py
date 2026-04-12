"""
Voice Command Recognition - распознаёт намерения из текста и вызывает нужные функции
Работает на RU / EN / NL
"""
import re

# ── Паттерны команд ───────────────────────────────────────────────────────────

PATTERNS = [

    # ФИНАНСЫ
    {"intent": "add_income",
     "patterns": [r"(доход|получил|заработал|income|received|ontvangen)\s+(\d+[\.,]?\d*)",
                  r"(\d+[\.,]?\d*)\s*(евро|euro|eur|€|доход)"],
     "desc": "💚 Доход"},

    {"intent": "add_expense",
     "patterns": [r"(расход|потратил|купил|expense|spent|betaald|uitgave)\s+(\d+[\.,]?\d*)",
                  r"(\d+[\.,]?\d*)\s*(евро|euro|eur|€)\s+на\s+(\w+)"],
     "desc": "💸 Расход"},

    {"intent": "balance",
     "patterns": [r"(баланс|balance|saldo|остаток|сколько денег|how much money)"],
     "desc": "💰 Баланс"},

    {"intent": "finance_report",
     "patterns": [r"(отчёт|отчет|report|rapportage|финансовый отчёт|financial report)"],
     "desc": "📊 Финансовый отчёт"},

    # CRM
    {"intent": "add_client",
     "patterns": [r"(добавь клиента|новый клиент|add client|nieuwe klant)\s+(.+)",
                  r"(клиент|client|klant)\s+(добавить|add|nieuw)\s+(.+)"],
     "desc": "👤 Добавить клиента"},

    {"intent": "list_clients",
     "patterns": [r"(список клиентов|мои клиенты|all clients|klanten|show clients|покажи клиентов)"],
     "desc": "👥 Список клиентов"},

    {"intent": "crm_stats",
     "patterns": [r"(crm|crm статистика|сделки|deals|pipeline|воронка продаж)"],
     "desc": "📊 CRM статистика"},

    # СЧЕТА
    {"intent": "list_invoices",
     "patterns": [r"(счета|счёта|invoices|facturen|мои счета|show invoices)"],
     "desc": "🧾 Список счетов"},

    # ПК УПРАВЛЕНИЕ
    {"intent": "open_app",
     "patterns": [r"(открой|запусти|open|start|opstarten)\s+(chrome|firefox|telegram|notepad|explorer|calculator|calc|vscode|cmd|powershell)"],
     "desc": "🚀 Открыть программу"},

    {"intent": "press_key",
     "patterns": [r"(нажми|нажать|press|druk op)\s+(enter|escape|esc|tab|space|delete|f\d+|home|end|up|down)"],
     "desc": "⌨️ Нажать клавишу"},

    {"intent": "hotkey",
     "patterns": [r"(комбинация|hotkey|сочетание)\s+(ctrl|alt|shift)\s*\+?\s*(\w+)",
                  r"(ctrl|alt|shift)\s*\+\s*(\w+)"],
     "desc": "⌨️ Горячие клавиши"},

    {"intent": "type_text",
     "patterns": [r"(напечатай|введи текст|type|schrijf)\s+(.+)",
                  r"(напиши|write)\s+[\"\'«»](.+)[\"\'«»]"],
     "desc": "⌨️ Печать текста"},

    {"intent": "screenshot",
     "patterns": [r"(скриншот|screenshot|снимок экрана|schermafbeelding|сделай скрин)"],
     "desc": "📸 Скриншот"},

    # ПАМЯТЬ И ИСТОРИЯ
    {"intent": "memory",
     "patterns": [r"(память|what do you remember|что ты помнишь|мои данные|my memory)"],
     "desc": "🧠 Память"},

    {"intent": "clear_context",
     "patterns": [r"(очисти|сбрось|clear|reset|wis)\s+(контекст|context|историю|history|всё|all)"],
     "desc": "🗑️ Очистить контекст"},

    # МОНИТОРИНГ ЦЕН
    {"intent": "check_prices",
     "patterns": [r"(проверь цены|check prices|prijzen|цены изменились|price check)"],
     "desc": "🔔 Проверить цены"},

    # БРИФИНГ
    {"intent": "briefing",
     "patterns": [r"(брифинг|briefing|новости|дай сводку|what's new|что нового|nieuws)"],
     "desc": "☀️ Брифинг"},

    # НАПОМИНАНИЯ
    {"intent": "reminders",
     "patterns": [r"(напоминания|reminders|мои задачи|my tasks|herinneringen)"],
     "desc": "🔔 Напоминания"},

    # ПОГОДА
    {"intent": "weather",
     "patterns": [r"(погода|weather|weer|какая погода|what's the weather)"],
     "desc": "🌤️ Погода"},

    # ПОМОЩЬ
    {"intent": "help",
     "patterns": [r"(помощь|помоги|help|hulp|что ты умеешь|what can you do|команды|commands)"],
     "desc": "❓ Помощь"},
]


def extract_amount(text: str) -> float:
    """Extract number from text"""
    m = re.search(r'(\d+[\.,]\d+|\d+)', text)
    if m:
        return float(m.group(1).replace(',', '.'))
    return 0.0


def extract_after_keyword(text: str, keywords: list) -> str:
    """Extract words after a keyword"""
    text_lower = text.lower()
    for kw in keywords:
        idx = text_lower.find(kw)
        if idx != -1:
            return text[idx + len(kw):].strip()
    return ""


def recognize_intent(text: str) -> dict | None:
    """
    Returns dict with:
      intent: str
      desc: str
      params: dict
      original: str
    Or None if no intent found
    """
    text_lower = text.lower().strip()

    for pattern_group in PATTERNS:
        for pat in pattern_group["patterns"]:
            m = re.search(pat, text_lower, re.IGNORECASE)
            if m:
                intent = pattern_group["intent"]
                params = _extract_params(intent, text, text_lower, m)
                return {
                    "intent": intent,
                    "desc": pattern_group["desc"],
                    "params": params,
                    "original": text
                }
    return None


def _extract_params(intent: str, text: str, text_lower: str, match) -> dict:
    """Extract parameters based on intent"""
    params = {}

    if intent == "add_income":
        params["amount"] = extract_amount(text)
        # Description = everything that's not a number or keyword
        desc = re.sub(r'(доход|получил|заработал|income|received|ontvangen|\d+[\.,]?\d*|евро|euro|eur|€)', '', text, flags=re.IGNORECASE).strip()
        params["description"] = desc or "income"

    elif intent == "add_expense":
        params["amount"] = extract_amount(text)
        desc = re.sub(r'(расход|потратил|купил|expense|spent|betaald|uitgave|\d+[\.,]?\d*|евро|euro|eur|€)', '', text, flags=re.IGNORECASE).strip()
        params["description"] = desc or "expense"

    elif intent == "add_client":
        name = extract_after_keyword(text_lower,
            ["добавь клиента", "новый клиент", "add client", "nieuwe klant", "клиент"])
        params["name"] = name.strip() or "New Client"

    elif intent == "open_app":
        apps = ["chrome","firefox","telegram","notepad","explorer","calculator","calc","vscode","cmd","powershell"]
        for app in apps:
            if app in text_lower:
                params["app"] = app; break

    elif intent == "press_key":
        keys = ["enter","escape","esc","tab","space","delete","home","end","up","down"]
        for key in keys:
            if key in text_lower:
                params["key"] = key; break
        # F-keys
        fkey = re.search(r'f(\d+)', text_lower)
        if fkey: params["key"] = f"f{fkey.group(1)}"

    elif intent == "hotkey":
        mods = []
        if "ctrl" in text_lower: mods.append("ctrl")
        if "alt" in text_lower: mods.append("alt")
        if "shift" in text_lower: mods.append("shift")
        # Find the final key
        cleaned = re.sub(r'(ctrl|alt|shift|\+|комбинация|hotkey|сочетание)', '', text_lower).strip()
        final_key = cleaned.split()[-1] if cleaned.split() else ""
        params["keys"] = mods + [final_key] if final_key else mods

    elif intent == "type_text":
        typed = extract_after_keyword(text_lower,
            ["напечатай", "введи текст", "type", "schrijf", "напиши", "write"])
        typed = re.sub(r'[«»"\']', '', typed).strip()
        params["text"] = typed

    return params


def format_voice_result(recognized: dict) -> str:
    """Format what was recognized for user feedback"""
    intent = recognized["intent"]
    params = recognized["params"]
    desc = recognized["desc"]

    parts = [f"🎤 Recognized: **{desc}**"]
    if params:
        for k, v in params.items():
            if v:
                parts.append(f"   {k}: {v}")
    return "\n".join(parts)
