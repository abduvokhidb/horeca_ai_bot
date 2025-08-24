import os
from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")  # t.me/<BOT_USERNAME>
    # Managers
    MANAGER_USERNAMES: str = os.getenv("MANAGER_USERNAMES", "")
    MANAGER_IDS: str = os.getenv("MANAGER_IDS", "")
    # DB
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "taskbot.db")

    # Time/locale
    TIMEZONE: ZoneInfo = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent"))
    MORNING_REMINDER: time = time.fromisoformat(os.getenv("MORNING_REMINDER", "09:00:00"))
    EVENING_REMINDER: time = time.fromisoformat(os.getenv("EVENING_REMINDER", "18:00:00"))
    DAILY_REPORT_TIME: time = time.fromisoformat(os.getenv("DAILY_REPORT_TIME", "18:00:00"))

    # AI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_TASK_MODEL: str = os.getenv("OPENAI_TASK_MODEL", "gpt-4o-mini")
    ENABLE_WHISPER: bool = os.getenv("ENABLE_WHISPER", "1") == "1"
    ENABLE_NL_AGENT: bool = os.getenv("ENABLE_NL_AGENT", "1") == "1"

    # Misc
    MAX_EMPLOYEES: int = int(os.getenv("MAX_EMPLOYEES", "200"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "uz")
