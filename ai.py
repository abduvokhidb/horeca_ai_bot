# ai.py — OpenAI yordamchi qatlam
import os
import asyncio
from typing import Optional, Dict, List

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_TASK_MODEL = os.getenv("OPENAI_TASK_MODEL", "gpt-4o-mini")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

def ai_available() -> bool:
    return bool(OPENAI_API_KEY)

async def transcribe_voice(file_path: str) -> str:
    """Ovoz -> matn (fallback: bo‘sh)"""
    if not ai_available():
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        with open(file_path, "rb") as f:
            tr = client.audio.transcriptions.create(model=OPENAI_TRANSCRIBE_MODEL, file=f)
        return (tr.text or "").strip()
    except Exception:
        return ""

async def translate_text(text: str, target_lang_name: str) -> str:
    """Matnni ko‘rsatilgan tilga tarjima (masalan, 'Uzbek', 'Russian', 'Kazakh')."""
    if not ai_available() or not text:
        return text
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        sys = f"Translate the user content to {target_lang_name}. Keep meaning; be concise."
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=OPENAI_TASK_MODEL,
            messages=[{"role":"system","content":sys},{"role":"user","content":text}],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return text

async def pm_assistant_answer(prompt: str, context_hint: str = "") -> str:
    """PM assistant: savol-javob, tahlil, tavsiyalar."""
    if not ai_available():
        return "AI o‘chirilgan. OPENAI_API_KEY sozlang."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        sys = (
            "Siz Project Manager Assistant’siz. Task va resurslarni tahlil qiling, deadline va yuklama bo‘yicha "
            "tavsiyalar bering, kerak bo‘lsa savollar bering. Javobni aniq, punktli va qisqa yozing."
        )
        if context_hint:
            sys += f"\nContext: {context_hint}"
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=OPENAI_TASK_MODEL,
            messages=[{"role":"system","content":sys},{"role":"user","content":prompt}],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"AI xatolik: {e}"

async def parse_task_from_text(text: str, now_iso: str, known_usernames: List[str]) -> Dict:
    """
    Matndan {assignee, title, deadline, priority} JSON chiqarish.
    """
    import json
    if not ai_available():
        # Fallback — bot natural parseri bosqichida yakunlanadi
        return {"assignee":"","title":text.strip() or "No title","deadline":"","priority":"Medium"}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        sys = (
            "Siz Telegram uchun Task Manager agentisiz. Kirish matnidan vazifa maydonlarini ajrating. "
            "Faqat JSON qaytaring: {\"assignee\":\"@username yoki bo‘sh\",\"title\":\"...\","
            "\"deadline\":\"YYYY-MM-DD HH:MM\",\"priority\":\"Low|Medium|High|Urgent\"}."
            "Agar username ism bilan berilgan bo‘lsa, known_usernames bo‘yicha mos @username ni belgilang."
        )
        user = f"now={now_iso}\nknown_usernames={known_usernames}\ntext={text}"
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=OPENAI_TASK_MODEL,
            messages=[{"role":"system","content":sys},{"role":"user","content":user}],
            response_format={"type":"json_object"},
            temperature=0.1,
        )
        raw = (resp.choices[0].message.content or "{}").strip()
        return json.loads(raw)
    except Exception:
        return {"assignee":"","title":text.strip() or "No title","deadline":"","priority":"Medium"}
