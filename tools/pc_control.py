"""
PC Control - управление мышью и клавиатурой через бота
Требует: pip install pyautogui
"""
import subprocess, sys, time

def _ensure_pyautogui():
    try:
        import pyautogui
        return pyautogui
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui", "--break-system-packages"], 
                      capture_output=True)
        import pyautogui
        return pyautogui

class PCControl:

    def move_mouse(self, x: int, y: int) -> str:
        """Move mouse to coordinates"""
        try:
            pg = _ensure_pyautogui()
            pg.moveTo(x, y, duration=0.3)
            return f"🖱️ Mouse moved to ({x}, {y})"
        except Exception as e:
            return f"❌ Error: {e}"

    def click(self, x: int = None, y: int = None, button: str = "left") -> str:
        """Click mouse at position (or current position)"""
        try:
            pg = _ensure_pyautogui()
            if x is not None and y is not None:
                pg.click(x, y, button=button)
                return f"🖱️ Clicked {button} at ({x}, {y})"
            else:
                pg.click(button=button)
                pos = pg.position()
                return f"🖱️ Clicked {button} at current position {pos}"
        except Exception as e:
            return f"❌ Error: {e}"

    def double_click(self, x: int, y: int) -> str:
        """Double click at position"""
        try:
            pg = _ensure_pyautogui()
            pg.doubleClick(x, y)
            return f"🖱️ Double clicked at ({x}, {y})"
        except Exception as e:
            return f"❌ Error: {e}"

    def type_text(self, text: str, interval: float = 0.05) -> str:
        """Type text using keyboard"""
        try:
            pg = _ensure_pyautogui()
            time.sleep(0.5)
            pg.typewrite(text, interval=interval)
            return f"⌨️ Typed: {text[:50]}{'...' if len(text)>50 else ''}"
        except Exception as e:
            # fallback for unicode
            try:
                pg.hotkey('ctrl', 'a')
                import pyperclip
                pyperclip.copy(text)
                pg.hotkey('ctrl', 'v')
                return f"⌨️ Typed (clipboard): {text[:50]}"
            except:
                return f"❌ Error: {e}"

    def press_key(self, key: str) -> str:
        """Press a keyboard key (enter, escape, tab, f5, etc.)"""
        try:
            pg = _ensure_pyautogui()
            pg.press(key)
            return f"⌨️ Pressed: {key}"
        except Exception as e:
            return f"❌ Error: {e}"

    def hotkey(self, *keys) -> str:
        """Press key combination (ctrl+c, alt+tab, etc.)"""
        try:
            pg = _ensure_pyautogui()
            pg.hotkey(*keys)
            return f"⌨️ Hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"❌ Error: {e}"

    def scroll(self, amount: int, x: int = None, y: int = None) -> str:
        """Scroll up (positive) or down (negative)"""
        try:
            pg = _ensure_pyautogui()
            if x and y:
                pg.scroll(amount, x=x, y=y)
            else:
                pg.scroll(amount)
            direction = "up" if amount > 0 else "down"
            return f"🖱️ Scrolled {direction} by {abs(amount)}"
        except Exception as e:
            return f"❌ Error: {e}"

    def open_app(self, app_name: str) -> str:
        """Open application by name"""
        try:
            apps = {
                "chrome": "start chrome",
                "firefox": "start firefox",
                "notepad": "start notepad",
                "explorer": "start explorer",
                "calculator": "start calc",
                "telegram": "start telegram",
                "vscode": "start code",
                "cmd": "start cmd",
                "powershell": "start powershell",
                "task manager": "start taskmgr",
            }
            cmd = apps.get(app_name.lower(), f"start {app_name}")
            subprocess.Popen(cmd, shell=True)
            return f"🚀 Opening: {app_name}"
        except Exception as e:
            return f"❌ Error opening {app_name}: {e}"

    def get_mouse_position(self) -> str:
        """Get current mouse position"""
        try:
            pg = _ensure_pyautogui()
            pos = pg.position()
            size = pg.size()
            return f"🖱️ Mouse at: ({pos.x}, {pos.y})\n🖥️ Screen size: {size.width}x{size.height}"
        except Exception as e:
            return f"❌ Error: {e}"

    def screenshot_region(self, x: int, y: int, w: int, h: int) -> str:
        """Take screenshot of specific region"""
        try:
            pg = _ensure_pyautogui()
            from pathlib import Path
            import time as _time
            path = Path.home() / "ai-agent" / "screenshots" / f"region_{int(_time.time())}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            img = pg.screenshot(region=(x, y, w, h))
            img.save(str(path))
            return f"📸 Region screenshot saved: {path.name}"
        except Exception as e:
            return f"❌ Error: {e}"

    def write_to_active_window(self, text: str) -> str:
        """Type text into currently active window"""
        try:
            pg = _ensure_pyautogui()
            time.sleep(0.3)
            # Use clipboard for unicode support
            try:
                import pyperclip
                pyperclip.copy(text)
                pg.hotkey('ctrl', 'v')
            except:
                pg.typewrite(text, interval=0.03)
            return f"⌨️ Written to active window: {text[:60]}"
        except Exception as e:
            return f"❌ Error: {e}"
