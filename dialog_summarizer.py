"""
Dialog Summarizer - auto summary after each conversation
"""
import asyncio
import os
from tools.memory_tools import MemoryTools

memory = MemoryTools()

PROMPT = """Write a brief 1-3 sentence summary in Russian of this conversation.
Focus on: topics discussed, decisions, tasks. Output ONLY the summary."""


async def _summarize_gpt(messages):
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        text = "\n".join([
            f"{m['role']}: {str(m.get('content', ''))[:200]}"
            for m in messages[-20:]
            if isinstance(m.get("content"), str)
        ])
        if not text.strip():
            return ""
        r = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": text}],
            max_tokens=150)
        return r.choices[0].message.content.strip()
    except Exception:
        return ""


async def _summarize_gemini(messages):
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.0-flash")
        text = "\n".join([str(m)[:100] for m in messages[-10:]])
        r = await asyncio.to_thread(model.generate_content, PROMPT + "\n\n" + text[:2000])
        return r.text.strip()
    except Exception:
        return ""


async def _summarize_claude(messages):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        text = "\n".join([
            f"{m['role']}: {str(m.get('content', ''))[:200]}"
            for m in messages[-20:]
            if isinstance(m.get("content"), str)
        ])
        if not text.strip():
            return ""
        r = await asyncio.to_thread(
            client.messages.create,
            model="claude-haiku-4-5-20251001", max_tokens=150,
            system=PROMPT, messages=[{"role": "user", "content": text}])
        return r.content[0].text.strip()
    except Exception:
        return ""


async def auto_summarize(agent, provider: str):
    """Summarize current dialog session and save to memory"""
    try:
        msgs = getattr(agent, "messages", [])
        if len(msgs) < 2:
            return
        if provider == "gpt":
            summary = await _summarize_gpt(msgs)
        elif provider == "claude":
            summary = await _summarize_claude(msgs)
        else:
            summary = await _summarize_gemini(msgs)
        if summary:
            memory.save_dialog_summary(summary)
    except Exception as e:
        print(f"Summarize error: {e}")
