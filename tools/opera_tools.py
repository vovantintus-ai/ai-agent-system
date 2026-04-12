"""
Opera Browser Tools - управление браузером Opera через Selenium
- Открывать URL и делать скриншот
- Получать текст страницы
- Работает с авторизацией (через профиль пользователя)
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

OPERA_PATH       = r"C:\Users\YOUR_USER\AppData\Local\Programs\Opera\opera.exe"
SCREENSHOTS_DIR  = Path.home() / "ai-agent" / "screenshots"

_driver = None


def _get_driver(headless: bool = False):
    """Получить или создать экземпляр драйвера Opera"""
    global _driver
    if _driver is not None:
        try:
            _ = _driver.current_url   # проверяем жив ли
            return _driver
        except Exception:
            _driver = None

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.binary_location = OPERA_PATH

    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=service, options=options)
    _driver.set_page_load_timeout(30)
    logger.info("Opera browser started")
    return _driver


class OperaTools:

    def open_and_screenshot(self, url: str, wait: int = 3) -> tuple[str, str]:
        """
        Открыть URL в Opera и сделать скриншот.
        Возвращает (path_to_screenshot, page_title).
        path начинается с "ERROR:" при ошибке.
        """
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            driver = _get_driver()
            driver.get(url)
            time.sleep(wait)  # ждём загрузки

            title = driver.title or url

            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            filename = "opera_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
            path = str(SCREENSHOTS_DIR / filename)
            driver.save_screenshot(path)
            logger.info(f"Screenshot saved: {path}")
            return path, title

        except Exception as e:
            logger.error(f"Opera error: {e}")
            return f"ERROR:{e}", ""

    def get_page_text(self, url: str = None, wait: int = 2) -> str:
        """Получить текст текущей или указанной страницы"""
        try:
            driver = _get_driver()
            if url:
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                driver.get(url)
                time.sleep(wait)
            text = driver.find_element("tag name", "body").text
            if len(text) > 3000:
                text = text[:3000] + "\n...[текст обрезан]"
            return text if text.strip() else "(страница пустая или не загрузилась)"
        except Exception as e:
            return f"ERROR:{e}"

    def navigate(self, url: str) -> str:
        """Просто открыть URL без скриншота"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            driver = _get_driver()
            driver.get(url)
            time.sleep(1)
            return f"✅ Открыто: {driver.title}\n🔗 {url}"
        except Exception as e:
            return f"ERROR:{e}"

    def click_css(self, selector: str) -> str:
        """Кликнуть на элемент по CSS селектору"""
        try:
            driver = _get_driver()
            el = driver.find_element("css selector", selector)
            el.click()
            time.sleep(0.5)
            return f"✅ Кликнул: {selector}"
        except Exception as e:
            return f"ERROR:{e}"

    def type_into(self, selector: str, text: str) -> str:
        """Ввести текст в поле"""
        try:
            driver = _get_driver()
            el = driver.find_element("css selector", selector)
            el.clear()
            el.send_keys(text)
            return f"✅ Введён текст в {selector}"
        except Exception as e:
            return f"ERROR:{e}"

    def current_url(self) -> str:
        """Получить текущий URL"""
        try:
            return _driver.current_url if _driver else "Браузер не открыт"
        except Exception:
            return "Браузер не открыт"

    def close(self) -> str:
        """Закрыть браузер"""
        global _driver
        if _driver:
            try:
                _driver.quit()
            except Exception:
                pass
            _driver = None
            return "✅ Opera закрыта"
        return "Браузер уже закрыт"
