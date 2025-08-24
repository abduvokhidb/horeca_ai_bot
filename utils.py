# utils.py — vaqt/sana utilitlar, HH:MM DD.MM.YYYY format
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

# Asosiy formatlar
FMT_DB = "%Y-%m-%d %H:%M:%S"      # DB (ISO-ish)
FMT_HUMAN = "%H:%M %d.%m.%Y"      # UI talabi

TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")
DMY_RE  = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b")
YMD_RE  = re.compile(r"\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b")

SHEVA_OFFSETS = {
    # sheva & sinonimlar → kun offset
    "indin": 2, "indinga": 2, "послезавтра": 2,
    "ertaga": 1, "завтра": 1,
    "bugun": 0, "сегодня": 0, "today": 0,
}

def to_db_str(dt: datetime) -> str:
    return dt.strftime(FMT_DB)

def to_human_str(dt: datetime) -> str:
    return dt.strftime(FMT_HUMAN)

def parse_human_or_natural(text: str, base_dt: datetime, tz: ZoneInfo) -> Optional[datetime]:
    """Matndan datetime olish:
    - HH:MM DD.MM.YYYY (talab)
    - YYYY-MM-DD HH:MM yoki DD.MM.YYYY [HH:MM]
    - 'ertaga 10:00', 'indin 18:00' va h.k.
    """
    t = (text or "").strip().lower()

    # 1) HH:MM DD.MM.YYYY (asosiy)
    m_time = TIME_RE.search(t)
    m_dmy  = DMY_RE.search(t)
    if m_time and m_dmy:
        hh, mm = int(m_time.group(1)), int(m_time.group(2))
        d, mo, y = int(m_dmy.group(1)), int(m_dmy.group(2)), int(m_dmy.group(3))
        if y < 100: y += 2000
        try:
            return datetime(y, mo, d, hh, mm, tzinfo=tz)
        except Exception:
            pass

    # 2) YYYY-MM-DD [HH:MM]
    m_ymd = YMD_RE.search(t)
    if m_ymd:
        y, mo, d = map(int, m_ymd.groups())
        hh, mm = 18, 0
        if m_time: hh, mm = int(m_time.group(1)), int(m_time.group(2))
        try:
            return datetime(y, mo, d, hh, mm, tzinfo=tz)
        except Exception:
            pass

    # 3) DD.MM.YYYY [HH:MM]
    if m_dmy:
        d, mo, y = int(m_dmy.group(1)), int(m_dmy.group(2)), int(m_dmy.group(3))
        if y < 100: y += 2000
        hh, mm = 18, 0
        if m_time: hh, mm = int(m_time.group(1)), int(m_time.group(2))
        try:
            return datetime(y, mo, d, hh, mm, tzinfo=tz)
        except Exception:
            pass

    # 4) Natural (ertaga/indin/...)
    for key, off in SHEVA_OFFSETS.items():
        if key in t:
            hh, mm = 18, 0
            if m_time:
                hh, mm = int(m_time.group(1)), int(m_time.group(2))
            d0 = (base_dt + timedelta(days=off)).date()
            try:
                return datetime(d0.year, d0.month, d0.day, hh, mm, tzinfo=tz)
            except Exception:
                return None

    return None
