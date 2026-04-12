"""
AI Desktop Agent PRO — AI Agent System
Управление ПК голосом и текстом. Все манипуляции на ПК.
"""
import os, sys, subprocess, threading, queue, time, json, re, io, wave
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import datetime

# ── .env ──────────────────────────────────────────────────────
AGENT_DIR = Path(__file__).parent
env_file = AGENT_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GPT_KEY    = os.environ.get("OPENAI_API_KEY", "")
CLAUDE_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Цвета (тёмная тема как у старого агента) ──────────────────
BG      = "#1e1e2e"
BG2     = "#2a2a3e"
CARD    = "#313145"
ACCENT  = "#7c3aed"   # фиолетовый
ACCENT2 = "#06b6d4"   # cyan
GREEN   = "#22c55e"
RED     = "#ef4444"
GOLD    = "#f59e0b"
TEXT    = "#e2e8f0"
MUTED   = "#94a3b8"
WHITE   = "#ffffff"

# ══════════════════════════════════════════════════════════════
#  КАРТА ПРИЛОЖЕНИЙ
# ══════════════════════════════════════════════════════════════
APP_MAP = {
    "chrome":"chrome","хром":"chrome","гугл хром":"chrome",
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
    "spotify":"spotify","vlc":"vlc","zoom":"zoom",
    "edge":"msedge","эдж":"msedge",
    "opera":"opera","brave":"brave",
    "telegram":"telegram","телеграм":"telegram","тг":"telegram",
    "whatsapp":"whatsapp","ватсап":"whatsapp",
    "discord":"discord","дискорд":"discord",
    "skype":"skype","скайп":"skype",
}
EXE_MAP = {
    "chrome":"chrome.exe","firefox":"firefox.exe","telegram":"telegram.exe",
    "notepad":"notepad.exe","calc":"calc.exe","explorer":"explorer.exe",
    "winword":"winword.exe","excel":"excel.exe","mspaint":"mspaint.exe",
    "taskmgr":"taskmgr.exe","spotify":"spotify.exe","vlc":"vlc.exe",
    "msedge":"msedge.exe","opera":"opera.exe",
}

# ══════════════════════════════════════════════════════════════
#  ИНСТРУМЕНТЫ — РЕАЛЬНЫЕ ДЕЙСТВИЯ НА ПК
# ══════════════════════════════════════════════════════════════

def pc_open(app):
    exe = APP_MAP.get(app.lower().strip(), app)
    try:
        subprocess.Popen(exe, shell=True)
        return f"✅ Открываю {app}"
    except Exception as e:
        return f"❌ {e}"

def pc_close(app):
    cmd = APP_MAP.get(app.lower().strip(), app)
    exe = EXE_MAP.get(cmd, cmd if ".exe" in cmd else cmd+".exe")
    try:
        r = subprocess.run(["taskkill","/F","/IM",exe], capture_output=True, text=True)
        return f"✅ {app} закрыт" if r.returncode==0 else f"⚠️ {app} не найден"
    except Exception as e:
        return f"❌ {e}"

def pc_screenshot():
    fname = AGENT_DIR / f"screen_{datetime.datetime.now().strftime('%H%M%S')}.png"
    try:
        import pyautogui
        pyautogui.screenshot(str(fname))
        return f"✅ Скриншот → {fname.name}"
    except ImportError:
        try:
            ps = (f'Add-Type -Assembly System.Windows.Forms,System.Drawing;'
                  f'$b=New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,'
                  f'[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height);'
                  f'$g=[System.Drawing.Graphics]::FromImage($b);$g.CopyFromScreen(0,0,0,0,$b.Size);$b.Save("{fname}")')
            subprocess.run(["powershell","-Command",ps], timeout=10, capture_output=True)
            return f"✅ Скриншот → {fname.name}"
        except Exception as e:
            return f"❌ {e}"

def pc_key(key):
    KEY_MAP = {
        "enter":"enter","энтер":"enter","ввод":"enter","подтверди":"enter",
        "escape":"escape","esc":"escape","эскейп":"escape",
        "tab":"tab","таб":"tab",
        "space":"space","пробел":"space",
        "backspace":"backspace","стереть":"backspace",
        "delete":"delete","удалить":"delete","удали":"delete",
        "f1":"f1","f2":"f2","f3":"f3","f4":"f4","f5":"f5",
        "f6":"f6","f7":"f7","f8":"f8","f9":"f9","f10":"f10",
        "f11":"f11","f12":"f12",
        "home":"home","end":"end","pageup":"pageup","pagedown":"pagedown",
        "up":"up","вверх":"up","down":"down","вниз":"down",
        "left":"left","влево":"left","right":"right","вправо":"right",
        "printscreen":"printscreen","prtsc":"printscreen",
    }
    try:
        import pyautogui
        k = KEY_MAP.get(key.lower().strip(), key.lower().strip())
        pyautogui.press(k)
        return f"✅ Нажал {key}"
    except ImportError:
        return "❌ pip install pyautogui"
    except Exception as e:
        return f"❌ {e}"

def pc_hotkey(keys):
    try:
        import pyautogui
        parts = re.split(r'[+\s]', keys.lower().strip())
        parts = [p for p in parts if p]
        pyautogui.hotkey(*parts)
        return f"✅ {'+'.join(parts)}"
    except ImportError:
        return "❌ pip install pyautogui"
    except Exception as e:
        return f"❌ {e}"

def pc_type(text):
    try:
        import pyautogui
        pyautogui.write(text, interval=0.04)
        return f"✅ Напечатал: {text[:40]}"
    except ImportError:
        return "❌ pip install pyautogui"
    except Exception as e:
        return f"❌ {e}"

def pc_click(button="left", double=False):
    try:
        import pyautogui
        if double:
            pyautogui.doubleClick()
        elif button == "right":
            pyautogui.rightClick()
        else:
            pyautogui.click()
        return f"✅ Клик ({button})"
    except Exception as e:
        return f"❌ {e}"

def pc_scroll(direction="down", amount=5):
    try:
        import pyautogui
        pyautogui.scroll(-amount if direction=="down" else amount)
        return f"✅ Прокрутка {direction}"
    except Exception as e:
        return f"❌ {e}"

def pc_volume(action):
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
    except Exception:
        subprocess.run('powershell -c "(New-Object -com WScript.Shell).SendKeys([char]173)"', shell=True)
        return "✅ Громкость изменена"

def pc_search_web(query):
    import urllib.parse
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"✅ Ищу: {query}"

def pc_weather(city="Amsterdam"):
    try:
        import urllib.request
        with urllib.request.urlopen(f"https://wttr.in/{city}?format=3", timeout=6) as r:
            return "🌤️ " + r.read().decode().strip()
    except Exception as e:
        return f"❌ Погода: {e}"

def pc_time():
    n = datetime.datetime.now()
    days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
    return f"🕐 {n.strftime('%H:%M')} | {days[n.weekday()]} {n.strftime('%d.%m.%Y')}"

def pc_shell(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=15, encoding="utf-8", errors="replace")
        out = (r.stdout + r.stderr).strip()[:500]
        return f"✅ {out}" if out else "✅ Готово"
    except Exception as e:
        return f"❌ {e}"

# ── TELEGRAM УПРАВЛЕНИЕ ──────────────────────────────────────
def tg_open():
    """Открыть Telegram"""
    try:
        subprocess.Popen("telegram", shell=True)
        return "✅ Telegram открывается"
    except:
        # Попробовать через AppData
        tg_paths = [
            os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Telegram Desktop\Telegram.exe"),
            r"C:\Program Files\Telegram Desktop\Telegram.exe",
        ]
        for p in tg_paths:
            if os.path.exists(p):
                subprocess.Popen(f'"{p}"')
                return "✅ Telegram открыт"
        return "⚠️ Telegram не найден. Установи с telegram.org"

def tg_send_message(contact, message):
    """Отправить сообщение в Telegram через URL схему"""
    import urllib.parse
    # Открыть Telegram с контактом (работает если Telegram установлен)
    if contact.startswith("@"):
        url = f"tg://resolve?domain={contact.lstrip('@')}&text={urllib.parse.quote(message)}"
    else:
        url = f"tg://resolve?domain={urllib.parse.quote(contact)}&text={urllib.parse.quote(message)}"
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"✅ Открываю чат с {contact}: {message[:30]}..."

def tg_open_chat(contact):
    """Открыть чат с контактом"""
    import urllib.parse
    if contact.startswith("+"):
        url = f"tg://resolve?phone={contact.lstrip('+')}"
    else:
        url = f"tg://resolve?domain={contact.lstrip('@')}"
    subprocess.Popen(f'start "" "{url}"', shell=True)
    return f"✅ Открываю чат: {contact}"

def pc_move_mouse(x, y):
    try:
        import pyautogui
        pyautogui.moveTo(x, y, duration=0.3)
        return f"✅ Мышь → ({x}, {y})"
    except Exception as e:
        return f"❌ {e}"

# ══════════════════════════════════════════════════════════════
#  AI РОУТЕР — понимает команду и выбирает действие
# ══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """\
Ты AI агент управления компьютером. На команду пользователя отвечай ТОЛЬКО JSON.
Доступные действия:
{"action":"open_app","app":"chrome|firefox|telegram|notepad|calc|explorer|word|excel|cmd|paint|taskmgr|spotify|vlc|edge"}
{"action":"close_app","app":"название"}
{"action":"screenshot"}
{"action":"key","key":"enter|escape|tab|space|f5|f11|delete|backspace|up|down|left|right|home|end|pageup|pagedown"}
{"action":"hotkey","keys":"ctrl+c|ctrl+v|ctrl+z|ctrl+s|ctrl+a|ctrl+w|ctrl+t|ctrl+f|alt+f4|alt+tab|win+d|win+l|win+e"}
{"action":"type","text":"текст"}
{"action":"click","button":"left|right","double":false}
{"action":"scroll","direction":"up|down","amount":5}
{"action":"volume","cmd":"громче|тише|выкл"}
{"action":"search","query":"запрос"}
{"action":"weather","city":"Amsterdam"}
{"action":"time"}
{"action":"shell","command":"cmd команда"}
{"action":"telegram","cmd":"open"} — открыть Telegram
{"action":"telegram","cmd":"send","contact":"@username","message":"текст"} — отправить сообщение
{"action":"telegram","cmd":"chat","contact":"@username"} — открыть чат
{"action":"chat","reply":"ответ"}
Отвечай ТОЛЬКО JSON без лишнего текста!
"""

def ai_route(text):
    """Локальные паттерны + AI fallback"""
    t = text.lower().strip()

    # ВРЕМЯ
    if any(w in t for w in ["который час","сколько времени","время","clock","часы","скажи время"]):
        return {"action":"time"}

    # СКРИНШОТ
    if any(w in t for w in ["скриншот","screenshot","снимок экрана","сфотографируй"]):
        return {"action":"screenshot"}

    # ПОГОДА
    if any(w in t for w in ["погода","weather","температура","градус"]):
        city = "Amsterdam"
        for c in ["rotterdam","amsterdam","moscow","москва","utrecht","eindhoven"]:
            if c in t: city = c.title(); break
        return {"action":"weather","city":city}

    # ОТКРЫТЬ
    if any(w in t for w in ["открой","запусти","включи","launch","start","open","run","запустить","открыть"]):
        for app in APP_MAP:
            if app in t: return {"action":"open_app","app":app}

    # ЗАКРЫТЬ
    if any(w in t for w in ["закрой","закрыть","close","kill","выключи","завершить","выйди"]):
        for app in APP_MAP:
            if app in t: return {"action":"close_app","app":app}
        return {"action":"hotkey","keys":"alt+f4"}

    # ГОРЯЧИЕ КЛАВИШИ
    hk_list = [
        (["скопируй","копировать","ctrl+c","ctrl c"],          "ctrl+c"),
        (["вставь","вставить","ctrl+v","ctrl v"],               "ctrl+v"),
        (["отмени","отменить","ctrl+z","ctrl z"],               "ctrl+z"),
        (["повтори","ctrl+y","ctrl y"],                         "ctrl+y"),
        (["сохрани","сохранить","ctrl+s","ctrl s"],             "ctrl+s"),
        (["выдели все","выдели всё","ctrl+a","ctrl a"],         "ctrl+a"),
        (["закрой вкладку","ctrl+w","ctrl w"],                  "ctrl+w"),
        (["новая вкладка","ctrl+t","ctrl t"],                   "ctrl+t"),
        (["найди на странице","ctrl+f","ctrl f"],               "ctrl+f"),
        (["обнови","обновить страницу","ctrl+r"],               "ctrl+r"),
        (["закрой окно","закрыть программу","alt+f4","alt f4"], "alt+f4"),
        (["переключи окно","alt+tab","alt tab"],                "alt+tab"),
        (["рабочий стол","свернуть всё","win+d","win d"],       "win+d"),
        (["заблокируй","блокировка","win+l","win l"],           "win+l"),
        (["проводник","win+e","win e"],                         "win+e"),
        (["диспетчер","ctrl+alt+delete","ctrl alt del"],        "ctrl+alt+delete"),
        (["увеличь масштаб","ctrl+plus","ctrl +"],              "ctrl+="),
        (["уменьши масштаб","ctrl+minus","ctrl -"],             "ctrl+-"),
        (["printscreen","prtsc","снимок клавишей"],             "printscreen"),
    ]
    for words, keys in hk_list:
        if any(w in t for w in words):
            return {"action":"hotkey","keys":keys}

    # ОДИНОЧНЫЕ КЛАВИШИ
    key_list = [
        (["нажми enter","нажать enter","энтер","ввод","подтверди"],  "enter"),
        (["нажми esc","escape","эскейп","нажать escape"],            "escape"),
        (["нажми tab","tab","таб"],                                   "tab"),
        (["нажми delete","удали","delete"],                           "delete"),
        (["нажми backspace","стереть","backspace"],                   "backspace"),
        (["нажми f5","обнови","f5"],                                  "f5"),
        (["нажми f11","полный экран","f11"],                          "f11"),
        (["пробел","нажми space","space"],                            "space"),
        (["стрелка вверх","нажми вверх"],                             "up"),
        (["стрелка вниз","нажми вниз"],                               "down"),
        (["стрелка влево","нажми влево"],                             "left"),
        (["стрелка вправо","нажми вправо"],                           "right"),
    ]
    for words, key in key_list:
        if any(w in t for w in words):
            return {"action":"key","key":key}

    # НАПЕЧАТАТЬ
    m = re.search(r"(?:напечатай|напиши|введи|набери|type)\s+(.+)", t)
    if m: return {"action":"type","text":m.group(1).strip()}

    # КЛИК МЫШЬЮ
    if any(w in t for w in ["кликни","клик","нажми мышью"]):
        double = "двойной" in t or "double" in t
        right  = "правой" in t or "right" in t
        return {"action":"click","button":"right" if right else "left","double":double}

    # ПРОКРУТКА
    if any(w in t for w in ["прокрути","scroll","листай","мотай"]):
        direction = "down" if any(w in t for w in ["вниз","down"]) else "up"
        return {"action":"scroll","direction":direction,"amount":5}

    # ПОИСК
    if any(w in t for w in ["найди","поищи","загугли","поиск","search","google","погугли"]):
        q = t
        for w in ["найди","поищи","загугли","поиск","search","google","погугли","в интернете","онлайн"]:
            q = q.replace(w,"").strip()
        if q: return {"action":"search","query":q}

    # ГРОМКОСТЬ
    if any(w in t for w in ["громкость","volume","тише","громче","без звука","mute"]):
        return {"action":"volume","cmd":t}

    # TELEGRAM КОМАНДЫ
    tg_words = ["телеграм","telegram","тг","тelegram"]
    if any(w in t for w in tg_words):
        # Открыть Telegram
        if any(w in t for w in ["открой","запусти","включи","open"]):
            return {"action":"telegram","cmd":"open"}
        # Написать сообщение: "напиши в телеграм @user привет"
        m = re.search(r"(?:напиши|отправь|пошли|send)\s+(?:в\s+)?(?:телеграм|telegram|тг)\s+(@?\w+)\s+(.+)", t)
        if m:
            return {"action":"telegram","cmd":"send","contact":m.group(1),"message":m.group(2)}
        # Открыть чат: "открой чат @user в телеграме"
        m2 = re.search(r"(?:открой|open)\s+(?:чат\s+)?(@\w+|\+\d+)", t)
        if m2:
            return {"action":"telegram","cmd":"chat","contact":m2.group(1)}
        # Просто открыть
        return {"action":"telegram","cmd":"open"}

    # ВЫКЛЮЧЕНИЕ / ПЕРЕЗАГРУЗКА
    if any(w in t for w in ["перезагрузи","перезагрузить","restart"]):
        return {"action":"shell","command":"shutdown /r /t 30"}
    if any(w in t for w in ["выключи компьютер","выключить пк","shutdown"]):
        return {"action":"shell","command":"shutdown /s /t 30"}
    if any(w in t for w in ["отмени выключение","отмени перезагрузку"]):
        return {"action":"shell","command":"shutdown /a"}

    # ── AI (если есть ключ) ───────────────────────────────────
    for key_name, api_key in [("gemini", GEMINI_KEY), ("gpt", GPT_KEY)]:
        if not api_key: continue
        try:
            import urllib.request
            if key_name == "gemini":
                url = (f"https://generativelanguage.googleapis.com/v1beta/"
                       f"models/gemini-2.0-flash:generateContent?key={api_key}")
                body = json.dumps({"contents":[{"parts":[{
                    "text":f"{SYSTEM_PROMPT}\nКоманда: {text}"}]}]}).encode()
                req = urllib.request.Request(url, data=body,
                      headers={"Content-Type":"application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=8) as r:
                    d = json.loads(r.read())
                raw = d["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                url = "https://api.openai.com/v1/chat/completions"
                body = json.dumps({"model":"gpt-4o-mini","max_tokens":150,
                    "messages":[{"role":"system","content":SYSTEM_PROMPT},
                                {"role":"user","content":text}]}).encode()
                req = urllib.request.Request(url, data=body,
                      headers={"Content-Type":"application/json",
                               "Authorization":f"Bearer {api_key}"}, method="POST")
                with urllib.request.urlopen(req, timeout=8) as r:
                    d = json.loads(r.read())
                raw = d["choices"][0]["message"]["content"].strip()
            raw = re.sub(r"```json\s*|```","",raw).strip()
            return json.loads(raw)
        except Exception:
            continue

    return {"action":"chat",
            "reply":(f"Не понял: «{text}»\n"
                     "Попробуй: открой chrome · скриншот · который час · ctrl+c · "
                     "найди рецепт · закрой telegram · нажми enter")}

def execute(cmd):
    a = cmd.get("action","chat")
    try:
        if   a == "open_app":   return pc_open(cmd.get("app",""))
        elif a == "close_app":  return pc_close(cmd.get("app",""))
        elif a == "screenshot": return pc_screenshot()
        elif a == "key":        return pc_key(cmd.get("key",""))
        elif a == "hotkey":     return pc_hotkey(cmd.get("keys",""))
        elif a == "type":       return pc_type(cmd.get("text",""))
        elif a == "click":      return pc_click(cmd.get("button","left"), cmd.get("double",False))
        elif a == "scroll":     return pc_scroll(cmd.get("direction","down"), cmd.get("amount",5))
        elif a == "volume":     return pc_volume(cmd.get("cmd",""))
        elif a == "search":     return pc_search_web(cmd.get("query",""))
        elif a == "weather":    return pc_weather(cmd.get("city","Amsterdam"))
        elif a == "time":       return pc_time()
        elif a == "shell":      return pc_shell(cmd.get("command",""))
        elif a == "telegram":
            sub = cmd.get("cmd","open")
            if sub == "send":
                return tg_send_message(cmd.get("contact",""), cmd.get("message",""))
            elif sub == "chat":
                return tg_open_chat(cmd.get("contact",""))
            else:
                return tg_open()
        elif a == "chat":       return cmd.get("reply","...")
        else: return f"❓ {a}"
    except Exception as e:
        return f"❌ {e}"

# ══════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ ИНТЕРФЕЙС
# ══════════════════════════════════════════════════════════════
class AgentPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Agent Manager — AI Agent")
        self.geometry("820x620")
        self.configure(bg=BG)
        self.minsize(700, 500)

        self._voice_on  = False
        self._speak_q   = queue.Queue()
        self._engine_var = tk.StringVar(value="gemini")
        self._status_var = tk.StringVar(value="Готов")

        self._build_ui()
        self._tts_start()
        self._show_startup()

    # ── BUILD UI ──────────────────────────────────────────────
    def _build_ui(self):
        # ── HEADER ────────────────────────────────────────────
        header = tk.Frame(self, bg="#12122a", pady=0)
        header.pack(fill="x")

        # Logo + title
        title_f = tk.Frame(header, bg="#12122a")
        title_f.pack(side="left", padx=14, pady=10)
        tk.Label(title_f, text="🤖", bg="#12122a",
                 font=("Segoe UI Emoji",22)).pack(side="left")
        tk.Label(title_f, text=" AI Agent Manager",
                 bg="#12122a", fg=WHITE,
                 font=("Segoe UI",16,"bold")).pack(side="left")

        tk.Label(header, text="AI Agent System",
                 bg="#12122a", fg=GOLD,
                 font=("Segoe UI",9)).pack(side="right", padx=14)

        # ── TABS ──────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Tab.TNotebook", background=BG2, borderwidth=0)
        style.configure("Tab.TNotebook.Tab",
                        background=BG2, foreground=MUTED,
                        padding=[14,6], font=("Segoe UI",10))
        style.map("Tab.TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", WHITE)])

        self._nb = ttk.Notebook(self, style="Tab.TNotebook")
        self._nb.pack(fill="both", expand=True, padx=0, pady=0)

        # Tab frames
        self._tab_launch = tk.Frame(self._nb, bg=BG)
        self._tab_voice  = tk.Frame(self._nb, bg=BG)
        self._tab_keys   = tk.Frame(self._nb, bg=BG)
        self._tab_diag   = tk.Frame(self._nb, bg=BG)
        self._tab_set    = tk.Frame(self._nb, bg=BG)

        self._nb.add(self._tab_launch, text="  🚀 Launch  ")
        self._nb.add(self._tab_voice,  text="  🎙️ Voice  ")
        self._nb.add(self._tab_keys,   text="  🔑 Keys  ")
        self._nb.add(self._tab_diag,   text="  🔧 Diagnostics  ")
        self._tab_tg = tk.Frame(self._nb, bg=BG)
        self._nb.add(self._tab_set,    text="  ⚙️ Settings  ")
        self._nb.add(self._tab_tg,     text="  💬 Telegram  ")

        self._build_launch()
        self._build_voice()
        self._build_keys()
        self._build_diag()
        self._build_settings()
        self._build_telegram()

    # ── TAB: LAUNCH ───────────────────────────────────────────
    def _build_launch(self):
        f = self._tab_launch

        # Engine selector
        eng_f = tk.LabelFrame(f, text=" Select AI Engine ",
                               bg=BG, fg=MUTED,
                               font=("Segoe UI",10),
                               bd=1, relief="solid")
        eng_f.pack(fill="x", padx=14, pady=(12,6))

        engines = [
            ("gemini", "🟢  Google Gemini",  "FREE  ⚡ 1500 req/day", GREEN),
            ("gpt",    "🔵  ChatGPT (OpenAI)","Paid  💳 $5 free",     ACCENT2),
            ("claude", "🟣  Claude (Anthropic)","Paid  💳",            "#9333ea"),
        ]
        for val, label, note, color in engines:
            row = tk.Frame(eng_f, bg=BG2, cursor="hand2")
            row.pack(fill="x", padx=8, pady=3)
            rb = tk.Radiobutton(row, variable=self._engine_var, value=val,
                                bg=BG2, activebackground=BG2,
                                selectcolor=CARD, cursor="hand2")
            rb.pack(side="left", padx=6, pady=8)
            tk.Label(row, text=label, bg=BG2, fg=color,
                     font=("Segoe UI",11,"bold")).pack(side="left")
            tk.Label(row, text=note, bg=BG2, fg=MUTED,
                     font=("Segoe UI",9)).pack(side="right", padx=12)
            row.bind("<Button-1>", lambda e, v=val: self._engine_var.set(v))

        # Status
        status_f = tk.Frame(f, bg=BG)
        status_f.pack(fill="x", padx=14, pady=4)
        self._dot_lbl = tk.Label(status_f, text="⚫", bg=BG, font=("Segoe UI",14))
        self._dot_lbl.pack(side="left")
        tk.Label(status_f, textvariable=self._status_var,
                 bg=BG, fg=TEXT, font=("Segoe UI",10)).pack(side="left", padx=6)

        # Control buttons
        btn_f = tk.Frame(f, bg=BG)
        btn_f.pack(fill="x", padx=14, pady=6)
        tk.Button(btn_f, text="▶  Start Agent",
                  command=self._start_agent,
                  bg=GREEN, fg="#000",
                  font=("Segoe UI",11,"bold"),
                  relief="flat", padx=20, pady=10,
                  cursor="hand2").pack(side="left", padx=(0,8))
        tk.Button(btn_f, text="⏹  Stop Agent",
                  command=self._stop_agent,
                  bg=RED, fg=WHITE,
                  font=("Segoe UI",11,"bold"),
                  relief="flat", padx=20, pady=10,
                  cursor="hand2").pack(side="left")

        # Chat log
        tk.Label(f, text="  Live Log:", bg=BG, fg=MUTED,
                 font=("Segoe UI",9)).pack(anchor="w", padx=14)
        self._log = scrolledtext.ScrolledText(
            f, bg="#0d0d1a", fg=TEXT,
            font=("Cascadia Code",9), wrap="word",
            state="disabled", relief="flat", bd=0, height=10)
        self._log.pack(fill="both", expand=True, padx=14, pady=(2,6))
        for tag, fg, bold in [
            ("you","#7dd3fc",True),("bot",GREEN,True),
            ("sys",GOLD,False),("err",RED,True),
            ("act","#c084fc",False),("msg",TEXT,False)]:
            self._log.tag_config(tag, foreground=fg,
                font=("Cascadia Code",9,"bold" if bold else "normal"))

        # Input
        inp_f = tk.Frame(f, bg=BG)
        inp_f.pack(fill="x", padx=14, pady=(0,8))
        self._inp = tk.Entry(inp_f, bg=CARD, fg=TEXT,
                              font=("Segoe UI",11), relief="flat",
                              insertbackground=TEXT, bd=6)
        self._inp.pack(side="left", fill="x", expand=True, ipady=7)
        self._inp.bind("<Return>",   lambda e: self._send())
        self._inp.bind("<KP_Enter>", lambda e: self._send())
        self._inp.focus()
        tk.Button(inp_f, text="Send ↵",
                  command=self._send,
                  bg=ACCENT, fg=WHITE,
                  font=("Segoe UI",11,"bold"),
                  relief="flat", padx=14, pady=7,
                  cursor="hand2").pack(side="left", padx=(6,0))

        # Quick commands
        quick_f = tk.Frame(f, bg=BG)
        quick_f.pack(fill="x", padx=14, pady=(0,6))
        tk.Label(quick_f, text="Быстро:", bg=BG, fg=MUTED,
                 font=("Segoe UI",9)).pack(side="left")
        for lbl, cmd in [
            ("📸","скриншот"),("🕐","время"),("🌤️","погода"),
            ("🌐 Chrome","открой chrome"),("📝","открой блокнот"),
            ("📋 Копировать","ctrl+c"),("📋 Вставить","ctrl+v"),
            ("🗑️","ctrl+z"),("❌ Окно","alt+f4"),
        ]:
            tk.Button(quick_f, text=lbl,
                      command=lambda c=cmd: self._quick(c),
                      bg=CARD, fg=TEXT,
                      font=("Segoe UI",9), relief="flat",
                      padx=7, pady=3, cursor="hand2"
                      ).pack(side="left", padx=2)

    # ── TAB: VOICE ────────────────────────────────────────────
    def _build_voice(self):
        f = self._tab_voice

        tk.Label(f, text="🎙️  Голосовое управление",
                 bg=BG, fg=WHITE,
                 font=("Segoe UI",14,"bold")).pack(pady=(18,4))
        tk.Label(f, text='Скажи "Агент [команда]" — агент выполнит на ПК',
                 bg=BG, fg=MUTED, font=("Segoe UI",10)).pack()

        # Wake word display
        ww_f = tk.Frame(f, bg=CARD)
        ww_f.pack(padx=30, pady=12, fill="x")
        tk.Label(ww_f, text="Wake word:", bg=CARD, fg=MUTED,
                 font=("Segoe UI",10)).pack(side="left", padx=12, pady=8)
        tk.Label(ww_f, text='"Агент"  /  "Agent"',
                 bg=CARD, fg=GOLD,
                 font=("Segoe UI",13,"bold")).pack(side="left")

        # Voice status
        self._v_dot   = tk.Label(f, text="⚫", bg=BG, font=("Segoe UI",20))
        self._v_dot.pack(pady=6)
        self._v_status = tk.Label(f, text="Голос выключен",
                                   bg=BG, fg=MUTED, font=("Segoe UI",11))
        self._v_status.pack()

        # Buttons
        vbtn_f = tk.Frame(f, bg=BG)
        vbtn_f.pack(pady=12)
        self._vbtn = tk.Button(vbtn_f, text="🎙️  Start Voice",
                                command=self._voice_toggle,
                                bg=GREEN, fg="#000",
                                font=("Segoe UI",11,"bold"),
                                relief="flat", padx=20, pady=10,
                                cursor="hand2")
        self._vbtn.pack(side="left", padx=4)
        tk.Button(vbtn_f, text="🎤 Тест микрофона",
                  command=lambda: threading.Thread(
                      target=self._mic_test, daemon=True).start(),
                  bg=GOLD, fg="#000",
                  font=("Segoe UI",11,"bold"),
                  relief="flat", padx=16, pady=10,
                  cursor="hand2").pack(side="left", padx=4)

        # Language
        lang_f = tk.Frame(f, bg=BG)
        lang_f.pack(pady=4)
        tk.Label(lang_f, text="Язык:", bg=BG, fg=MUTED,
                 font=("Segoe UI",10)).pack(side="left")
        self._lang = tk.StringVar(value="ru-RU")
        for lbl, val in [("🇷🇺 RU","ru-RU"),("🇬🇧 EN","en-US"),("🇳🇱 NL","nl-NL")]:
            tk.Radiobutton(lang_f, text=lbl, variable=self._lang, value=val,
                           bg=BG, fg=TEXT, selectcolor=CARD,
                           activebackground=BG,
                           font=("Segoe UI",10)).pack(side="left", padx=6)

        # Examples
        ex_f = tk.LabelFrame(f, text=" Примеры команд ",
                              bg=BG, fg=MUTED, font=("Segoe UI",9),
                              bd=1, relief="solid")
        ex_f.pack(fill="x", padx=30, pady=10)
        examples = [
            '"Агент, открой хром"    → Chrome открывается',
            '"Агент, скриншот"       → файл сохраняется',
            '"Агент, ctrl+c"         → копирует',
            '"Агент, который час"    → говорит время',
            '"Агент, закрой телеграм"→ Telegram закрывается',
            '"Агент, найди погода Rotterdam" → открывает Google',
        ]
        for ex in examples:
            tk.Label(ex_f, text=f"  {ex}", bg=BG, fg=TEXT,
                     font=("Cascadia Code",9), anchor="w").pack(fill="x", padx=8, pady=1)

    # ── TAB: KEYS ─────────────────────────────────────────────
    def _build_keys(self):
        f = self._tab_keys
        tk.Label(f, text="🔑  API Ключи",
                 bg=BG, fg=WHITE, font=("Segoe UI",14,"bold")).pack(pady=(18,4))
        tk.Label(f, text="Ключи хранятся в файле .env",
                 bg=BG, fg=MUTED, font=("Segoe UI",10)).pack(pady=(0,12))

        self._key_vars = {}
        keys_info = [
            ("GEMINI_API_KEY",  "🟢 Google Gemini",   "aistudio.google.com",    GEMINI_KEY),
            ("OPENAI_API_KEY",  "🔵 OpenAI / ChatGPT", "platform.openai.com",    GPT_KEY),
            ("ANTHROPIC_API_KEY","🟣 Claude (Anthropic)","console.anthropic.com", CLAUDE_KEY),
        ]
        for env_key, label, url, current in keys_info:
            row = tk.LabelFrame(f, text=f" {label} ",
                                bg=BG2, fg=TEXT,
                                font=("Segoe UI",10,"bold"),
                                bd=1, relief="solid")
            row.pack(fill="x", padx=20, pady=6)
            # URL
            tk.Label(row, text=f"Получить: {url}",
                     bg=BG2, fg=ACCENT2,
                     font=("Segoe UI",9)).pack(anchor="w", padx=10, pady=(4,0))
            # Entry
            ef = tk.Frame(row, bg=BG2)
            ef.pack(fill="x", padx=10, pady=6)
            var = tk.StringVar(value=current if current else "")
            self._key_vars[env_key] = var
            status = "✅ Установлен" if current else "❌ Не установлен"
            color  = GREEN if current else RED
            tk.Label(ef, text=status, bg=BG2, fg=color,
                     font=("Segoe UI",9)).pack(side="right")
            ent = tk.Entry(ef, textvariable=var, bg=CARD, fg=TEXT,
                           font=("Segoe UI",10), relief="flat",
                           show="*", bd=4, width=40)
            ent.pack(side="left", fill="x", expand=True, ipady=4)

        tk.Button(f, text="💾  Сохранить ключи",
                  command=self._save_keys,
                  bg=GREEN, fg="#000",
                  font=("Segoe UI",11,"bold"),
                  relief="flat", padx=20, pady=8,
                  cursor="hand2").pack(pady=12)

    # ── TAB: DIAGNOSTICS ──────────────────────────────────────
    def _build_diag(self):
        f = self._tab_diag
        tk.Label(f, text="🔧  Диагностика системы",
                 bg=BG, fg=WHITE, font=("Segoe UI",14,"bold")).pack(pady=(18,4))

        btn_f = tk.Frame(f, bg=BG)
        btn_f.pack(pady=8)
        for lbl, cmd in [
            ("🔍 Полная диагностика",  self._run_full_diag),
            ("🎤 Тест микрофона",      lambda: threading.Thread(target=self._mic_test, daemon=True).start()),
            ("🗑️ Очистить",            self._clear_diag),
        ]:
            tk.Button(btn_f, text=lbl, command=cmd,
                      bg=CARD, fg=TEXT,
                      font=("Segoe UI",10), relief="flat",
                      padx=12, pady=7, cursor="hand2"
                      ).pack(side="left", padx=4)

        self._diag = scrolledtext.ScrolledText(
            f, bg="#0d0d1a", fg=TEXT,
            font=("Cascadia Code",9), wrap="word",
            state="disabled", relief="flat", bd=0)
        self._diag.pack(fill="both", expand=True, padx=14, pady=6)
        for tag, fg in [("ok",GREEN),("err",RED),("warn",GOLD),("info",ACCENT2)]:
            self._diag.tag_config(tag, foreground=fg)

    # ── TAB: SETTINGS ─────────────────────────────────────────
    def _build_settings(self):
        f = self._tab_settings = self._tab_set
        tk.Label(f, text="⚙️  Настройки",
                 bg=BG, fg=WHITE, font=("Segoe UI",14,"bold")).pack(pady=(18,8))

        settings_items = [
            ("Автозапуск при включении ПК", "autostart"),
            ("Автовключение голоса при старте", "auto_voice"),
            ("Голосовые ответы (TTS)", "tts_enabled"),
            ("Показывать уведомления", "notifications"),
        ]
        self._settings_vars = {}
        for label, key in settings_items:
            var = tk.BooleanVar(value=True)
            self._settings_vars[key] = var
            row = tk.Frame(f, bg=BG2)
            row.pack(fill="x", padx=20, pady=4)
            tk.Label(row, text=label, bg=BG2, fg=TEXT,
                     font=("Segoe UI",10)).pack(side="left", padx=12, pady=8)
            tk.Checkbutton(row, variable=var, bg=BG2,
                           activebackground=BG2,
                           selectcolor=ACCENT,
                           cursor="hand2").pack(side="right", padx=12)

        tk.Button(f, text="💾 Сохранить настройки",
                  command=lambda: self._log_add("sys","✅ Настройки сохранены"),
                  bg=GREEN, fg="#000",
                  font=("Segoe UI",11,"bold"),
                  relief="flat", padx=20, pady=8,
                  cursor="hand2").pack(pady=16)

        # About
        about = tk.LabelFrame(f, text=" О программе ",
                               bg=BG2, fg=MUTED,
                               font=("Segoe UI",9), bd=1, relief="solid")
        about.pack(fill="x", padx=20, pady=8)
        for line in [
            "AI Desktop Agent PRO",
            "AI Agent System",
            "vova-products.com",
            "Версия: 3.0 | Реальное управление ПК голосом и текстом",
        ]:
            tk.Label(about, text=line, bg=BG2, fg=TEXT,
                     font=("Segoe UI",9)).pack(anchor="w", padx=12, pady=1)

    # ── HELPERS ───────────────────────────────────────────────
    def _log_add(self, role, text):
        try:
            self._log.config(state="normal")
            labels = {"you":"▶ Ты","bot":"🤖","sys":"⚙","err":"❌","act":"⚡"}
            self._log.insert("end", f"{labels.get(role,role)}: ", role)
            self._log.insert("end", text+"\n", "msg")
            self._log.see("end")
            self._log.config(state="disabled")
        except: pass

    def _diag_add(self, text, tag="info"):
        try:
            self._diag.config(state="normal")
            self._diag.insert("end", text+"\n", tag)
            self._diag.see("end")
            self._diag.config(state="disabled")
        except: pass

    def _set_status(self, text, dot="⚫"):
        try:
            self._status_var.set(text)
            self._dot_lbl.config(text=dot)
        except: pass

    def _clear_diag(self):
        try:
            self._diag.config(state="normal")
            self._diag.delete("1.0","end")
            self._diag.config(state="disabled")
        except: pass

    def _quick(self, cmd):
        self._inp.delete(0,"end")
        self._inp.insert(0, cmd)
        self._send()

    def _show_startup(self):
        self._log_add("sys","🤖 AI Desktop Agent PRO запущен!")
        if GEMINI_KEY:
            self._log_add("sys","✅ Gemini API ключ найден")
        elif GPT_KEY:
            self._log_add("sys","✅ OpenAI API ключ найден")
        else:
            self._log_add("err","⚠️ API ключ не найден — работают локальные команды")
            self._log_add("sys","Добавь ключ во вкладке 🔑 Keys")
        self._log_add("sys",'Попробуй: "открой chrome" · "скриншот" · "ctrl+c"')

    # ── AGENT START/STOP ──────────────────────────────────────
    def _start_agent(self):
        self._set_status("Агент запущен ✅", "🟢")
        self._log_add("sys","▶ Агент запущен — пиши или говори команды")

    def _stop_agent(self):
        if self._voice_on:
            self._voice_on = False
        self._set_status("Агент остановлен", "⚫")
        self._log_add("sys","⏹ Агент остановлен")

    # ── SEND / PROCESS ────────────────────────────────────────
    def _send(self):
        text = self._inp.get().strip()
        if not text: return
        self._inp.delete(0,"end")
        self._log_add("you", text)
        self._set_status("🔵 Выполняю...", "🔵")
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text):
        try:
            cmd    = ai_route(text)
            action = cmd.get("action","chat")
            if action != "chat":
                self.after(0, lambda a=action:
                    self._log_add("act", f"Действие: {a}"))
            result = execute(cmd)
            self.after(0, lambda r=result: self._log_add("bot", r))
            self.after(0, lambda: self._set_status("Готов ✅", "🟢"))
            self._speak(result)
        except Exception as e:
            self.after(0, lambda: self._log_add("err", str(e)))
            self.after(0, lambda: self._set_status("Ошибка", "🔴"))

    # ── SAVE KEYS ─────────────────────────────────────────────
    def _save_keys(self):
        lines = []
        for k, var in self._key_vars.items():
            v = var.get().strip()
            if v: lines.append(f'{k}="{v}"')
        env_path = AGENT_DIR / ".env"
        # Keep existing non-key lines
        existing = []
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if not any(line.startswith(k) for k in self._key_vars):
                    existing.append(line)
        all_lines = existing + lines
        env_path.write_text("\n".join(all_lines), encoding="utf-8")
        # Reload
        for k, var in self._key_vars.items():
            v = var.get().strip()
            if v: os.environ[k] = v
        global GEMINI_KEY, GPT_KEY, CLAUDE_KEY
        GEMINI_KEY = os.environ.get("GEMINI_API_KEY","")
        GPT_KEY    = os.environ.get("OPENAI_API_KEY","")
        CLAUDE_KEY = os.environ.get("ANTHROPIC_API_KEY","")
        self._log_add("sys","✅ Ключи сохранены в .env!")
        messagebox.showinfo("Сохранено","API ключи сохранены успешно!")

    # ── TTS ───────────────────────────────────────────────────
    def _tts_start(self):
        def worker():
            try:
                import pyttsx3
                e = pyttsx3.init()
                e.setProperty("rate",165)
                for v in e.getProperty("voices"):
                    if any(x in v.name.lower() for x in ["russian","irina","zira","elena"]):
                        e.setProperty("voice",v.id); break
                while True:
                    try:
                        t = self._speak_q.get(timeout=1)
                        e.say(t[:180]); e.runAndWait()
                    except queue.Empty: continue
            except: pass
        threading.Thread(target=worker, daemon=True).start()

    def _speak(self, text):
        clean = re.sub(r"[✅❌⚡🎙🤖⚙📸🌤🕐📋↩⚫🟢🔴🔵]","",text)
        clean = re.sub(r"\n"," ",clean).strip()
        try: self._speak_q.put_nowait(clean[:180])
        except: pass

    # ── VOICE ─────────────────────────────────────────────────
    def _voice_toggle(self):
        if self._voice_on:
            self._voice_on = False
            self._vbtn.config(text="🎙️  Start Voice", bg=GREEN, fg="#000")
            self._v_dot.config(text="⚫")
            self._v_status.config(text="Голос выключен", fg=MUTED)
            self._log_add("sys","🔇 Голос остановлен")
        else:
            self._voice_on = True
            self._vbtn.config(text="⏹  Stop Voice", bg=RED, fg=WHITE)
            threading.Thread(target=self._voice_loop, daemon=True).start()

    def _voice_loop(self):
        try:
            import speech_recognition as sr
            import sounddevice as sd
            import numpy as np

            rec  = sr.Recognizer()
            SR   = 16000
            WAKE = ["агент","agent","ассистент","assistant"]

            self.after(0, lambda: self._v_dot.config(text="🟢"))
            self.after(0, lambda: self._v_status.config(
                text='Слушаю... скажи "Агент [команда]"', fg=GREEN))
            self.after(0, lambda: self._log_add("sys",'🎙️ Голос активен — скажи "Агент [команда]"'))
            self._speak("Готов. Скажи Агент.")

            def record(sec=5):
                audio = sd.rec(int(sec*SR), samplerate=SR, channels=1, dtype="int16")
                sd.wait()
                buf = io.BytesIO()
                with wave.open(buf,"wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2)
                    wf.setframerate(SR); wf.writeframes(audio.tobytes())
                buf.seek(0)
                return sr.AudioData(buf.read(), SR, 2)

            def recognize(aud):
                lang = self._lang.get()
                for lng in [lang,"ru-RU","en-US","nl-NL"]:
                    try: return rec.recognize_google(aud, language=lng)
                    except sr.UnknownValueError: continue
                    except: return ""
                return ""

            while self._voice_on:
                aud  = record(5)
                text = recognize(aud)
                if not text: continue

                tl = text.lower()
                self.after(0, lambda t=text:
                    self._v_status.config(text=f'Слышу: "{t}"', fg=ACCENT2))

                if not any(w in tl for w in WAKE): continue

                cmd_text = tl
                for w in sorted(WAKE, key=len, reverse=True):
                    cmd_text = cmd_text.replace(w,"").strip(" ,!?.")

                if not cmd_text:
                    self._speak("Слушаю")
                    self.after(0, lambda: self._v_status.config(
                        text="Говори команду...", fg=GOLD))
                    aud2 = record(7)
                    cmd_text = recognize(aud2)

                if cmd_text:
                    self.after(0, lambda c=cmd_text:
                        self._log_add("you", f"🎙️ {c}"))
                    self.after(0, lambda: self._set_status("🔵 Выполняю...", "🔵"))
                    threading.Thread(
                        target=self._process, args=(cmd_text,),
                        daemon=True).start()

        except ImportError as e:
            self.after(0, lambda: self._log_add("err",
                f"Установи библиотеки! Запусти install_all.bat\n{e}"))
        except Exception as e:
            self.after(0, lambda: self._log_add("err", f"Голос: {e}"))
        finally:
            self._voice_on = False
            self.after(0, lambda: self._vbtn.config(
                text="🎙️  Start Voice", bg=GREEN, fg="#000"))
            self.after(0, lambda: self._v_dot.config(text="⚫"))
            self.after(0, lambda: self._v_status.config(
                text="Голос выключен", fg=MUTED))

    # ── MIC TEST ──────────────────────────────────────────────
    def _mic_test(self):
        self._nb.select(self._tab_diag)
        def log(m, t="info"): self.after(0, lambda m=m,t=t: self._diag_add(m,t))
        log("━━━ ТЕСТ МИКРОФОНА ━━━","info")
        try:
            import sounddevice as sd, numpy as np
            devs = [d for d in sd.query_devices() if d["max_input_channels"]>0]
            if not devs:
                log("❌ Микрофоны не найдены!","err")
                log("Проверь: Пуск → Настройки → Система → Звук → Ввод","warn")
                return
            log(f"✅ Найдено {len(devs)} микрофон(ов):","ok")
            for d in devs[:4]: log(f"  🎙️ {d['name']}","info")
            default = sd.query_devices(kind="input")
            log(f"⭐ Активный: {default['name']}","ok")
            log("🔴 Говори 3 секунды СЕЙЧАС...","warn")
            audio = sd.rec(int(3*16000), samplerate=16000, channels=1, dtype="int16")
            sd.wait()
            vol = int(np.abs(audio).max())
            log(f"📊 Уровень: {vol}/32767","info")
            if   vol > 2000: log("✅ Сигнал отличный!","ok")
            elif vol > 300:  log("⚠️ Слабый сигнал — говори громче","warn")
            else:
                log("❌ Сигнал не обнаружен!","err")
                log("Исправь: Правая кнопка на значок звука → Параметры звука","warn")
                log("→ Ввод → выбери Microfoon (Realtek) как устройство по умолчанию","warn")
                return
            import speech_recognition as sr
            buf = io.BytesIO()
            with wave.open(buf,"wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2)
                wf.setframerate(16000); wf.writeframes(audio.tobytes())
            buf.seek(0)
            aud = sr.AudioData(buf.read(),16000,2)
            try:
                text = sr.Recognizer().recognize_google(aud, language="ru-RU")
                log(f'✅ Распознано: "{text}"',"ok")
                log("🎉 Микрофон работает!","ok")
            except sr.UnknownValueError:
                log("⚠️ Речь не распознана — говори чётче","warn")
            except Exception as e:
                log(f"❌ Нет интернета или ошибка: {e}","err")
        except ImportError:
            log("❌ Запусти install_all.bat от Администратора!","err")
        except Exception as e:
            log(f"❌ {e}","err")
        log("━━━━━━━━━━━━━━━━━━━━━━━━","info")

    # ── FULL DIAGNOSTICS ──────────────────────────────────────
    def _run_full_diag(self):
        self._clear_diag()
        threading.Thread(target=self._do_full_diag, daemon=True).start()

    def _do_full_diag(self):
        def log(m,t="info"): self.after(0, lambda m=m,t=t: self._diag_add(m,t))
        log("━━━ ПОЛНАЯ ДИАГНОСТИКА ━━━","info")
        modules = {
            "tkinter":           ("GUI интерфейс","ok"),
            "speech_recognition":("Распознавание голоса","warn"),
            "sounddevice":       ("Микрофон (нет PyAudio)","warn"),
            "pyttsx3":           ("Голосовой ответ TTS","warn"),
            "pyautogui":         ("Управление ПК","warn"),
            "PIL":               ("Скриншоты","warn"),
        }
        all_ok = True
        for mod,(name,_) in modules.items():
            try:
                __import__(mod)
                log(f"✅ {name}","ok")
            except ImportError:
                log(f"❌ {name} — pip install {mod}","err")
                all_ok = False
        log("","info")
        log(f"{'✅ Все модули в порядке!' if all_ok else '⚠️ Запусти install_all.bat'}",
            "ok" if all_ok else "warn")
        # API keys
        log("","info")
        log("── API Ключи ──","info")
        log(f"{'✅' if GEMINI_KEY else '❌'} Gemini: {'установлен' if GEMINI_KEY else 'не найден'}",
            "ok" if GEMINI_KEY else "err")
        log(f"{'✅' if GPT_KEY else '❌'} OpenAI: {'установлен' if GPT_KEY else 'не найден'}",
            "ok" if GPT_KEY else "err")
        log(f"{'✅' if CLAUDE_KEY else '❌'} Claude: {'установлен' if CLAUDE_KEY else 'не найден'}",
            "ok" if CLAUDE_KEY else "err")
        log("━━━━━━━━━━━━━━━━━━━━━━━━","info")

    def _build_telegram(self):
        f = self._tab_tg

        tk.Label(f, text="💬  Управление Telegram",
                 bg=BG, fg=WHITE, font=("Segoe UI",14,"bold")).pack(pady=(18,4))
        tk.Label(f, text="Открывай чаты и отправляй сообщения голосом или текстом",
                 bg=BG, fg=MUTED, font=("Segoe UI",10)).pack(pady=(0,12))

        # Quick actions
        quick_f = tk.LabelFrame(f, text=" Быстрые действия ",
                                 bg=BG2, fg=MUTED, font=("Segoe UI",9),
                                 bd=1, relief="solid")
        quick_f.pack(fill="x", padx=20, pady=6)

        btns = [
            ("📱 Открыть Telegram",    "открой телеграм"),
            ("❌ Закрыть Telegram",    "закрой телеграм"),
            ("🔇 Заглушить",           "ctrl+shift+m"),
        ]
        for lbl, cmd in btns:
            tk.Button(quick_f, text=lbl,
                      command=lambda c=cmd: self._quick_tg(c),
                      bg=CARD, fg=TEXT,
                      font=("Segoe UI",10), relief="flat",
                      padx=12, pady=7, cursor="hand2"
                      ).pack(side="left", padx=8, pady=8)

        # Send message form
        msg_f = tk.LabelFrame(f, text=" Написать сообщение ",
                               bg=BG2, fg=MUTED, font=("Segoe UI",9),
                               bd=1, relief="solid")
        msg_f.pack(fill="x", padx=20, pady=6)

        # Contact
        r1 = tk.Frame(msg_f, bg=BG2)
        r1.pack(fill="x", padx=10, pady=(8,2))
        tk.Label(r1, text="Контакт/username:", bg=BG2, fg=TEXT,
                 font=("Segoe UI",10), width=16).pack(side="left")
        self._tg_contact = tk.Entry(r1, bg=CARD, fg=TEXT,
                                     font=("Segoe UI",10), relief="flat", bd=4)
        self._tg_contact.insert(0, "@username")
        self._tg_contact.pack(side="left", fill="x", expand=True, ipady=4, padx=4)

        # Message
        r2 = tk.Frame(msg_f, bg=BG2)
        r2.pack(fill="x", padx=10, pady=4)
        tk.Label(r2, text="Сообщение:", bg=BG2, fg=TEXT,
                 font=("Segoe UI",10), width=16).pack(side="left")
        self._tg_msg = tk.Entry(r2, bg=CARD, fg=TEXT,
                                 font=("Segoe UI",10), relief="flat", bd=4)
        self._tg_msg.pack(side="left", fill="x", expand=True, ipady=4, padx=4)

        tk.Button(msg_f, text="📤  Отправить",
                  command=self._tg_send,
                  bg=ACCENT, fg=WHITE,
                  font=("Segoe UI",10,"bold"),
                  relief="flat", padx=16, pady=6,
                  cursor="hand2").pack(pady=8)

        # Voice examples
        ex_f = tk.LabelFrame(f, text=" Голосовые команды ",
                              bg=BG, fg=MUTED, font=("Segoe UI",9),
                              bd=1, relief="solid")
        ex_f.pack(fill="x", padx=20, pady=8)
        examples = [
            '"Агент, открой телеграм"              → Telegram открывается',
            '"Агент, закрой телеграм"              → Telegram закрывается',
            '"Агент, напиши в телеграм @user привет" → открывает чат с сообщением',
            '"Агент, открой чат @username"         → открывает конкретный чат',
        ]
        for ex in examples:
            tk.Label(ex_f, text=f"  {ex}", bg=BG, fg=TEXT,
                     font=("Cascadia Code",9), anchor="w").pack(fill="x", padx=8, pady=2)

    def _quick_tg(self, cmd):
        self._inp.delete(0,"end")
        self._inp.insert(0, cmd)
        self._nb.select(self._tab_launch)
        self._send()

    def _tg_send(self):
        contact = self._tg_contact.get().strip()
        message = self._tg_msg.get().strip()
        if not contact or not message:
            return
        result = tg_send_message(contact, message)
        self._log_add("bot", result)
        self._nb.select(self._tab_launch)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--autostart", action="store_true")
    args, _ = parser.parse_known_args()
    app = AgentPro()
    if args.autostart:
        app.after(2500, lambda: (
            app._start_agent(),
            app._voice_toggle()
        ))
    app.mainloop()
