"""
TTS Tools - Text to Speech via Edge TTS (free, no API key needed)
Supports: Russian, Ukrainian, English - Female voices
"""

import asyncio
import tempfile
import os
import logging
import re

logger = logging.getLogger(__name__)

# Female voice mapping per language
VOICES = {
    "ru": "ru-RU-SvetlanaNeural",      # Russian female
    "uk": "uk-UA-PolinaNeural",         # Ukrainian female
    "en": "en-GB-SoniaNeural",          # English female (UK)
}

# Language detection keywords
LANG_HINTS = {
    "uk": ["що", "як", "де", "коли", "чому", "хто", "будь ласка", "дякую", "так", "ні",
           "можеш", "зроби", "відкрий", "знайди", "покажи"],
    "ru": ["что", "как", "где", "когда", "почему", "кто", "пожалуйста", "спасибо", "да", "нет",
           "можешь", "сделай", "открой", "найди", "покажи"],
}


def detect_language(text: str) -> str:
    """Detect language from text: ru, uk, or en"""
    text_lower = text.lower()

    uk_score = sum(1 for word in LANG_HINTS["uk"] if word in text_lower)
    ru_score = sum(1 for word in LANG_HINTS["ru"] if word in text_lower)

    # Check Cyrillic presence
    cyrillic = len(re.findall(r'[а-яёА-ЯЁ]', text))
    ukrainian = len(re.findall(r'[іїєґІЇЄҐ]', text))  # Ukrainian-specific chars

    if ukrainian > 0 or uk_score > ru_score:
        return "uk"
    elif cyrillic > 0 or ru_score > 0:
        return "ru"
    else:
        return "en"


def clean_text_for_tts(text: str) -> str:
    """Remove markdown and technical content not suitable for speech"""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '[код]', text)
    text = re.sub(r'`[^`]+`', '', text)
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove emojis
    text = re.sub(r'[^\w\s\.,!?;:\-\'\"()а-яёА-ЯЁіїєґІЇЄҐ]', '', text)
    # Clean up whitespace
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


async def text_to_speech(text: str, lang: str = None) -> str:
    """
    Convert text to speech using Edge TTS.
    Returns path to .mp3 file.
    """
    try:
        import edge_tts
    except ImportError:
        raise ImportError("edge-tts не установлен. Выполни: pip install edge-tts")

    # Auto-detect language if not specified
    if lang is None:
        lang = detect_language(text)

    voice = VOICES.get(lang, VOICES["en"])
    clean = clean_text_for_tts(text)

    # Limit TTS length (very long responses → summarize speech)
    if len(clean) > 500:
        clean = clean[:500] + "... и так далее."

    if not clean:
        clean = "Готово."

    # Generate audio
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()

    communicate = edge_tts.Communicate(clean, voice)
    await communicate.save(tmp.name)

    logger.info(f"TTS: lang={lang}, voice={voice}, chars={len(clean)}")
    return tmp.name


async def text_to_speech_bytes(text: str, lang: str = None) -> bytes:
    """Return MP3 audio as bytes"""
    path = await text_to_speech(text, lang)
    try:
        with open(path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(path):
            os.remove(path)
