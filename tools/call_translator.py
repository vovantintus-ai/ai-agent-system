"""
Call Translator — транскрибирует аудио звонка и переводит на нужный язык
Поддерживает: MP3, WAV, OGG, M4A, FLAC
"""
import os, subprocess, sys, json
from pathlib import Path
from datetime import datetime

OUT_DIR = Path.home() / "ai-agent" / "call_transcripts"

def _ensure_whisper():
    try:
        import whisper
        return whisper
    except ImportError:
        print("Installing whisper...")
        subprocess.run([sys.executable, "-m", "pip", "install",
                        "openai-whisper", "--break-system-packages"],
                       capture_output=True)
        import whisper
        return whisper

def _ensure_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False

def _translate_text(text: str, target_lang: str, source_lang: str, provider: str = "gemini") -> str:
    """Translate text using AI"""
    lang_names = {
        "ru": "Russian", "en": "English", "nl": "Dutch/Nederlands",
        "de": "German", "fr": "French", "es": "Spanish", "uk": "Ukrainian"
    }
    target_name = lang_names.get(target_lang, target_lang)
    source_name = lang_names.get(source_lang, source_lang)
    prompt = (f"Translate the following text from {source_name} to {target_name}. "
              f"Output ONLY the translation, nothing else:\n\n{text}")
    try:
        if provider == "gpt":
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000)
            return r.choices[0].message.content.strip()
        elif provider == "claude":
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
            r = client.messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=2000,
                messages=[{"role": "user", "content": prompt}])
            return r.content[0].text.strip()
        else:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
            model = genai.GenerativeModel("gemini-2.0-flash")
            r = model.generate_content(prompt)
            return r.text.strip()
    except Exception as e:
        return f"[Translation error: {e}]"


class CallTranslator:

    def transcribe_file(self, file_path: str, target_lang: str = "en",
                        provider: str = "gemini") -> str:
        """
        Transcribe audio file and translate to target language.
        target_lang: 'en', 'ru', 'nl', 'de', 'fr', 'es'
        """
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = Path(file_path)
        if not path.exists():
            return f"❌ File not found: {file_path}"

        # Check ffmpeg
        if not _ensure_ffmpeg():
            return ("❌ FFmpeg not installed.\n"
                    "Install it: https://ffmpeg.org/download.html\n"
                    "Or on Windows: winget install ffmpeg")

        try:
            whisper = _ensure_whisper()
        except Exception as e:
            return f"❌ Could not load Whisper: {e}\nTry: pip install openai-whisper"

        try:
            # Load Whisper model (base is fast and good enough)
            model = whisper.load_model("base")
            result = model.transcribe(str(path), fp16=False)

            original_text = result["text"].strip()
            detected_lang = result.get("language", "unknown")

            lang_names = {
                "ru": "Russian 🇷🇺", "en": "English 🇬🇧", "nl": "Dutch 🇳🇱",
                "de": "German 🇩🇪", "fr": "French 🇫🇷", "es": "Spanish 🇪🇸",
                "uk": "Ukrainian 🇺🇦"
            }
            detected_name = lang_names.get(detected_lang, detected_lang)
            target_name = lang_names.get(target_lang, target_lang)

            lines = [
                f"🎙️ **Call Transcript**",
                f"📁 File: {path.name}",
                f"🔍 Detected: {detected_name}",
                f"🌐 Translated to: {target_name}",
                f"⏱️ Duration: ~{int(len(original_text.split())/2.5)} sec",
                "",
                f"📝 **Original ({detected_lang.upper()}):**",
                original_text,
                "",
            ]

            # Translate if different language
            if detected_lang != target_lang and original_text:
                translation = _translate_text(
                    original_text, target_lang, detected_lang, provider)
                lines += [
                    f"🌐 **Translation ({target_lang.upper()}):**",
                    translation,
                    ""
                ]
            else:
                translation = original_text

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = OUT_DIR / f"transcript_{timestamp}.txt"
            save_content = "\n".join(lines)
            save_path.write_text(save_content, encoding="utf-8")
            lines.append(f"💾 Saved: {save_path}")

            return "\n".join(lines)

        except Exception as e:
            return f"❌ Transcription error: {e}"

    def transcribe_telegram_audio(self, file_path: str,
                                   target_lang: str = "en",
                                   provider: str = "gemini") -> str:
        """Transcribe audio received from Telegram"""
        return self.transcribe_file(file_path, target_lang, provider)

    def list_transcripts(self) -> str:
        """List saved transcripts"""
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(OUT_DIR.glob("*.txt"), reverse=True)[:10]
        if not files:
            return "📭 No transcripts saved yet."
        lines = [f"📋 **Saved transcripts ({len(files)}):**\n"]
        for f in files:
            size = f.stat().st_size // 1024
            lines.append(f"• {f.name} ({size}KB)")
        return "\n".join(lines)

    def get_transcript(self, filename: str) -> str:
        """Read a saved transcript"""
        path = OUT_DIR / filename
        if not path.exists():
            return f"❌ File not found: {filename}"
        return path.read_text(encoding="utf-8")[:4000]
