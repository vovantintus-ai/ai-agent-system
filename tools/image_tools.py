"""
Image Tools - работа с фото и изображениями
"""
import os
import base64
import aiohttp
from pathlib import Path


class ImageTools:

    async def analyze_image(self, image_path: str, question: str = "What do you see?") -> str:
        """Анализ изображения через Ollama vision"""
        path = Path(image_path)
        if not path.exists():
            return f"File not found: {image_path}"

        try:
            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
            payload = {
                "model": model,
                "prompt": question,
                "images": [image_data],
                "stream": False
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    data = await resp.json()
                    return data.get("response", "Could not analyze image")
        except Exception as e:
            return f"Image analysis error: {e}"

    async def analyze_telegram_photo(self, file_path: str, question: str = "") -> str:
        """Анализ фото полученного из Telegram"""
        q = question or "Describe this image in detail. What do you see?"
        return await self.analyze_image(file_path, q)

    def get_image_info(self, image_path: str) -> str:
        """Получить информацию об изображении"""
        try:
            path = Path(image_path)
            if not path.exists():
                return f"File not found: {image_path}"
            size = path.stat().st_size
            ext = path.suffix.lower()
            return f"File: {path.name}, Size: {size//1024}KB, Format: {ext}"
        except Exception as e:
            return f"Error: {e}"

    def list_images(self, directory: str = ".") -> str:
        """Список изображений в папке"""
        try:
            extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            path = Path(directory)
            images = [f.name for f in path.iterdir() if f.suffix.lower() in extensions]
            if not images:
                return "No images found"
            return f"Images in {directory}:\n" + "\n".join(images)
        except Exception as e:
            return f"Error: {e}"
