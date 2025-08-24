# config.py — .env dan o‘qiladi
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")  # @sizningbot emas, faqat username
    DATABASE_PATH = os.getenv("DATABASE_PATH", "taskbot.db")

    TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent"))

    MANAGER_IDS = os.getenv("MANAGER_IDS", "")
    MANAGER_USERNAMES = os.getenv("MANAGER_USERNAMES", "")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_TASK_MODEL = os.getenv("OPENAI_TASK_MODEL", "gpt-4o-mini")
    OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
