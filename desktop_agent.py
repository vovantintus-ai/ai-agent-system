"""
AI Desktop Agent — VoVa_vOvA Products and Service
Реальное управление ПК: голос + текст + AI
"""
import os, sys, subprocess, threading, queue, time, json, re, io, wave
import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path
import datetime

# ── .env ──────────────────────────────────────────────────────
AGENT_DIR = Path(__file__).parent
env = AGENT_DIR / ".env"
if env.exists():
    for line in env.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GPT_KEY    = os.environ.get("OPENAI_API_KEY", "")

# ── Цвета ─────────────────────────────────────────────────────
BG     = "#0d1117"
CARD   = "#161b22"
TEXT   = "#e6edf3"
ACCENT = "#58a6ff"
GREEN  = "#3fb950"
RED    = "#f85149"
GOLD   = "#d29922"
MUTED  = "#8b949e"
PURPLE = "#bc8cff"

# ══════════════════════════════════════════════════════════════
#  ИНСТРУМЕНТЫ — реальные действия
# ══════════════════════════════════════════════════════════════

APP_MAP = {
    "chrome":"chrome","хром":"chrome",
    "firefox":"firefox","фаерфокс":"firefox",
    "telegram":"telegram","телеграм":"telegram",
    "notepad":"notepad","блокнот":"notepad",
    "calculator":"calc","калькулятор":"calc","calc":"calc",
    "explorer":"explorer","проводник":"explorer","файлы":"explorer",
    "word":"winword","excel":"excel","powerpoint":"powerpnt",
    "cmd":"cmd","командная строка":"cmd",
    "powershell":"powershell",
    "paint":"mspaint","пейнт":"mspaint",
    "taskmgr":"taskmgr","диспетчер задач":"taskmgr",
    "spotify":"spotify","vlc":"vlc",
    "zoom":"zoom","teams":"teams",
}

EXE_MAP = {
    "chrome":"chrome.exe","firefox":"firefox.exe",
    "telegram":"telegram.exe","notepad":"notepad.exe",
    "calc":"calc.exe","explorer":"explorer.exe",
    "winword":"winword.exe","excel":"excel.exe",
    "mspaint":"mspaint.exe","taskmgr":"taskmgr.exe",
    "spotify":"spotify.exe","vlc":"vlc.exe",
    "zoom":"zoom.exe","teams":"teams.exe",
}

def open_app(app: str) -> str:
    exe = APP_MAP.get(app.lower().strip(), app)
    try:
        subprocess.Popen(exe, shell=True)
        return f"✅ Открываю {app}"
    except Exception as e:
        return f"❌ Не могу открыть {app}: {e}"

def close_app(app: str) -> str:
    cmd = APP_MAP.get(app.lower().strip(), app)
    exe = EXE_MAP.get(cmd, cmd if cmd.endswith(".exe") else cmd + ".exe")
    try:
        r = subprocess.run(["taskkill","/F","/IM",exe],
                           capture_output=True, text=True)
        return f"✅ {app} закрыт" if r.returncode == 0 else f"⚠️ {app} не найден"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def do_screenshot() -> str:
    fname = AGENT_DIR / f"screen_{datetime.datetime.now().strftime('%H%M%S')}.png"
    # Try pyautogui first
    try:
        import pyautogui
        pyautogui.screenshot(str(fname))
        return f"✅ Скриншот сохранён → {fname.name}"
    except ImportError:
        pass
    # Fallback: PowerShell
    try:
        ps = (
            "Add-Type -Assembly System.Windows.Forms,System.Drawing;"
            "$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
            "$b=New-Object System.Drawing.Bitmap($s.Width,$s.Height);"
            "$g=[System.Drawing.Graphics]::FromImage($b);"
            "$g.CopyFromScreen(0,0,0,0,$b.Size);"
            f"$b.Save('{fname}')"
        )
        subprocess.run(["powershell","-Command",ps], timeout=10, capture_output=True)
        return f"✅ Скриншот: {fname.name}"
    except Exception as e:
        return f"❌ Скриншот: {e}"

def press_key(key: str) -> str:
    try:
        import pyautogui
        KEY_MAP = {
            "enter":"enter","энтер":"enter","ввод":"enter",
            "escape":"escape","esc":"escape","эскейп":"escape",
            "tab":"tab","таб":"tab",
            "space":"space","пробел":"space",
            "backspace":"backspace","удалить":"backspace",
            "delete":"delete","del":"delete",
            "f5":"f5","обновить":"f5",
            "f4":"f4","f11":"f11",
            "home":"home","end":"end",
            "pageup":"pageup","pagedown":"pagedown",
            "up":"up","вверх":"up",
            "down":"down","вниз":"down",
            "left":"left","влево":"left",
            "right":"right","вправо":"right",
        }
        k = KEY_MAP.get(key.lower().strip(), key.lower().strip())
        pyautogui.press(k)
        return f"✅ Нажал {key}"
    except ImportError:
        return "❌ Установи pyautogui: pip install pyautogui"
    except Exception as e:
        return f"❌ {e}"

def press_hotkey(keys: str) -> str:
    try:
        import pyautogui
        # Parse "ctrl+c" or "ctrl c" or "ctrl и c"
        parts = re.split(r'[+\s&]+', keys.lower().strip())
        parts = [p.strip() for p in parts if p.strip()]
        pyautogui.hotkey(*parts)
        return f"✅ Нажал {'+'.join(parts)}"
    except ImportError:
        return "❌ Установи pyautogui"
    except Exception as e:
        return f"❌ {e}"

def type_text(text: str) -> str:
    try:
        import pyautogui
        pyautogui.write(text, interval=0.04)
        return f"✅ Напечатал: {text[:40]}"
    except ImportError:
        return "❌ Установи pyautogui"
    except Exception as e:
        return f"❌ {e}"

def control_volume(action: str) -> str:
    try:
        import pyautogui
        a = action.lower()
        if any(w in a for w in ["больше","громче","up","увелич"]):
            for _ in range(5): pyautogui.press("volumeup")
            return "✅ Громче"
        elif any(w in a for w in ["тише","меньше","down","уменьш"]):
            for _ in range(5): pyautogui.press("volumedown")
            return "✅ Тише"
        else:
            pyautogui.press("volumemute")
            return "✅ Звук вкл/выкл"
    except ImportError:
        subprocess.run(
            'powershell -c "(New-Object -com WScript.Shell).SendKeys([char]173)"',
            shell=True)
        return "✅ Громкость изменена"

def search_web(query: str) -> str:
    import urllib.parse
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"✅ Ищу: {query}"

def get_weather(city="Amsterdam") -> str:
    try:
        import urllib.request
        with urllib.request.urlopen(
                f"https://wttr.in/{city}?format=3", timeout=6) as r:
            return "🌤️ " + r.read().decode().strip()
    except Exception as e:
        return f"❌ Погода недоступна: {e}"

def get_time() -> str:
    n = datetime.datetime.now()
    days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
    return f"🕐 {n.strftime('%H:%M')} | {days[n.weekday()]} {n.strftime('%d.%m.%Y')}"

def run_shell(cmd: str) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=10, encoding="utf-8", errors="replace")
        out = (r.stdout + r.stderr).strip()[:400]
        return f"✅ {out}" if out else "✅ Выполнено"
    except subprocess.TimeoutExpired:
        return "⏱️ Команда выполняется слишком долго"
    except Exception as e:
        return f"❌ {e}"

# ══════════════════════════════════════════════════════════════
#  AI РОУТЕР
# ══════════════════════════════════════════════════════════════

SYSTEM = """\
Ты AI-агент управления компьютером. На каждую команду пользователя отвечай ТОЛЬКО JSON.

Доступные действия:
{"action":"open_app","app":"chrome|notepad|calculator|telegram|explorer|firefox|word|excel|cmd|paint"}
{"action":"close_app","app":"chrome|telegram|..."}
{"action":"screenshot"}
{"action":"key","key":"enter|escape|tab|space|f5|delete|backspace|up|down|left|right"}
{"action":"hotkey","keys":"ctrl+c|ctrl+v|ctrl+z|ctrl+s|ctrl+a|alt+f4|ctrl+w|win+d"}
{"action":"type","text":"текст для ввода"}
{"action":"volume","cmd":"громче|тише|выкл"}
{"action":"search","query":"что искать"}
{"action":"weather","city":"Amsterdam"}
{"action":"time"}
{"action":"shell","command":"команда cmd"}
{"action":"chat","reply":"ответ на обычный вопрос"}

Правила:
- Отвечай ТОЛЬКО JSON, никакого текста вокруг
- "открой" / "запусти" → open_app
- "закрой" / "выйди" → close_app  
- "скриншот" / "снимок экрана" → screenshot
- "нажми enter" → key
- "ctrl+c" / "скопируй" → hotkey
- "напечатай текст" → type
- Обычный вопрос → chat
"""

def route(text: str) -> dict:
    """Локальные паттерны + AI"""
    t = text.lower().strip()

    # ── Локальные быстрые паттерны ────────────────────────────
    # Время
    if any(w in t for w in ["который час","сколько времени","время","time","clock","часы"]):
        return {"action":"time"}

    # Скриншот
    if any(w in t for w in ["скриншот","screenshot","снимок экрана","сфотографируй экран"]):
        return {"action":"screenshot"}

    # Погода
    if any(w in t for w in ["погода","weather","температура","градус"]):
        city = "Amsterdam"
        for c in ["rotterdam","amsterdam","moscow","москва","utrecht","гаага","den haag"]:
            if c in t:
                city = c.title()
                break
        return {"action":"weather","city":city}

    # Открыть приложение
    if any(w in t for w in ["открой","запусти","запустить","открыть","launch","start","open"]):
        for app_name in APP_MAP:
            if app_name in t:
                return {"action":"open_app","app":app_name}

    # Закрыть приложение
    if any(w in t for w in ["закрой","закрыть","close","kill","завершить","выйди из"]):
        for app_name in APP_MAP:
            if app_name in t:
                return {"action":"close_app","app":app_name}

    # Hotkeys — распознаём распространённые
    hotkey_patterns = {
        r"ctrl\s*[\+\s]\s*c|скопируй|копировать":   "ctrl+c",
        r"ctrl\s*[\+\s]\s*v|вставь|вставить":        "ctrl+v",
        r"ctrl\s*[\+\s]\s*z|отмени|отменить":        "ctrl+z",
        r"ctrl\s*[\+\s]\s*s|сохрани|сохранить":      "ctrl+s",
        r"ctrl\s*[\+\s]\s*a|выдели всё|выбрать всё": "ctrl+a",
        r"ctrl\s*[\+\s]\s*w|закрой вкладку":          "ctrl+w",
        r"alt\s*[\+\s]\s*f4|закрой окно":             "alt+f4",
        r"win\s*[\+\s]\s*d|рабочий стол|свернуть всё":"win+d",
        r"alt\s*[\+\s]\s*tab|переключи окно":          "alt+tab",
        r"ctrl\s*[\+\s]\s*alt\s*[\+\s]\s*del":        "ctrl+alt+delete",
        r"win\s*[\+\s]\s*l|заблокируй|блокировка":    "win+l",
    }
    for pattern, keys in hotkey_patterns.items():
        if re.search(pattern, t):
            return {"action":"hotkey","keys":keys}

    # Одиночные клавиши
    key_patterns = {
        r"\benter\b|\bэнтер\b|\bввод\b":                "enter",
        r"\bescape\b|\besc\b|\bэскейп\b|\bотмена\b":    "escape",
        r"\btab\b|\bтаб\b":                              "tab",
        r"\bdelete\b|\bудалить\b|\bделит\b":             "delete",
        r"\bbackspace\b|\bбекспейс\b":                   "backspace",
        r"\bf5\b|\bобновить\b|\bобнови\b":               "f5",
        r"\bf11\b|\bполный экран\b":                      "f11",
        r"\bspace\b|\bпробел\b":                          "space",
    }
    if any(w in t for w in ["нажми","press","нажать","нажмите"]):
        for pattern, key in key_patterns.items():
            if re.search(pattern, t):
                return {"action":"key","key":key}

    # Напечатать текст
    type_match = re.search(r'(?:напечатай|напиши|введи|type)\s+(.+)', t)
    if type_match:
        return {"action":"type","text":type_match.group(1).strip()}

    # Поиск
    if any(w in t for w in ["найди","поищи","загугли","search","google"]):
        q = t
        for w in ["найди","поищи","загугли","search","google","в интернете","в гугле"]:
            q = q.replace(w,"").strip()
        return {"action":"search","query":q}

    # Громкость
    if any(w in t for w in ["громкость","volume","тише","громче","звук"]):
        return {"action":"volume","cmd":t}

    # ── AI роутинг ───────────────────────────────────────────
    if GEMINI_KEY:
        try:
            import urllib.request
            url = (f"https://generativelanguage.googleapis.com/v1beta/"
                   f"models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}")
            body = json.dumps({"contents":[{"parts":[{
                "text": f"{SYSTEM}\n\nКоманда пользователя: {text}"}]}]}).encode()
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type":"application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            raw = re.sub(r"```json\s*|```","",raw).strip()
            return json.loads(raw)
        except Exception:
            pass

    if GPT_KEY:
        try:
            import urllib.request
            url = "https://api.openai.com/v1/chat/completions"
            body = json.dumps({
                "model":"gpt-4o-mini",
                "messages":[
                    {"role":"system","content":SYSTEM},
                    {"role":"user","content":text}
                ],
                "max_tokens":150
            }).encode()
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type":"application/json",
                         "Authorization":f"Bearer {GPT_KEY}"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            raw = data["choices"][0]["message"]["content"].strip()
            raw = re.sub(r"```json\s*|```","",raw).strip()
            return json.loads(raw)
        except Exception:
            pass

    # Финальный fallback
    return {"action":"chat",
            "reply":(f"Не понял: «{text}»\n"
                     "Попробуй: открой chrome, скриншот, который час, "
                     "ctrl+c, нажми enter, найди рецепт борща")}

def execute(cmd: dict) -> str:
    a = cmd.get("action","chat")
    try:
        if   a == "open_app":  return open_app(cmd.get("app",""))
        elif a == "close_app": return close_app(cmd.get("app",""))
        elif a == "screenshot":return do_screenshot()
        elif a == "key":       return press_key(cmd.get("key",""))
        elif a == "hotkey":    return press_hotkey(cmd.get("keys",""))
        elif a == "type":      return type_text(cmd.get("text",""))
        elif a == "volume":    return control_volume(cmd.get("cmd",""))
        elif a == "search":    return search_web(cmd.get("query",""))
        elif a == "weather":   return get_weather(cmd.get("city","Amsterdam"))
        elif a == "time":      return get_time()
        elif a == "shell":     return run_shell(cmd.get("command",""))
        elif a == "chat":      return cmd.get("reply","...")
        else: return f"❓ Неизвестное действие: {a}"
    except Exception as e:
        return f"❌ Ошибка выполнения: {e}"

# ══════════════════════════════════════════════════════════════
#  ИНТЕРФЕЙС
# ══════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🤖 AI Desktop Agent — VoVa_vOvA")
        self.geometry("760x580")
        self.configure(bg=BG)
        self.minsize(600,450)

        self._voice_on = False
        self._speak_q  = queue.Queue()
        self._build()
        self._tts_start()
        self._log("sys", "🤖 AI Desktop Agent готов!")
        if not GEMINI_KEY and not GPT_KEY:
            self._log("err", "⚠️ API ключ не найден в .env — AI роутинг отключён, работают локальные команды")
        else:
            self._log("sys", f"✅ AI: {'Gemini' if GEMINI_KEY else 'GPT-4o Mini'}")
        self._log("sys", 'Попробуй: "открой chrome" · "скриншот" · "который час" · "ctrl+c"')

    # ── UI ────────────────────────────────────────────────────
    def _build(self):
        # Header
        h = tk.Frame(self, bg="#0d2137", pady=8)
        h.pack(fill="x")
        tk.Label(h, text="🤖  AI Desktop Agent",
                 bg="#0d2137", fg=ACCENT,
                 font=("Segoe UI",15,"bold")).pack(side="left", padx=14)
        tk.Label(h, text="VoVa_vOvA Products and Service",
                 bg="#0d2137", fg=GOLD,
                 font=("Segoe UI",9)).pack(side="right", padx=14)

        # Status
        sf = tk.Frame(self, bg=CARD, pady=5)
        sf.pack(fill="x", padx=8, pady=(5,0))
        self._dot = tk.Label(sf, text="⚫", bg=CARD, font=("Segoe UI",13))
        self._dot.pack(side="left", padx=8)
        self._status = tk.Label(sf, text="Готов",
                                 bg=CARD, fg=TEXT,
                                 font=("Segoe UI",10), anchor="w")
        self._status.pack(side="left", fill="x", expand=True)

        # Log
        self._chat = scrolledtext.ScrolledText(
            self, bg="#010409", fg=TEXT,
            font=("Segoe UI",10), wrap="word",
            state="disabled", relief="flat", bd=0)
        self._chat.pack(fill="both", expand=True, padx=8, pady=5)
        for tag, fg, bold in [
            ("you", ACCENT, True), ("bot", GREEN, True),
            ("sys", GOLD, False),  ("err", RED, True),
            ("msg", TEXT, False),  ("act", PURPLE, False),
        ]:
            self._chat.tag_config(
                tag, foreground=fg,
                font=("Segoe UI",10,"bold" if bold else "normal"))

        # Input
        inf = tk.Frame(self, bg=BG)
        inf.pack(fill="x", padx=8, pady=(0,5))
        self._inp = tk.Entry(inf, bg="#161b22", fg=TEXT,
                              font=("Segoe UI",12), relief="flat",
                              insertbackground=TEXT, bd=6)
        self._inp.pack(side="left", fill="x", expand=True, ipady=7)
        self._inp.bind("<Return>",   lambda e: self._send())
        self._inp.bind("<KP_Enter>", lambda e: self._send())
        self._inp.focus()
        tk.Button(inf, text="Отправить ↵",
                  command=self._send,
                  bg=ACCENT, fg="white",
                  font=("Segoe UI",11,"bold"),
                  relief="flat", padx=14, pady=7,
                  cursor="hand2").pack(side="left", padx=(5,0))

        # Buttons row 1
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(0,3))
        self._vbtn = tk.Button(
            bf, text="🎙️  Start Voice",
            command=self._voice_toggle,
            bg=GREEN, fg="#000",
            font=("Segoe UI",10,"bold"),
            relief="flat", padx=14, pady=6, cursor="hand2")
        self._vbtn.pack(side="left", padx=3)
        tk.Button(bf, text="🎤 Тест микрофона",
                  command=lambda: threading.Thread(
                      target=self._mic_test, daemon=True).start(),
                  bg=GOLD, fg="#000",
                  font=("Segoe UI",10,"bold"),
                  relief="flat", padx=12, pady=6, cursor="hand2"
                  ).pack(side="left", padx=3)
        tk.Button(bf, text="🗑️ Очистить",
                  command=self._clear,
                  bg=CARD, fg=TEXT,
                  font=("Segoe UI",10), relief="flat",
                  padx=12, pady=6, cursor="hand2"
                  ).pack(side="left", padx=3)

        # Quick buttons row 2
        qf = tk.Frame(self, bg=BG)
        qf.pack(pady=(0,6))
        tk.Label(qf, text="Быстро:", bg=BG, fg=MUTED,
                 font=("Segoe UI",9)).pack(side="left", padx=(6,4))
        quick = [
            ("📸 Скрин",    "скриншот"),
            ("🕐 Время",    "который час"),
            ("🌤️ Погода",   "погода"),
            ("🌐 Chrome",   "открой chrome"),
            ("📝 Блокнот",  "открой блокнот"),
            ("📋 Копировать","ctrl+c"),
            ("📋 Вставить",  "ctrl+v"),
            ("↩️ Отменить",  "ctrl+z"),
        ]
        for lbl, cmd in quick:
            tk.Button(qf, text=lbl,
                      command=lambda c=cmd: self._quick(c),
                      bg=CARD, fg=TEXT,
                      font=("Segoe UI",9), relief="flat",
                      padx=7, pady=3, cursor="hand2"
                      ).pack(side="left", padx=2)

    # ── Helpers ───────────────────────────────────────────────
    def _log(self, role, text):
        try:
            self._chat.config(state="normal")
            labels = {"you":"▶ Ты","bot":"🤖","sys":"⚙","err":"❌","act":"⚡"}
            self._chat.insert("end", f"{labels.get(role,role)}: ", role)
            self._chat.insert("end", text + "\n", "msg")
            self._chat.see("end")
            self._chat.config(state="disabled")
        except: pass

    def _set(self, text, dot="⚫"):
        try:
            self._status.config(text=text)
            self._dot.config(text=dot)
        except: pass

    def _clear(self):
        try:
            self._chat.config(state="normal")
            self._chat.delete("1.0","end")
            self._chat.config(state="disabled")
        except: pass

    def _quick(self, cmd):
        self._inp.delete(0,"end")
        self._inp.insert(0, cmd)
        self._send()

    # ── Send / Process ────────────────────────────────────────
    def _send(self):
        text = self._inp.get().strip()
        if not text: return
        self._inp.delete(0,"end")
        self._log("you", text)
        self._set("🔵 Выполняю...", "🔵")
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text):
        try:
            cmd = route(text)
            action = cmd.get("action","chat")
            if action != "chat":
                self.after(0, lambda a=action:
                    self._log("act", f"Действие: {a}"))
            result = execute(cmd)
            self.after(0, lambda r=result: self._log("bot", r))
            self.after(0, lambda: self._set("Готов", "🟢"))
            self._speak(result)
        except Exception as e:
            self.after(0, lambda: self._log("err", str(e)))
            self.after(0, lambda: self._set("Ошибка", "🔴"))

    # ── TTS ───────────────────────────────────────────────────
    def _tts_start(self):
        def worker():
            try:
                import pyttsx3
                e = pyttsx3.init()
                e.setProperty("rate", 165)
                e.setProperty("volume", 1.0)
                for v in e.getProperty("voices"):
                    if any(x in v.name.lower()
                           for x in ["russian","irina","zira","elena"]):
                        e.setProperty("voice", v.id)
                        break
                while True:
                    try:
                        t = self._speak_q.get(timeout=1)
                        e.say(t[:180])
                        e.runAndWait()
                    except queue.Empty:
                        continue
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _speak(self, text):
        clean = re.sub(r'[✅❌⚠️🎙🤖⚙️📸🌤️🕐📋↩️⚡🔵🟢🔴⚫]','', text)
        clean = re.sub(r'\n',' ', clean).strip()
        try: self._speak_q.put_nowait(clean[:180])
        except: pass

    # ── Voice ─────────────────────────────────────────────────
    def _voice_toggle(self):
        if self._voice_on:
            self._voice_on = False
            self._vbtn.config(text="🎙️  Start Voice", bg=GREEN)
            self._set("Голос остановлен", "⚫")
            self._log("sys", "🔇 Голосовое управление остановлено")
        else:
            self._voice_on = True
            self._vbtn.config(text="⏹  Stop Voice", bg=RED)
            threading.Thread(target=self._voice_loop, daemon=True).start()

    def _voice_loop(self):
        try:
            import speech_recognition as sr
            import sounddevice as sd
            import numpy as np

            rec  = sr.Recognizer()
            SR   = 16000
            WAKE = ["агент","agent","ассистент","hey agent","эй агент"]

            self.after(0, lambda: self._set('Слушаю — скажи "Агент"', "🟢"))
            self.after(0, lambda: self._log("sys", '🎙️ Скажи "Агент [команда]"'))
            self._speak("Готов. Скажи Агент.")

            def record(sec=5):
                audio = sd.rec(int(sec*SR), samplerate=SR,
                               channels=1, dtype="int16")
                sd.wait()
                buf = io.BytesIO()
                with wave.open(buf,"wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2)
                    wf.setframerate(SR); wf.writeframes(audio.tobytes())
                buf.seek(0)
                return sr.AudioData(buf.read(), SR, 2)

            def recognize(aud):
                for lang in ["ru-RU","en-US","nl-NL"]:
                    try: return rec.recognize_google(aud, language=lang)
                    except sr.UnknownValueError: continue
                    except: return ""
                return ""

            while self._voice_on:
                self.after(0, lambda: self._dot.config(text="🟢"))
                aud = record(5)
                text = recognize(aud)
                if not text: continue

                tl = text.lower()
                self.after(0, lambda t=text:
                    self._status.config(text=f'Слышу: "{t}"'))

                if not any(w in tl for w in WAKE):
                    continue

                # Убираем wake word
                cmd_text = tl
                for w in sorted(WAKE, key=len, reverse=True):
                    cmd_text = cmd_text.replace(w,"").strip(" ,!?.")

                if not cmd_text:
                    self._speak("Слушаю")
                    self.after(0, lambda: self._set("Говори команду...", "🔵"))
                    aud2 = record(7)
                    cmd_text = recognize(aud2)

                if cmd_text:
                    self.after(0, lambda c=cmd_text:
                        self._log("you", f"🎙️ {c}"))
                    self.after(0, lambda: self._set("🔵 Выполняю...", "🔵"))
                    threading.Thread(
                        target=self._process, args=(cmd_text,),
                        daemon=True).start()

        except ImportError as e:
            self.after(0, lambda: self._log("err",
                f"Установи: pip install SpeechRecognition sounddevice scipy\n{e}"))
        except Exception as e:
            self.after(0, lambda: self._log("err", f"Голос: {e}"))
        finally:
            self._voice_on = False
            self.after(0, lambda: self._vbtn.config(
                text="🎙️  Start Voice", bg=GREEN))
            self.after(0, lambda: self._set("Голос остановлен", "⚫"))

    # ── Mic test ─────────────────────────────────────────────
    def _mic_test(self):
        def log(m, t="sys"):
            self.after(0, lambda m=m,t=t: self._log(t,m))
        log("━━━ ТЕСТ МИКРОФОНА ━━━")
        try:
            import sounddevice as sd, numpy as np
            devs = [d for d in sd.query_devices() if d["max_input_channels"]>0]
            if not devs:
                log("❌ Микрофоны не найдены!", "err")
                log("Подключи микрофон и перезапусти программу", "err")
                return
            log(f"✅ Найдено {len(devs)} микрофон(ов):")
            for d in devs[:4]:
                log(f"  🎙️ {d['name']}")
            default = sd.query_devices(kind="input")
            log(f"⭐ Активный: {default['name']}")
            log("🔴 ГОВОРИ СЕЙЧАС — запись 3 секунды...")
            self.after(0, lambda: self._set("🔴 Запись...", "🔴"))
            audio = sd.rec(int(3*16000), samplerate=16000,
                           channels=1, dtype="int16")
            sd.wait()
            vol = int(np.abs(audio).max())
            log(f"📊 Уровень сигнала: {vol}/32767")
            if   vol > 2000: log("✅ Сигнал отличный!")
            elif vol > 500:  log("⚠️ Сигнал слабый — говори громче")
            else:            log("❌ Сигнал не обнаружен!", "err"); return

            # STT
            import speech_recognition as sr
            buf = io.BytesIO()
            with wave.open(buf,"wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2)
                wf.setframerate(16000); wf.writeframes(audio.tobytes())
            buf.seek(0)
            aud = sr.AudioData(buf.read(), 16000, 2)
            try:
                text = sr.Recognizer().recognize_google(aud, language="ru-RU")
                log(f"✅ Распознано: «{text}»")
                log("🎉 Микрофон работает отлично!")
            except sr.UnknownValueError:
                log("⚠️ Речь не распознана. Говори чётче или проверь интернет.")
            except Exception as e:
                log(f"❌ STT ошибка: {e}", "err")
        except ImportError:
            log("❌ Запусти install_all.bat от Администратора!", "err")
        except Exception as e:
            log(f"❌ {e}", "err")
        finally:
            self.after(0, lambda: self._set("Готов", "🟢"))
            log("━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--autostart", action="store_true",
                        help="Auto-start voice on launch")
    args, _ = parser.parse_known_args()

    app = App()

    # Auto-start voice if flag set OR if running from startup
    auto = args.autostart or any(
        x in " ".join(sys.argv).lower()
        for x in ["autostart","startup","автозапуск"])

    if auto:
        # Small delay to let UI load, then start voice
        app.after(2000, lambda: (
            app._log("sys", "🤖 Автозапуск — голосовое управление включается..."),
            app._voice_toggle()
        ))

    app.mainloop()
