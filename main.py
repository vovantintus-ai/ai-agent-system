#!/usr/bin/env python3
"""
AI Agent - Telegram Bot
Supports: Google Gemini (free) + Claude (Anthropic)
On every start: asks which engine to use
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from tools.voice_tools import VoiceTools
from tools.tts_tools import text_to_speech, detect_language

import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
load_dotenv(encoding='utf-8-sig')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "").strip()
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID", "").strip()
VOICE_REPLY     = os.getenv("VOICE_REPLY", "true").lower() == "true"
AI_PROVIDER     = os.getenv("AI_PROVIDER", "gemini").strip().lower()

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set in .env")

# Load correct agent based on provider
if AI_PROVIDER == "claude":
    from agent_claude import Agent
    logger.info("🟣 Using Claude (Anthropic)")
elif AI_PROVIDER == "gpt":
    from agent_gpt import Agent
    logger.info("🟢 Using ChatGPT (OpenAI)")
elif AI_PROVIDER == "ollama":
    from agent_ollama import Agent
    logger.info("🦙 Using Ollama (Local FREE)")
else:
    from agent_gemini import Agent
    logger.info("🔵 Using Google Gemini")

agent       = Agent()
voice_tools = VoiceTools()


def check_access(update: Update) -> bool:
    return not ALLOWED_USER_ID or str(update.effective_user.id) == ALLOWED_USER_ID


async def send_reply(update: Update, text: str, lang: str = None):
    if len(text) > 4000:
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(text)

    if VOICE_REPLY:
        audio_path = None
        try:
            audio_path = await text_to_speech(text, lang)
            with open(audio_path, 'rb') as f:
                await update.message.reply_voice(voice=f)
        except Exception as e:
            logger.warning(f"TTS: {e}")
        finally:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        return
    if AI_PROVIDER == "gemini":   engine = "Google Gemini 🔵 (FREE)"
    elif AI_PROVIDER == "gpt":     engine = "ChatGPT 🟢 (OpenAI)"
    elif AI_PROVIDER == "ollama":  engine = "Ollama 🦙 (Local FREE)"
    else:                           engine = "Claude 🟣 (Anthropic)"
    await update.message.reply_text(
        f"👋 *AI Agent is active!*\n"
        f"🤖 Engine: *{engine}*\n\n"
        "I can:\n"
        "📁 Manage files\n"
        "📧 Email & calendar\n"
        "🌐 Search the internet\n"
        "⚡ Run commands & code\n"
        "🎙️ Voice in & out\n\n"
        "Speak or type in 🇷🇺 🇺🇦 🇬🇧\n\n"
        "/history — recent tasks\n"
        "/clear — reset conversation\n"
        "/engine — show current AI engine",
        parse_mode='Markdown'
    )


async def cmd_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        return
    if AI_PROVIDER == "gemini":   engine = "Google Gemini 🔵 (FREE)"
    elif AI_PROVIDER == "gpt":     engine = "ChatGPT 🟢 (OpenAI)"
    elif AI_PROVIDER == "ollama":  engine = "Ollama 🦙 (Local FREE)"
    else:                           engine = "Claude 🟣 (Anthropic)"
    await update.message.reply_text(f"🤖 Current engine: *{engine}*", parse_mode='Markdown')


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        return
    hist = agent.get_history()
    if not hist:
        await update.message.reply_text("No history yet.")
        return
    text = "📋 *Recent tasks:*\n\n"
    for i, item in enumerate(hist[-10:], 1):
        t = item['task']
        text += f"{i}. {t[:60]}...\n" if len(t) > 60 else f"{i}. {t}\n"
    await update.message.reply_text(text, parse_mode='Markdown')


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        return
    agent.clear_context()
    await update.message.reply_text("✅ Context cleared.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    task = update.message.text
    lang = detect_language(task)
    await update.message.reply_text("⏳...")
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = await agent.run(task)
        await send_reply(update, result, lang)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    await update.message.reply_text("🎙️ Listening...")
    try:
        voice_file = await update.message.voice.get_file()
        task = await voice_tools.transcribe_telegram_voice(voice_file)
        lang = detect_language(task)
        await update.message.reply_text(f"🗣️ _{task}_", parse_mode='Markdown')
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = await agent.run(task)
        await send_reply(update, result, lang)
    except Exception as e:
        logger.error(f"Voice error: {e}")
        await update.message.reply_text(f"❌ Voice error: {str(e)}")


def main():
    engine = "Gemini" if AI_PROVIDER == "gemini" else "Claude"
    logger.info(f"🚀 Agent starting with {engine}...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("clear",   cmd_clear))
    app.add_handler(CommandHandler("engine",  cmd_engine))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("✅ Ready! Waiting for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
