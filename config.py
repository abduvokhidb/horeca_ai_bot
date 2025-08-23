import os
from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# 🔹 Environment o'zgaruvchilarni yuklash
load_dotenv()


@dataclass(frozen=True)
class Config:
    # --- Telegram & API kalitlar ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # --- Database ---
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "taskbot.db")

    # --- Manager sozlamalari ---
    MANAGER_USERNAMES: str = os.getenv("MANAGER_USERNAMES", "")
    MANAGER_IDS: str = os.getenv("MANAGER_IDS", "")

    # --- Til va vaqt ---
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "uz")
    TIMEZONE: ZoneInfo = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent"))

    # --- Reminder va report vaqtlari ---
    MORNING_REMINDER: time = time.fromisoformat(os.getenv("MORNING_REMINDER", "09:00:00"))
    EVENING_REMINDER: time = time.fromisoformat(os.getenv("EVENING_REMINDER", "18:00:00"))
    DAILY_REPORT_TIME: time = time.fromisoformat(os.getenv("DAILY_REPORT_TIME", "18:00:00"))

    # --- Funksiya flaglari ---
    ENABLE_WHISPER: bool = os.getenv("ENABLE_WHISPER", "1") == "1"   # ovozdan task parse
    ENABLE_PARSER: bool = os.getenv("ENABLE_PARSER", "1") == "1"     # matndan deadline parse

    # --- Limitlar ---
    MAX_EMPLOYEES: int = int(os.getenv("MAX_EMPLOYEES", "50"))

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- Invite link sozlamalari ---
    INVITE_BASE_URL: str = os.getenv("INVITE_BASE_URL", "https://t.me/yourbot?start=")


# 🔹 Priority darajalari (tasklar uchun)
PRIORITY_LEVELS = ["Low", "Medium", "High", "Urgent"]
DEFAULT_PRIORITY = "Medium"

# 🔹 Statuslar (kelajakda holatlarni kuzatish uchun)
TASK_STATUSES = ["new", "accepted", "rejected", "done", "pending"]


def get_manager_usernames() -> set[str]:
    """Manager usernamelarini set qilib qaytaradi."""
    raw = Config.MANAGER_USERNAMES
    return {x.strip().lower() for x in raw.split(",") if x.strip()} if raw else set()


def get_manager_ids() -> set[int]:
    """Manager ID larini set qilib qaytaradi."""
    raw = Config.MANAGER_IDS
    if not raw:
        return set()
    out = set()
    for p in raw.split(","):
        p = p.strip()
        if not p:
            continue
        try:
            out.add(int(p))
        except ValueError:
            pass
    return out
