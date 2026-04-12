# AI Agent System

A multi-engine AI assistant with 26+ tool modules, voice I/O, and business automation capabilities. Built for real-world freelance operations.

## Architecture

```
TELEGRAM BOT (main.py)
    |
    |-- AI Engine (choose one at startup)
    |   |-- Claude (Anthropic)
    |   |-- GPT (OpenAI)
    |   |-- Gemini (Google)
    |   |-- Ollama (Local/Offline)
    |
    |-- 26 Tool Modules
    |   |-- file_tools      - File operations
    |   |-- shell_tools     - System commands
    |   |-- browser_tools   - Web search & scraping
    |   |-- email_tools     - Send emails + calendar events
    |   |-- voice_tools     - Speech-to-text (Telegram voice)
    |   |-- tts_tools       - Text-to-speech (edge-tts)
    |   |-- memory_tools    - Persistent dialog history
    |   |-- finance_tools   - Financial calculations
    |   |-- invoice_tools   - Invoice generation
    |   |-- crm_tools       - Contact management
    |   |-- scraper_tools   - Web scraping
    |   |-- image_tools     - Image processing
    |   |-- excel_tools     - Spreadsheet operations
    |   |-- document_tools  - Document handling
    |   |-- pc_control      - Desktop automation
    |   |-- pc_voice        - PC voice commands
    |   |-- monitor_tools   - System monitoring
    |   |-- reminder_tools  - Reminders & scheduling
    |   |-- learning_tools  - Self-improvement
    |   |-- screenshot_tools- Screen capture
    |   |-- opera_tools     - Browser automation
    |   |-- call_translator - Real-time translation
    |   |-- price_monitor   - Market price tracking
    |   |-- briefing_tools  - Daily briefings
    |   +-- and more...
    |
    |-- Market Monitor (standalone)
    |   |-- Upwork RSS feed scanner
    |   |-- Reddit job board scanner
    |   +-- Telegram notifications
    |
    |-- Kabanchik Agent (standalone)
    |   |-- Freelancer search (Playwright)
    |   +-- Rating & price extraction
    |
    +-- Desktop Agent (standalone)
        |-- Windows PC control via GUI
        |-- App launcher, file manager
        +-- Voice commands
```

## Features

- **4 AI engines** — Switch between Claude, GPT, Gemini, or local Ollama
- **Voice I/O** — Send voice messages, get voice responses
- **26 tool modules** — File ops, email, web search, PC control, finance, CRM
- **Job monitoring** — Auto-scan Upwork & Reddit for freelance opportunities
- **Freelancer discovery** — Find talent on Kabanchik.ua with auto-scraping
- **Desktop automation** — Control Windows PC via Telegram commands
- **Persistent memory** — Conversation history survives restarts
- **Multi-language** — Supports EN, RU, UA with auto-detection

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ai-agent-system.git
cd ai-agent-system

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium  # for web scraping

# 3. Configure
cp .env.example .env
# Edit .env with your API keys

# 4. Run the main bot
python main.py

# 5. Run market monitor (separate terminal)
python market_monitor.py

# 6. Run freelancer scanner (separate terminal)
python kabanchik_agent.py
```

## Configuration

Copy `.env.example` to `.env`:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_gpt_key
GEMINI_API_KEY=your_gemini_key
ALLOWED_USER_ID=your_telegram_chat_id
AI_PROVIDER=gemini  # claude | gpt | gemini | ollama
VOICE_REPLY=true
```

## Project Structure

```
.
|-- main.py               # Telegram bot entry point
|-- agent_claude.py       # Claude engine with tool calling
|-- agent_gpt.py          # GPT engine with tool calling
|-- agent_gemini.py       # Gemini engine with tool calling
|-- agent_ollama.py       # Ollama (local) engine
|-- agent_pro.py          # Enhanced desktop agent
|-- desktop_agent.py      # Windows desktop automation GUI
|-- market_monitor.py     # Upwork/Reddit job scanner
|-- kabanchik_agent.py    # Freelancer search agent
|-- manager.py            # Diagnostic & installer UI
|-- dialog_summarizer.py  # Conversation summarization
|-- requirements.txt      # Python dependencies
|-- tools/                # 26 tool modules
|   |-- file_tools.py
|   |-- voice_tools.py
|   |-- email_tools.py
|   +-- ...
|-- data/                 # Persistent storage
|   |-- seen_jobs.json
|   +-- shared_context.json
+-- .env                  # API keys (not in repo)
```

## Tech Stack

- **Python 3.10+**
- **python-telegram-bot** — Async Telegram integration
- **Anthropic / OpenAI / Google AI SDKs** — Multi-engine AI
- **Playwright** — Headless browser for web scraping
- **edge-tts** — Text-to-speech
- **Whisper** — Speech recognition
- **aiohttp** — Async HTTP requests
- **tkinter** — Desktop GUI

## Use Cases

- Personal AI assistant via Telegram
- Freelance job monitoring & alerting
- Freelancer talent scouting
- Desktop PC remote control
- Business email automation
- Voice-controlled workflows

## License

MIT
