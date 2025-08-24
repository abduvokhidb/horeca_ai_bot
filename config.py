# config.py
"""
Konfiguratsiya (Render/Heroku/docker .env uchun).
- Production: TELEGRAM_BOT_TOKEN majburiy, bo'sh bo'lsa xatolik.
- Developer-friendly: oqilona defaultlar bor, lekin productionda .env bilan to'liq boshqariladi.
"""

import os
from zoneinfo import ZoneInfo


def _getenv_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


class Config:
    # --- Majburiy ---
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not TELEGRAM_BOT_TOKEN:
        # Production xavfsizligi: token bo'sh bo'lmasin
        raise RuntimeError("TELEGRAM_BOT_TOKEN bo'sh bo'lmasligi kerak")

    # Bot username (deep-link uchun). @ belgisisiz saqlaymiz.
    # Masalan: BOT_USERNAME="AITaskBot" (emas, "@AITaskBot" emas)
    BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")

    # SQLite fayl yo'li (dev uchun oqilona default)
    DATABASE_PATH = os.getenv("DATABASE_PATH", "taskbot.db")

    # Vaqt zonasi (default: Asia/Tashkent)
    TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent"))

    # Eslatma va manager report vaqtlar (HH:MM) — bot.py shu formatni kutadi
    MORNING_REMINDER  = os.getenv("MORNING_REMINDER", "09:00")
    EVENING_REMINDER  = os.getenv("EVENING_REMINDER", "18:00")
    DAILY_REPORT_TIME = os.getenv("DAILY_REPORT_TIME", "18:00")

    # Til (languages.py bilan mos)
    DEFAULT_LANG = os.getenv("DEFAULT_LANG", "uz")

    # Kim manager?
    # Eslatma: bot.py bu qiymatlarni .split(",") bilan ishlatadi, shuning uchun string ko'rinishida qoldiramiz.
    MANAGER_IDS       = os.getenv("MANAGER_IDS", "")         # misol: "12345678,98765432"
    MANAGER_USERNAMES = os.getenv("MANAGER_USERNAMES", "")   # misol: "boss,pm,teamlead"

    # AI (ixtiyoriy). API KEY bo'lmasa bot fallback parser bilan ishlaydi.
    OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
    # Botdagi default model: gpt-4o-mini (xohlasangiz almashtiring)
    OPENAI_TASK_MODEL = os.getenv("OPENAI_TASK_MODEL", "gpt-4o-mini")

    # Log darajasi: DEBUG | INFO | WARNING | ERROR
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # --- Webhook / Polling boshqaruvi (bot.py bilan mos) ---
    # Render/Heroku-da webhook ishlatish uchun:
    # USE_WEBHOOK=1 yoki RENDER_EXTERNAL_URL mavjud bo'lsa — webhook yoqiladi.
    USE_WEBHOOK = _getenv_bool("USE_WEBHOOK", False)

    # Webhook bazaviy URL (agar RENDER_EXTERNAL_URL bor bo'lsa, bot.py undan foydalanadi)
    WEBHOOK_BASE = os.getenv("WEBHOOK_BASE", os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")

    # Telegram webhook tekshiruvi uchun ixtiyoriy maxfiy token
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

    # Render/Heroku port (run_webhook uchun kerak bo'ladi)
    PORT = int(os.getenv("PORT", "8080"))

    # --- Qo'shimcha dev qulayliklari ---
    # Polling interval va timeout ni xohlasangiz .env bilan boshqaring (bot.py defaultlarini saqlab qolgan holda)
    POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2.0"))
    POLL_TIMEOUT  = int(os.getenv("POLL_TIMEOUT", "30"))
