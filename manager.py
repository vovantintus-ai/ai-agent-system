"""
AI Agent Manager v2
- Asks which engine (Gemini/Claude) on EVERY launch
- No autostart
- Live log
- Diagnostics with auto-fix hints
- Package installer
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import os, sys, subprocess, threading, importlib, time

BG     = "#1e1e2e"
CARD   = "#2a2a3e"
TEXT   = "#cdd6f4"
ACCENT = "#5865F2"
GREEN  = "#a6e3a1"
YELLOW = "#f9e2af"
RED    = "#f38ba8"
ORANGE = "#fab387"

AGENT_DIR = Path.home() / "ai-agent"
ENV_PATH  = AGENT_DIR / ".env"

# ── helpers ───────────────────────────────────────────────────────────────────

def load_env():
    d = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                d[k.strip()] = v.strip()
    return d

def save_env(d):
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text("\n".join(f"{k}={v}" for k, v in d.items()) + "\n", encoding="utf-8")

def pkg_ok(name):
    try: importlib.import_module(name); return True
    except ImportError: return False

def run_diag(provider="gemini"):
    env = load_env()
    res = []
    v = sys.version_info
    res.append((v.major==3 and v.minor>=10,
                f"Python {v.major}.{v.minor}.{v.micro}",
                "Need Python 3.10+  →  python.org/downloads"))
    res.append((ENV_PATH.exists(), f".env  →  {ENV_PATH}",
                "Run installer first"))
    res.append(((AGENT_DIR/"main.py").exists(), f"Agent files  →  {AGENT_DIR}",
                "Run installer first"))
    tg  = env.get("TELEGRAM_TOKEN","")
    uid = env.get("ALLOWED_USER_ID","")
    res.append((bool(tg and len(tg)>10), "Telegram Token",
                "Get from @BotFather  →  /mybots  →  Generate new token"))
    res.append((bool(uid and uid.isdigit()), f"Telegram User ID: {uid or '???'}",
                "Get from @userinfobot in Telegram"))
    if provider == "gemini":
        gm = env.get("GEMINI_API_KEY","")
        res.append((bool(gm and len(gm)>10), "Gemini API Key",
                    "Free key  →  aistudio.google.com/app/apikey"))
    elif provider == "gpt":
        ok = env.get("OPENAI_API_KEY","")
        res.append((bool(ok and len(ok)>10), "OpenAI API Key",
                    "Get key  →  platform.openai.com/api-keys"))
    elif provider == "ollama":
        import urllib.request
        try:
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
            ollama_ok = True
        except Exception:
            ollama_ok = False
        res.append((ollama_ok, "Ollama running at localhost:11434",
                    "Start Ollama app first!"))
        model = env.get("OLLAMA_MODEL", "gemma3:1b")
        res.append((True, f"Ollama model: {model}", ""))
    else:
        ak = env.get("ANTHROPIC_API_KEY","")
        res.append((bool(ak and len(ak)>10), "Anthropic API Key",
                    "Get key  →  console.anthropic.com/settings/keys"))

    pkgs = [("telegram","python-telegram-bot"), ("aiohttp","aiohttp"),
            ("edge_tts","edge-tts"), ("dotenv","python-dotenv")]
    if provider == "gemini":
        pkgs.append(("google.generativeai","google-generativeai"))
    elif provider == "gpt":
        pkgs.append(("openai","openai"))
    elif provider == "ollama":
        pass  # no extra packages needed for ollama
    else:
        pkgs.append(("anthropic","anthropic"))

    for mod, pkg in pkgs:
        ok = pkg_ok(mod)
        res.append((ok, f"Package: {pkg}",
                    f"Go to Install tab  →  click Install ALL"))
    try:
        subprocess.run(["ffmpeg","-version"], capture_output=True, timeout=5)
        ff = True
    except Exception:
        ff = False
    res.append((ff, "ffmpeg (voice)", "Install tab  →  Install ffmpeg"))
    return res

# ── App ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Agent Manager v2")
        self.geometry("600x740")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.update_idletasks()
        self.geometry(f"600x740+{(self.winfo_screenwidth()-600)//2}+{(self.winfo_screenheight()-740)//2}")
        self._proc   = None
        self._engine = tk.StringVar(value=load_env().get("AI_PROVIDER","gemini"))
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        hdr = tk.Frame(self, bg=ACCENT, height=64)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="🤖  AI Agent Manager",
                 font=("Segoe UI",18,"bold"), bg=ACCENT, fg="white").pack(expand=True)

        st = ttk.Style(); st.theme_use("default")
        st.configure("TNotebook", background=BG, borderwidth=0)
        st.configure("TNotebook.Tab", background=CARD, foreground=TEXT,
                     padding=[14,7], font=("Segoe UI",10))
        st.map("TNotebook.Tab",
               background=[("selected",ACCENT)], foreground=[("selected","white")])

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
        t1=tk.Frame(nb,bg=BG); nb.add(t1, text="🚀  Launch")
        t2=tk.Frame(nb,bg=BG); nb.add(t2, text="🔑  Keys")
        t3=tk.Frame(nb,bg=BG); nb.add(t3, text="🔧  Diagnostics")
        t4=tk.Frame(nb,bg=BG); nb.add(t4, text="📦  Install")
        t5=tk.Frame(nb,bg=BG); nb.add(t5, text="⚙️  Settings")
        t6=tk.Frame(nb,bg=BG); nb.add(t6, text="🎙️  Voice")

        self._tab_launch(t1)
        self._tab_keys(t2)
        self._tab_diag(t3)
        self._tab_install(t4)
        self._tab_settings(t5)
        self._tab_voice(t6)

        self.statusbar = tk.Label(self, text="Ready — choose engine and press Start",
                                  bg=CARD, fg=TEXT, font=("Segoe UI",9), anchor="w", padx=10)
        self.statusbar.pack(fill="x", side="bottom")

    # ── Launch tab ────────────────────────────────────────────────────────────

    def _tab_launch(self, f):
        tk.Frame(f, bg=BG, height=16).pack()

        # Engine selection header
        tk.Label(f, text="Select AI engine:", bg=BG, fg=TEXT,
                 font=("Segoe UI",13,"bold")).pack()
        tk.Frame(f, bg=BG, height=10).pack()

        # Gemini card
        gf = tk.Frame(f, bg=CARD, relief="flat")
        gf.pack(fill="x", padx=32, pady=4)
        tk.Radiobutton(gf, text="", variable=self._engine, value="gemini",
                       bg=CARD, activebackground=CARD,
                       selectcolor=GREEN).pack(side="left", padx=10, pady=14)
        tk.Label(gf, text="🔵  Google Gemini", bg=CARD, fg=GREEN,
                 font=("Segoe UI",13,"bold")).pack(side="left")
        tk.Label(gf, text="FREE ✨  1500 req/day", bg=CARD, fg=GREEN,
                 font=("Segoe UI",10)).pack(side="right", padx=16)
        for w in [gf]+list(gf.winfo_children()):
            w.bind("<Button-1>", lambda e: self._engine.set("gemini"))

        # GPT card
        pf = tk.Frame(f, bg=CARD, relief="flat")
        pf.pack(fill="x", padx=32, pady=4)
        tk.Radiobutton(pf, text="", variable=self._engine, value="gpt",
                       bg=CARD, activebackground=CARD,
                       selectcolor="#74c7ec").pack(side="left", padx=10, pady=14)
        tk.Label(pf, text="🟢  ChatGPT (OpenAI)", bg=CARD, fg="#74c7ec",
                 font=("Segoe UI",13,"bold")).pack(side="left")
        tk.Label(pf, text="Paid 💳  $5 free", bg=CARD, fg=YELLOW,
                 font=("Segoe UI",10)).pack(side="right", padx=16)
        for w in [pf]+list(pf.winfo_children()):
            w.bind("<Button-1>", lambda e: self._engine.set("gpt"))

        # Claude card
        cf = tk.Frame(f, bg=CARD, relief="flat")
        cf.pack(fill="x", padx=32, pady=4)
        tk.Radiobutton(cf, text="", variable=self._engine, value="claude",
                       bg=CARD, activebackground=CARD,
                       selectcolor=ACCENT).pack(side="left", padx=10, pady=14)
        tk.Label(cf, text="🟣  Claude (Anthropic)", bg=CARD, fg=TEXT,
                 font=("Segoe UI",13,"bold")).pack(side="left")
        tk.Label(cf, text="Paid 💳", bg=CARD, fg=YELLOW,
                 font=("Segoe UI",10)).pack(side="right", padx=16)
        for w in [cf]+list(cf.winfo_children()):
            w.bind("<Button-1>", lambda e: self._engine.set("claude"))

        tk.Frame(f, bg=BG, height=12).pack()

        # Status
        self.agent_status = tk.Label(f, text="⬜  Agent not running",
                                     bg=BG, fg=YELLOW, font=("Segoe UI",11,"bold"))
        self.agent_status.pack()
        tk.Frame(f, bg=BG, height=8).pack()

        # Start / Stop
        row = tk.Frame(f, bg=BG); row.pack(fill="x", padx=32)
        tk.Button(row, text="▶  Start Agent", bg=GREEN, fg="#1e1e2e",
                  font=("Segoe UI",12,"bold"), relief="flat", cursor="hand2", height=2,
                  command=self._start).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(row, text="⏹  Stop Agent", bg=RED, fg="#1e1e2e",
                  font=("Segoe UI",12,"bold"), relief="flat", cursor="hand2", height=2,
                  command=self._stop).pack(side="left", fill="x", expand=True, padx=(4,0))

        tk.Frame(f, bg=BG, height=6).pack()

        tk.Button(f, text="🔄  Update Agent Files", bg=CARD, fg=TEXT,
                  font=("Segoe UI",10), relief="flat", cursor="hand2",
                  command=lambda: threading.Thread(target=self._update_files, daemon=True).start()).pack(fill="x", padx=32)

        tk.Frame(f, bg=BG, height=6).pack()

        # Live log
        tk.Label(f, text="📋  Live log:", bg=BG, fg=TEXT,
                 font=("Segoe UI",9)).pack(anchor="w", padx=32)
        self.log = scrolledtext.ScrolledText(
            f, height=8, bg=CARD, fg=GREEN, font=("Consolas",8),
            relief="flat", state="disabled", wrap="word")
        self.log.pack(fill="x", padx=32, pady=4)

        tk.Label(f, text="💡 After starting — open Telegram and write to your bot!",
                 bg=BG, fg=YELLOW, font=("Segoe UI",9)).pack()

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg+"\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start(self):
        engine = self._engine.get()
        env    = load_env()

        # Validate
        errors = []
        if not env.get("TELEGRAM_TOKEN"):
            errors.append("❌ Telegram Token missing → Keys tab")
        if not env.get("ALLOWED_USER_ID"):
            errors.append("❌ Telegram User ID missing → Keys tab")
        if engine == "gemini" and not env.get("GEMINI_API_KEY"):
            errors.append("❌ Gemini API Key missing → Keys tab\n   Free: aistudio.google.com/app/apikey")
        if engine == "claude" and not env.get("ANTHROPIC_API_KEY"):
            errors.append("❌ Anthropic API Key missing → Keys tab\n   console.anthropic.com/settings/keys")
        if not (AGENT_DIR/"main.py").exists():
            errors.append(f"❌ Agent not installed at {AGENT_DIR}")
        if errors:
            messagebox.showerror("Fix these issues first:", "\n\n".join(errors))
            return

        # Auto-install missing packages
        self._log("📦 Checking packages...")
        pkgs = ["python-telegram-bot", "aiohttp", "edge-tts", "python-dotenv"]
        if engine == "gemini":  pkgs.append("google-generativeai")
        elif engine == "gpt":   pkgs.append("openai")
        else:                   pkgs.append("anthropic")
        import importlib
        missing = []
        check = {"python-telegram-bot":"telegram", "google-generativeai":"google.generativeai",
                 "openai":"openai", "anthropic":"anthropic", "aiohttp":"aiohttp",
                 "edge-tts":"edge_tts", "python-dotenv":"dotenv"}
        for pkg in pkgs:
            mod = check.get(pkg, pkg)
            try: importlib.import_module(mod)
            except ImportError: missing.append(pkg)
        if missing:
            self._log(f"📦 Installing: {', '.join(missing)}")
            r = subprocess.run([sys.executable, "-m", "pip", "install"] + missing,
                               capture_output=True, text=True)
            if r.returncode == 0:
                self._log("✅ Packages installed!")
            else:
                self._log(f"⚠️ Some failed: {r.stderr[-100:]}")
        else:
            self._log("✅ All packages OK")

        # Auto-update files
        self._log("🔄 Updating agent files...")
        self._update_files(silent=False)

        # Save chosen engine
        env["AI_PROVIDER"] = engine
        save_env(env)

        # Stop previous
        self._stop(silent=True)
        time.sleep(0.3)

        e = os.environ.copy()
        e.update(env)

        self._log(f"▶ Starting with {engine.upper()}...")
        try:
            self._proc = subprocess.Popen(
                [sys.executable, str(AGENT_DIR/"main.py")],
                cwd=str(AGENT_DIR), env=e,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            names = {"gemini":"Gemini 🔵","gpt":"ChatGPT 🟢","ollama":"Ollama 🦙","claude":"Claude 🟣"}
            name = names.get(engine, engine)
            self.agent_status.config(text=f"🟢  Running — {name}", fg=GREEN)
            self.statusbar.config(text=f"✅ Agent running with {engine}. Open Telegram!", fg=GREEN)
            self._log(f"✅ Started! PID {self._proc.pid}")
            self._log("📱 Open Telegram → write to your bot!")
            threading.Thread(target=self._read_log, daemon=True).start()
        except Exception as ex:
            self._log(f"❌ Failed: {ex}")
            self.agent_status.config(text="❌  Start failed!", fg=RED)

    def _read_log(self):
        try:
            for line in self._proc.stdout:
                line = line.rstrip()
                if line:
                    self.after(0, self._log, line)
            code = self._proc.wait()
            self.after(0, self._log, f"\n⚠️ Agent stopped (exit code: {code})")
            self.after(0, self.agent_status.config, {"text":"⬜  Agent stopped","fg":YELLOW})
        except Exception as e:
            self.after(0, self._log, f"Log error: {e}")

    def _update_files(self, silent=False):
        """Copy new agent files from manager folder to AGENT_DIR"""
        import shutil, time

        # Stop bot first if running — files will be locked otherwise
        was_running = self._proc is not None and self._proc.poll() is None
        if was_running:
            if not silent: self._log('⏹ Stopping bot before update...')
            self._stop(silent=True)
            time.sleep(1.5)  # wait for process to release file locks

        src = Path(__file__).parent

        # Copy ALL python files from source root
        files = [f.name for f in src.glob('*.py')]
        # Copy ALL tool files
        tools = [f.name for f in (src / 'tools').glob('*.py')] if (src / 'tools').exists() else []

        AGENT_DIR.mkdir(parents=True, exist_ok=True)
        (AGENT_DIR / 'tools').mkdir(exist_ok=True)

        count = 0
        errors = 0
        for f in files:
            s = src / f
            if s.exists():
                try:
                    shutil.copy2(s, AGENT_DIR / f)
                    if not silent: self._log(f'✅ {f}')
                    count += 1
                except PermissionError as e:
                    self._log(f'⚠️ Skipped {f} (in use)')
                    errors += 1
                except Exception as e:
                    self._log(f'❌ {f}: {e}')
                    errors += 1

        for f in tools:
            s = src / 'tools' / f
            if s.exists():
                try:
                    shutil.copy2(s, AGENT_DIR / 'tools' / f)
                    count += 1
                except Exception:
                    errors += 1

        if not silent:
            self._log(f'✅ Tools updated ({len(tools)} files)')
            self._log(f'🎉 {count} files copied to {AGENT_DIR}')
            if errors:
                self._log(f'⚠️ {errors} files skipped (close other programs and retry)')

        # Restart bot if it was running before update
        if was_running:
            time.sleep(0.5)
            if not silent: self._log('▶️ Restarting bot...')
            self._start(silent=True)

    def _stop(self, silent=False):
        if self._proc:
            try: self._proc.terminate()
            except Exception: pass
            self._proc = None
        if not silent:
            self.agent_status.config(text="⬜  Agent stopped", fg=YELLOW)
            self.statusbar.config(text="Agent stopped", fg=YELLOW)
            self._log("⏹ Stopped.")

    # ── Keys tab ──────────────────────────────────────────────────────────────

    def _tab_keys(self, f):
        env = load_env()
        tk.Frame(f, bg=BG, height=12).pack()
        fields = [
            ("Telegram Token",    "TELEGRAM_TOKEN",    "@BotFather → /mybots → Generate new token", None),
            ("Gemini API Key",    "GEMINI_API_KEY",    "aistudio.google.com/app/apikey  ← FREE!", "https://aistudio.google.com/app/apikey"),
            ("OpenAI API Key",    "OPENAI_API_KEY",    "platform.openai.com/api-keys  ($5 free)", "https://platform.openai.com/api-keys"),
            ("Anthropic API Key", "ANTHROPIC_API_KEY", "console.anthropic.com/settings/keys", "https://console.anthropic.com/settings/keys"),
            ("Telegram User ID",  "ALLOWED_USER_ID",   "@userinfobot — write any message, copy ID", None),
        ]
        self._kvars = {}
        for label, key, hint, url in fields:
            self._sec(f, label)
            if url:
                lnk = tk.Label(f, text=f"🔗 {hint}", bg=BG, fg=ACCENT,
                               font=("Segoe UI",8,"underline"), cursor="hand2")
                lnk.pack(anchor="w", padx=24)
                lnk.bind("<Button-1>", lambda e, u=url: os.startfile(u))
            else:
                tk.Label(f, text=hint, bg=BG, fg=YELLOW,
                         font=("Segoe UI",8)).pack(anchor="w", padx=24)
            var = tk.StringVar(value=env.get(key,""))
            tk.Entry(f, textvariable=var, bg=CARD, fg=TEXT,
                     font=("Segoe UI",10), insertbackground=TEXT,
                     relief="flat", bd=8).pack(fill="x", padx=24, pady=2)
            self._kvars[key] = var

        tk.Frame(f, bg=BG, height=12).pack()
        tk.Button(f, text="💾  Save & Restart Agent", bg=ACCENT, fg="white",
                  font=("Segoe UI",12,"bold"), relief="flat", cursor="hand2", height=2,
                  command=self._save_keys).pack(fill="x", padx=24)
        tk.Frame(f, bg=BG, height=6).pack()
        tk.Button(f, text="💾  Save only", bg=CARD, fg=TEXT,
                  font=("Segoe UI",10), relief="flat", cursor="hand2",
                  command=lambda: self._save_keys(restart=False)).pack(fill="x", padx=24)

    def _save_keys(self, restart=True):
        env = load_env()
        for k, v in self._kvars.items():
            env[k] = v.get().strip()
        save_env(env)
        self.statusbar.config(text="✅ Keys saved!", fg=GREEN)
        if restart:
            self._start()

    # ── Diagnostics tab ───────────────────────────────────────────────────────

    def _tab_diag(self, f):
        tk.Frame(f, bg=BG, height=12).pack()
        tk.Button(f, text="🔍  Run Diagnostics", bg=ACCENT, fg="white",
                  font=("Segoe UI",12,"bold"), relief="flat", cursor="hand2",
                  command=self._diag).pack(fill="x", padx=24)
        tk.Frame(f, bg=BG, height=8).pack()
        self.diag_frame = tk.Frame(f, bg=BG)
        self.diag_frame.pack(fill="both", expand=True, padx=24)
        self.after(600, self._diag)

    def _diag(self):
        for w in self.diag_frame.winfo_children(): w.destroy()
        provider = self._engine.get()
        results  = run_diag(provider)
        all_ok   = all(r[0] for r in results)
        tk.Label(self.diag_frame,
                 text="✅ All OK! Ready to launch." if all_ok else "⚠️ Issues found:",
                 bg=BG, fg=GREEN if all_ok else YELLOW,
                 font=("Segoe UI",11,"bold")).pack(anchor="w", pady=(0,8))
        for ok, name, fix in results:
            row = tk.Frame(self.diag_frame, bg=CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text="✅" if ok else "❌", bg=CARD,
                     font=("Segoe UI",12), width=3).pack(side="left", padx=6, pady=6)
            tk.Label(row, text=name, bg=CARD, fg=GREEN if ok else RED,
                     font=("Segoe UI",10)).pack(side="left", pady=6)
            if not ok:
                fx = tk.Frame(self.diag_frame, bg="#2a1a1a")
                fx.pack(fill="x")
                tk.Label(fx, text=f"   🔧 {fix}", bg="#2a1a1a", fg=ORANGE,
                         font=("Segoe UI",8), wraplength=520,
                         justify="left").pack(anchor="w", padx=12, pady=3)

    # ── Install tab ───────────────────────────────────────────────────────────

    def _tab_install(self, f):
        tk.Frame(f, bg=BG, height=12).pack()
        pkgs = [
            ("python-telegram-bot", "Telegram bot"),
            ("google-generativeai", "Gemini AI  ← FREE"),
            ("anthropic",           "Claude AI"),
            ("aiohttp",             "HTTP client"),
            ("edge-tts",            "Voice synthesis"),
            ("openai-whisper",      "Speech recognition"),
            ("python-dotenv",       "Config loader"),
        ]
        for pkg, desc in pkgs:
            row = tk.Frame(f, bg=CARD)
            row.pack(fill="x", padx=24, pady=2)
            tk.Label(row, text=f"📦 {pkg}", bg=CARD, fg=TEXT,
                     font=("Segoe UI",10,"bold"), width=24, anchor="w").pack(side="left", padx=10, pady=8)
            tk.Label(row, text=desc, bg=CARD, fg="#888",
                     font=("Segoe UI",9)).pack(side="left")
            tk.Button(row, text="Install", bg=ACCENT, fg="white",
                      font=("Segoe UI",9), relief="flat", cursor="hand2",
                      command=lambda p=pkg: self._inst([p])).pack(side="right", padx=10, pady=6)

        tk.Frame(f, bg=BG, height=6).pack()
        tk.Button(f, text="📦  Install ALL", bg=GREEN, fg="#1e1e2e",
                  font=("Segoe UI",12,"bold"), relief="flat", cursor="hand2",
                  command=lambda: self._inst([p for p,_ in pkgs])).pack(fill="x", padx=24)
        tk.Frame(f, bg=BG, height=4).pack()
        tk.Button(f, text="🎙️  Install ffmpeg (voice)", bg=CARD, fg=TEXT,
                  font=("Segoe UI",10), relief="flat", cursor="hand2",
                  command=self._inst_ffmpeg).pack(fill="x", padx=24)
        tk.Frame(f, bg=BG, height=6).pack()
        self.ilog = scrolledtext.ScrolledText(
            f, height=6, bg=CARD, fg=TEXT, font=("Consolas",8),
            relief="flat", state="disabled")
        self.ilog.pack(fill="x", padx=24, pady=4)


    def _tab_settings(self, f):
        import json
        from pathlib import Path

        LANG_FILE = Path.home() / "ai-agent" / "data" / "bot_language.json"

        LANGUAGES = {
            "ru": "🇷🇺 Русский",
            "en": "🇬🇧 English",
            "nl": "🇳🇱 Nederlands",
            "de": "🇩🇪 Deutsch",
            "fr": "🇫🇷 Français",
            "uk": "🇺🇦 Українська",
        }

        def load_settings():
            try:
                if LANG_FILE.exists():
                    return json.loads(LANG_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
            return {}

        def save_settings(data):
            LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
            LANG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        tk.Frame(f, bg=BG, height=16).pack()

        # Title
        tk.Label(f, text="⚙️  Bot Settings", bg=BG, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 16))

        # ── Bot Language ──────────────────────────────────────────
        card1 = tk.Frame(f, bg=CARD, pady=16, padx=20)
        card1.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(card1, text="🗣  Bot Language", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(card1, text="The language the bot will use to respond in Telegram",
                 bg=CARD, fg="#888", font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 10))

        bot_lang_var = tk.StringVar(value=load_settings().get("lang", "ru"))

        lang_frame = tk.Frame(card1, bg=CARD)
        lang_frame.pack(fill="x")

        for i, (code, name) in enumerate(LANGUAGES.items()):
            btn = tk.Radiobutton(
                lang_frame, text=name, variable=bot_lang_var, value=code,
                bg=CARD, fg=TEXT, selectcolor=ACCENT,
                activebackground=CARD, activeforeground=TEXT,
                font=("Segoe UI", 10), cursor="hand2"
            )
            btn.grid(row=i//3, column=i%3, sticky="w", padx=12, pady=4)

        # ── Translation Language ──────────────────────────────────
        card2 = tk.Frame(f, bg=CARD, pady=16, padx=20)
        card2.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(card2, text="🌐  Call Translation Language",
                 bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(card2, text="Audio files will be transcribed and translated to this language",
                 bg=CARD, fg="#888", font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 10))

        translate_lang_var = tk.StringVar(value=load_settings().get("translate_lang", "en"))

        trans_frame = tk.Frame(card2, bg=CARD)
        trans_frame.pack(fill="x")

        for i, (code, name) in enumerate(LANGUAGES.items()):
            btn = tk.Radiobutton(
                trans_frame, text=name, variable=translate_lang_var, value=code,
                bg=CARD, fg=TEXT, selectcolor=ACCENT,
                activebackground=CARD, activeforeground=TEXT,
                font=("Segoe UI", 10), cursor="hand2"
            )
            btn.grid(row=i//3, column=i%3, sticky="w", padx=12, pady=4)

        # ── Voice Reply ───────────────────────────────────────────
        card3 = tk.Frame(f, bg=CARD, pady=16, padx=20)
        card3.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(card3, text="🎙️  Voice Reply",
                 bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(card3, text="Bot responds with voice messages (requires internet)",
                 bg=CARD, fg="#888", font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 8))

        voice_var = tk.BooleanVar(value=True)
        env_path = Path.home() / "ai-agent" / ".env"
        try:
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("VOICE_REPLY="):
                        voice_var.set(line.split("=",1)[1].strip().lower() == "true")
        except Exception:
            pass

        tk.Checkbutton(card3, text="Enable voice replies", variable=voice_var,
                       bg=CARD, fg=TEXT, selectcolor=ACCENT,
                       activebackground=CARD, font=("Segoe UI", 10)).pack(anchor="w")

        # ── Save Button ───────────────────────────────────────────
        status_lbl = tk.Label(f, text="", bg=BG, fg=GREEN, font=("Segoe UI", 10))
        status_lbl.pack(pady=(4, 0))

        def save_all():
            s = load_settings()
            s["lang"] = bot_lang_var.get()
            s["translate_lang"] = translate_lang_var.get()
            save_settings(s)
            # Update VOICE_REPLY in .env
            try:
                if env_path.exists():
                    lines = env_path.read_text(encoding="utf-8-sig").splitlines()
                    new_lines = []
                    found = False
                    for line in lines:
                        if line.startswith("VOICE_REPLY="):
                            new_lines.append(f"VOICE_REPLY={'true' if voice_var.get() else 'false'}")
                            found = True
                        else:
                            new_lines.append(line)
                    if not found:
                        new_lines.append(f"VOICE_REPLY={'true' if voice_var.get() else 'false'}")
                    env_path.write_text("\n".join(new_lines), encoding="utf-8")
            except Exception as e:
                status_lbl.config(text=f"⚠️ .env error: {e}", fg=YELLOW)
                return
            lang_name = LANGUAGES.get(bot_lang_var.get(), bot_lang_var.get())
            trans_name = LANGUAGES.get(translate_lang_var.get(), translate_lang_var.get())
            status_lbl.config(
                text=f"✅ Saved!  Bot: {lang_name}  |  Translate: {trans_name}",
                fg=GREEN)

        tk.Button(f, text="💾  Save Settings", command=save_all,
                  bg=ACCENT, fg="white", font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=24, pady=8, cursor="hand2"
                  ).pack(pady=12)

        tk.Label(f, text="⚡ Restart bot after saving to apply changes",
                 bg=BG, fg="#888", font=("Segoe UI", 9, "italic")).pack()


    def _tab_voice(self, f):
        """Voice + Text chat tab — direct AI without Telegram"""
        import threading, queue, sys, os

        self._chat_queue  = queue.Queue()
        self._voice_running = False
        self._voice_thread  = None

        # ── Layout ────────────────────────────────────────────
        tk.Frame(f, bg=BG, height=8).pack()

        tk.Label(f, text="🤖  AI Chat & Voice Control",
                 bg=BG, fg=TEXT, font=("Segoe UI", 13, "bold")).pack()
        tk.Label(f, text='Say "Агент" or type below — no Telegram needed',
                 bg=BG, fg=ACCENT, font=("Segoe UI", 9, "italic")).pack(pady=(2,8))

        # ── Status bar ────────────────────────────────────────
        status_f = tk.Frame(f, bg=CARD, pady=6, padx=12)
        status_f.pack(fill="x", padx=16, pady=(0,6))
        self._vc_dot = tk.Label(status_f, text="⚫", bg=CARD, font=("Segoe UI",14))
        self._vc_dot.pack(side="left", padx=(0,8))
        self._vc_status = tk.Label(status_f, text="Stopped",
                                    bg=CARD, fg=TEXT, font=("Segoe UI",9), anchor="w")
        self._vc_status.pack(side="left", fill="x", expand=True)

        # ── Chat window ───────────────────────────────────────
        from tkinter import scrolledtext
        self._chat_log = scrolledtext.ScrolledText(
            f, height=12, bg="#0d1117", fg="#e6edf3",
            font=("Segoe UI", 10), wrap="word",
            state="disabled", relief="flat", bd=0,
            insertbackground="white")
        self._chat_log.pack(fill="both", expand=True, padx=16, pady=(0,6))

        # Color tags
        self._chat_log.tag_config("you",    foreground="#79c0ff", font=("Segoe UI",10,"bold"))
        self._chat_log.tag_config("bot",    foreground="#56d364", font=("Segoe UI",10,"bold"))
        self._chat_log.tag_config("sys",    foreground="#e3b341", font=("Segoe UI",9,"italic"))
        self._chat_log.tag_config("err",    foreground="#f85149", font=("Segoe UI",9))
        self._chat_log.tag_config("msg",    foreground="#e6edf3", font=("Segoe UI",10))
        self._chat_log.tag_config("newline",foreground="#e6edf3", font=("Segoe UI",4))

        # ── Input row ─────────────────────────────────────────
        input_f = tk.Frame(f, bg=BG)
        input_f.pack(fill="x", padx=16, pady=(0,6))

        self._chat_input = tk.Entry(
            input_f, bg="#161b22", fg="#e6edf3",
            font=("Segoe UI", 11), relief="flat",
            insertbackground="white", bd=6)
        self._chat_input.pack(side="left", fill="x", expand=True, ipady=6)
        self._chat_input.bind("<Return>", lambda e: self._chat_send())
        self._chat_input.bind("<KP_Enter>", lambda e: self._chat_send())

        tk.Button(input_f, text="Send ↵",
                  command=self._chat_send,
                  bg=ACCENT, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=14, pady=6,
                  cursor="hand2").pack(side="left", padx=(6,0))

        # ── Buttons row ───────────────────────────────────────
        btn_f = tk.Frame(f, bg=BG)
        btn_f.pack(pady=(0,4))

        self._vc_btn = tk.Button(
            btn_f, text="🎙️  Start Voice",
            command=self._vc_toggle,
            bg=GREEN, fg="#000",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, pady=6, cursor="hand2")
        self._vc_btn.pack(side="left", padx=4)

        tk.Button(btn_f, text="🗑️ Clear",
                  command=self._chat_clear,
                  bg=CARD, fg=TEXT,
                  font=("Segoe UI", 10),
                  relief="flat", padx=12, pady=6,
                  cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_f, text="🎤 Тест микрофона",
                  command=self._mic_test,
                  bg=YELLOW, fg="#000",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=12, pady=6,
                  cursor="hand2").pack(side="left", padx=4)

        # Lang row
        lang_f = tk.Frame(f, bg=BG)
        lang_f.pack(pady=(0,6))
        tk.Label(lang_f, text="🌍", bg=BG, fg=TEXT,
                 font=("Segoe UI",9)).pack(side="left")
        self._vc_lang = tk.StringVar(value="ru-RU")
        for lbl, code in [("RU","ru-RU"),("EN","en-US"),("NL","nl-NL"),("DE","de-DE")]:
            tk.Radiobutton(lang_f, text=lbl, variable=self._vc_lang, value=code,
                           bg=BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=BG, font=("Segoe UI",9),
                           cursor="hand2").pack(side="left", padx=4)

        # Greet user
        self._chat_append("sys", "AI Agent Chat ready. Type a message or start Voice.")
        self._chat_input.focus()

    def _chat_append(self, role, text):
        """Append message to chat log"""
        try:
            log = self._chat_log
            log.config(state="normal")
            labels = {"you":"You", "bot":"🤖 Agent", "sys":"⚙", "err":"❌"}
            label = labels.get(role, role)
            log.insert("end", f"{label}: ", role)
            log.insert("end", text + "\n", "msg")
            log.see("end")
            log.config(state="disabled")
        except Exception:
            pass

    def _chat_clear(self):
        try:
            self._chat_log.config(state="normal")
            self._chat_log.delete("1.0","end")
            self._chat_log.config(state="disabled")
        except Exception:
            pass

    def _chat_send(self):
        """Send text message to AI"""
        text = self._chat_input.get().strip()
        if not text:
            return
        self._chat_input.delete(0,"end")
        self._chat_append("you", text)
        self._vc_set_status("🤖 Thinking...", "🔵")
        import threading
        threading.Thread(target=self._run_ai, args=(text,), daemon=True).start()

    def _run_ai(self, text):
        """Run AI query in background thread"""
        import asyncio, sys
        sys.path.insert(0, str(AGENT_DIR))
        # Load .env
        try:
            from dotenv import load_dotenv
            load_dotenv(str(AGENT_DIR / ".env"), encoding="utf-8-sig")
        except Exception:
            pass
        try:
            provider = self._get_provider()
            if provider == "claude":
                from agent_claude import ClaudeAgent
                agent = ClaudeAgent()
            elif provider == "gpt":
                from agent_gpt import GPTAgent
                agent = GPTAgent()
            else:
                from agent_gemini import GeminiAgent
                agent = GeminiAgent()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                asyncio.wait_for(agent.run(text), timeout=30))
            loop.close()

            self.after(0, lambda: self._chat_append("bot", result[:600]))
            self.after(0, lambda: self._vc_set_status("Ready", "🟢"))

            # Speak if voice active
            if self._voice_running and hasattr(self, "_vc_speak"):
                import re
                clean = re.sub(r"[*_`#>]", "", result)[:300]
                self._vc_speak(clean)

        except asyncio.TimeoutError:
            self.after(0, lambda: self._chat_append("err", "Timeout — try again"))
            self.after(0, lambda: self._vc_set_status("Timeout", "🔴"))
        except Exception as e:
            err = str(e)[:200]
            self.after(0, lambda: self._chat_append("err", err))
            self.after(0, lambda: self._vc_set_status("Error", "🔴"))

    def _vc_set_status(self, text, dot="⚫"):
        try:
            self._vc_status.config(text=text)
            self._vc_dot.config(text=dot)
        except Exception:
            pass

    def _vc_toggle(self):
        if self._voice_running:
            self._vc_stop()
        else:
            self._vc_start()

    def _vc_start(self):
        """Start always-on voice listener using sounddevice (no PyAudio needed)"""
        import threading, subprocess, sys

        self._voice_running = True
        self._vc_btn.config(text="⏹  Stop Voice", bg=RED)
        self._vc_set_status("Installing voice libs...", "🟡")

        def setup_and_run():
            # Install required packages
            pkgs = [
                ("SpeechRecognition", "speech_recognition"),
                ("sounddevice", "sounddevice"),
                ("scipy", "scipy"),
                ("pyttsx3", "pyttsx3"),
            ]
            for pkg, imp in pkgs:
                try:
                    __import__(imp)
                except ImportError:
                    self.after(0, lambda p=pkg: self._vc_set_status(
                        f"Installing {p}...", "🟡"))
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg,
                         "--break-system-packages", "-q"],
                        capture_output=True)

            self.after(0, lambda: self._vc_set_status(
                "🎤 Starting mic...", "🟡"))
            self._voice_loop()

        threading.Thread(target=setup_and_run, daemon=True).start()

    def _voice_loop(self):
        """Background voice loop — uses sounddevice instead of PyAudio"""
        import sys, subprocess, time, queue, threading
        sys.path.insert(0, str(AGENT_DIR))

        # ── Install deps silently ──────────────────────────────
        def pip_install(pkg):
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q",
                 "--break-system-packages"],
                capture_output=True)

        for pkg in ["SpeechRecognition", "sounddevice", "scipy",
                    "pyttsx3", "pywin32"]:
            try:
                imp = {"SpeechRecognition":"speech_recognition",
                       "pywin32":"win32api"}.get(pkg, pkg)
                __import__(imp)
            except ImportError:
                self.after(0, lambda p=pkg: self._vc_set_status(
                    f"Installing {p}...", "🟡"))
                pip_install(pkg)

        # ── TTS ───────────────────────────────────────────────
        tts_q = queue.Queue()

        def tts_worker():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", 160)
                engine.setProperty("volume", 1.0)
                # Try Russian voice
                for v in engine.getProperty("voices"):
                    if any(x in v.name.lower()
                           for x in ["russian","irina","zira","elena"]):
                        engine.setProperty("voice", v.id)
                        break
                while self._voice_running:
                    try:
                        txt = tts_q.get(timeout=0.5)
                        engine.say(txt)
                        engine.runAndWait()
                        tts_q.task_done()
                    except queue.Empty:
                        continue
            except Exception as e:
                self.after(0, lambda: self._chat_append(
                    "sys", f"TTS unavailable: {e}"))

        tts_thread = threading.Thread(target=tts_worker, daemon=True)
        tts_thread.start()

        def speak(txt):
            try:
                tts_q.put_nowait(txt[:300])
            except Exception:
                pass

        self._vc_speak = speak

        # ── STT with sounddevice backend ──────────────────────
        try:
            import speech_recognition as sr

            # Try sounddevice backend first (no PyAudio needed)
            try:
                import sounddevice as sd
                import scipy.io.wavfile as wav
                import numpy as np
                import tempfile, os
                USE_SD = True
                self.after(0, lambda: self._chat_append("sys", "Using sounddevice backend"))
            except ImportError:
                USE_SD = False

            rec = sr.Recognizer()
            rec.energy_threshold = 300
            rec.dynamic_energy_threshold = True
            rec.pause_threshold = 0.8

            if not USE_SD:
                try:
                    mic = sr.Microphone()
                except Exception as e:
                    raise Exception(f"No audio backend found. Run install_voice.bat\nDetails: {e}")
            else:
                mic = None

            WAKE = ["агент","agent","assistant","ассистент",
                    "hey agent","эй агент","привет агент"]

            def record_audio_sd(duration=6, samplerate=16000):
                """Record audio using sounddevice, return AudioData"""
                import sounddevice as sd
                import numpy as np
                import io, wave
                self.after(0, lambda: self._vc_dot.config(text="🟢"))
                audio_np = sd.rec(int(duration * samplerate),
                                  samplerate=samplerate, channels=1,
                                  dtype='int16')
                sd.wait()
                # Convert to WAV bytes
                buf = io.BytesIO()
                with wave.open(buf, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(samplerate)
                    wf.writeframes(audio_np.tobytes())
                buf.seek(0)
                return sr.AudioData(buf.read(), samplerate, 2)

            def listen_once(timeout=6):
                if USE_SD:
                    return record_audio_sd(duration=timeout)
                else:
                    with mic as src:
                        return rec.listen(src, timeout=timeout,
                                         phrase_time_limit=10)

            def recognize(audio):
                lang = self._vc_lang.get()
                for lng in [lang, "ru-RU", "en-US"]:
                    try:
                        return rec.recognize_google(audio, language=lng)
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        self.after(0, lambda: self._chat_append(
                            "err", f"STT error (no internet?): {e}"))
                        return ""
                return ""

            # Calibrate if using mic
            if not USE_SD:
                self.after(0, lambda: self._vc_set_status("Calibrating...", "🟡"))
                with mic as src:
                    rec.adjust_for_ambient_noise(src, duration=1.5)

            self.after(0, lambda: self._vc_set_status('Ready — say "Агент"', "🟢"))
            self.after(0, lambda: self._chat_append(
                "sys", '✅ Voice ready! Say "Агент [command]"'))
            speak("Привет! Я готов к работе. Скажи Агент для активации.")

            while self._voice_running:
                try:
                    audio = listen_once(timeout=6)
                except Exception:
                    if self._voice_running:
                        time.sleep(0.3)
                    continue

                text = recognize(audio)
                if not text:
                    continue

                tl = text.lower().strip()
                self.after(0, lambda t=text: self._vc_status.config(
                    text=f'Heard: "{t}"'))

                if not any(w in tl for w in WAKE):
                    continue

                cmd = tl
                for w in sorted(WAKE, key=len, reverse=True):
                    cmd = cmd.replace(w, "").strip(" ,!?.")

                self.after(0, lambda t=text: self._chat_append("you", t))

                if not cmd:
                    speak("Слушаю")
                    self.after(0, lambda: self._vc_set_status(
                        "Say your command...", "🔵"))
                    try:
                        audio2 = listen_once(timeout=7)
                        cmd = recognize(audio2)
                        if cmd:
                            self.after(0, lambda c=cmd:
                                       self._chat_append("you", c))
                    except Exception:
                        self.after(0, lambda: self._vc_set_status(
                            'Ready — say "Агент"', "🟢"))
                        continue

                if cmd:
                    self.after(0, lambda: self._vc_set_status(
                        "🤖 Thinking...", "🔵"))
                    threading.Thread(
                        target=self._run_ai, args=(cmd,),
                        daemon=True).start()

        except Exception as e:
            err = str(e)
            self.after(0, lambda: self._chat_append(
                "err", f"Voice setup failed: {err}\n"
                       "Fix: run install_voice.bat as Administrator"))
            self.after(0, lambda: self._vc_set_status(
                f"Error — run install_voice.bat", "🔴"))
            self._voice_running = False
            self.after(0, lambda: self._vc_btn.config(
                text="🎙️  Start Voice", bg=GREEN))


    def _vc_stop(self):
        self._voice_running = False
        self._vc_btn.config(text="🎙️  Start Voice", bg=GREEN)
        self._vc_set_status("Stopped", "⚫")
        self._chat_append("sys", "Voice control stopped")

    def _mic_test(self):
        """Full microphone diagnostic test"""
        import threading
        self._chat_append("sys", "🎤 Запускаю диагностику микрофона...")
        threading.Thread(target=self._run_mic_test, daemon=True).start()

    def _run_mic_test(self):
        import subprocess, sys, time

        def log(msg, tag="sys"):
            self.after(0, lambda m=msg, t=tag: self._chat_append(t, m))

        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log("🎤 ТЕСТ МИКРОФОНА")
        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Step 1: Check sounddevice
        log("1️⃣ Проверка sounddevice...")
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devs = [d for d in devices if d["max_input_channels"] > 0]
            if input_devs:
                log(f"   ✅ sounddevice OK — найдено {len(input_devs)} микрофон(ов)")
                for i, d in enumerate(input_devs[:3]):
                    log(f"   🎙️ [{i}] {d['name']}")
                default = sd.query_devices(kind='input')
                log(f"   ⭐ По умолчанию: {default['name']}")
            else:
                log("   ❌ Микрофоны не найдены!", "err")
                log("   Подключи микрофон и перезапусти", "err")
                return
        except ImportError:
            log("   ❌ sounddevice не установлен", "err")
            log("   Запусти install_voice.bat", "err")
            return
        except Exception as e:
            log(f"   ❌ Ошибка: {e}", "err")
            return

        # Step 2: Record 3 seconds
        log("2️⃣ Запись 3 секунды — ГОВОРИ СЕЙЧАС!")
        self.after(0, lambda: self._vc_set_status("🔴 RECORDING — говори!", "🔴"))
        try:
            import sounddevice as sd
            import numpy as np
            import io, wave

            samplerate = 16000
            duration = 3
            log("   ⏺️ Запись...")
            audio = sd.rec(int(duration * samplerate),
                          samplerate=samplerate, channels=1, dtype='int16')
            sd.wait()

            # Check volume
            volume = np.abs(audio).mean()
            max_vol = np.abs(audio).max()
            log(f"   📊 Средняя громкость: {volume:.0f}")
            log(f"   📊 Максимум: {max_vol:.0f}")

            if max_vol < 100:
                log("   ❌ Звук слишком тихий — микрофон не слышит!", "err")
                log("   Проверь: включён ли микрофон в Windows?", "err")
                log("   Пуск → Настройки → Система → Звук → Ввод", "err")
            elif max_vol < 500:
                log("   ⚠️ Звук слабый — говори громче или поднеси микрофон", "sys")
            else:
                log("   ✅ Звук хороший!")

        except Exception as e:
            log(f"   ❌ Ошибка записи: {e}", "err")
            return
        finally:
            self.after(0, lambda: self._vc_set_status('Ready — say "Агент"', "🟢"))

        # Step 3: SpeechRecognition test
        log("3️⃣ Проверка распознавания речи...")
        try:
            import speech_recognition as sr
            rec = sr.Recognizer()

            # Use recorded audio
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframes(audio.tobytes())
            buf.seek(0)
            audio_data = sr.AudioData(buf.read(), samplerate, 2)

            log("   📡 Отправляю в Google STT...")
            try:
                text = rec.recognize_google(audio_data, language="ru-RU")
                log(f"   ✅ Распознано: \"{text}\"")
                log("   🎉 Микрофон работает отлично!")
            except sr.UnknownValueError:
                log("   ⚠️ Речь не распознана — говори чётче или проверь интернет")
                try:
                    text2 = rec.recognize_google(audio_data, language="en-US")
                    log(f"   (EN распознал: \"{text2}\")")
                except Exception:
                    pass
            except sr.RequestError as e:
                log(f"   ❌ Нет интернета или ошибка Google STT: {e}", "err")

        except ImportError:
            log("   ❌ SpeechRecognition не установлен — запусти install_voice.bat", "err")
        except Exception as e:
            log(f"   ❌ Ошибка: {e}", "err")

        # Step 4: Windows mic settings hint
        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log("💡 Если микрофон не слышит:")
        log("   1. Пуск → Настройки → Конфиденциальность")
        log("   2. Микрофон → Разрешить приложениям")
        log("   3. Пуск → Управление звуком → Запись")
        log("   4. Правой кнопкой на микрофон → Свойства → Уровни")
        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    def _get_provider(self) -> str:
        try:
            return self._engine.get()
        except Exception:
            return "gemini"


    def _inst(self, pkgs):
        threading.Thread(target=self._do_inst, args=(pkgs,), daemon=True).start()

    def _do_inst(self, pkgs):
        for p in pkgs:
            self._ilog(f"Installing {p}...")
            r = subprocess.run([sys.executable,"-m","pip","install",p],
                               capture_output=True, text=True)
            self._ilog(f"{'✅' if r.returncode==0 else '❌'} {p}")
            if r.returncode != 0:
                self._ilog(r.stderr[-150:])
        self._ilog("Done!")
        self.after(100, self._diag)

    def _inst_ffmpeg(self):
        threading.Thread(target=lambda: (
            self._ilog("Installing ffmpeg..."),
            self._ilog("✅ Done!" if subprocess.run(
                ["winget","install","Gyan.FFmpeg","--silent"],
                capture_output=True).returncode==0 else "❌ Failed — install manually"),
            self.after(100, self._diag)
        ), daemon=True).start()

    def _ilog(self, msg):
        self.ilog.configure(state="normal")
        self.ilog.insert("end", msg+"\n")
        self.ilog.see("end")
        self.ilog.configure(state="disabled")
        self.update()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _sec(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=TEXT,
                 font=("Segoe UI",10,"bold")).pack(anchor="w", padx=24, pady=(8,0))
        tk.Frame(parent, bg=ACCENT, height=2).pack(fill="x", padx=24, pady=(2,2))


if __name__ == "__main__":
    App().mainloop()
