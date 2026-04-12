"""
Voice Tools - Windows compatible speech recognition via Whisper
"""

import os
import tempfile
import subprocess
import logging
import platform

logger = logging.getLogger(__name__)

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
IS_WINDOWS = platform.system() == "Windows"

_whisper_model = None


def _load_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        logger.info(f"Loading Whisper model '{WHISPER_MODEL}'...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        logger.info("Whisper loaded!")
    return _whisper_model


def _find_ffmpeg():
    """Find ffmpeg executable on Windows"""
    # Check common Windows locations
    candidates = [
        "ffmpeg",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
    ]
    for candidate in candidates:
        try:
            result = subprocess.run([candidate, "-version"],
                                    capture_output=True, timeout=5)
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


class VoiceTools:
    async def transcribe_telegram_voice(self, voice_file) -> str:
        """Download voice message from Telegram and transcribe"""
        try:
            # Temp files
            ogg_fd, ogg_path = tempfile.mkstemp(suffix=".ogg")
            wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(ogg_fd)
            os.close(wav_fd)

            try:
                await voice_file.download_to_drive(ogg_path)

                # Try converting with ffmpeg
                ffmpeg = _find_ffmpeg()
                converted = False

                if ffmpeg:
                    result = subprocess.run(
                        [ffmpeg, "-i", ogg_path, "-ar", "16000", "-ac", "1",
                         wav_path, "-y", "-loglevel", "quiet"],
                        capture_output=True, timeout=30
                    )
                    converted = result.returncode == 0

                audio_path = wav_path if converted else ogg_path
                return self._transcribe(audio_path)

            finally:
                for p in [ogg_path, wav_path]:
                    try:
                        if os.path.exists(p):
                            os.remove(p)
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    def _transcribe(self, audio_path: str) -> str:
        model = _load_model()
        result = model.transcribe(audio_path, fp16=False)
        text = result["text"].strip()
        return text if text else "Could not recognize speech"
