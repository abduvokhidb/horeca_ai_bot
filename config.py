# config.py
# Render/Heroku/.env muhitidagi o'zgaruvchilarni o'qiydi
import os
from zoneinfo import ZoneInfo

class Config:
    # --- majburiy ---
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN bo'sh bo'lmasligi kerak")

    # Bot username deep-link uchun (faqat nom, @siz): misol: "AITaskBot"
    BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")

    # SQLite yo‘li
    DATABASE_PATH = os.getenv("DATABASE_PATH", "taskbot.db")

    # Vaqt zonasi
    TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent"))

    # Eslatma va manager report vaqtlar (HH:MM)
    MORNING_REMINDER   = os.getenv("MORNING_REMINDER", "09:00")
    EVENING_REMINDER   = os.getenv("EVENING_REMINDER", "18:00")
    DAILY_REPORT_TIME  = os.getenv("DAILY_REPORT_TIME", "18:00")

    # Default til
    DEFAULT_LANG = os.getenv("DEFAULT_LANG", "uz")

    # Kim manager? ID va usernames (vergul bilan)
    MANAGER_IDS        = os.getenv("MANAGER_IDS", "")          # "123,456"
    MANAGER_USERNAMES  = os.getenv("MANAGER_USERNAMES", "")    # "boss,pm"

    # AI (ixtiyoriy) — yoqilmasa fallback parser ishlaydi
    OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
    OPENAI_TASK_MODEL  = os.getenv("OPENAI_TASK_MODEL", "gpt-4o-mini")

    # Log darajasi
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
