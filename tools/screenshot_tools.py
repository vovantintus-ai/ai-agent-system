"""
Screenshot Tools - скриншоты экрана
"""
import os
from datetime import datetime
from pathlib import Path

SCREENSHOTS_DIR = Path.home() / "ai-agent" / "screenshots"


class ScreenshotTools:

    def take_screenshot(self) -> str:
        try:
            import PIL.ImageGrab as ImageGrab
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            filename = "screen_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
            path = SCREENSHOTS_DIR / filename
            img = ImageGrab.grab()
            img.save(str(path))
            return str(path)
        except ImportError:
            return "ERROR:install_pillow"
        except Exception as e:
            return "ERROR:" + str(e)

    def list_screenshots(self) -> str:
        if not SCREENSHOTS_DIR.exists():
            return "No screenshots yet."
        files = sorted(SCREENSHOTS_DIR.glob("*.png"))
        if not files:
            return "No screenshots yet."
        result = "Screenshots (" + str(len(files)) + "):\n"
        for f in files[-10:]:
            size = f.stat().st_size // 1024
            result += "- " + f.name + " (" + str(size) + "KB)\n"
        return result

    def delete_old_screenshots(self, keep=20) -> str:
        if not SCREENSHOTS_DIR.exists():
            return "No screenshots."
        files = sorted(SCREENSHOTS_DIR.glob("*.png"))
        to_del = files[:-keep] if len(files) > keep else []
        for f in to_del:
            f.unlink()
        return "Deleted " + str(len(to_del)) + " old screenshots"

