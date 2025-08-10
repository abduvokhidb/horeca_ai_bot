import os, re, time
from typing import List, Dict, Tuple
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Sozlamalar
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/s/namozvaqtitest")
TTL = 60 * 60 * 6  # 6 soat cache
UA = {"user-agent": "Mozilla/5.0 (PrayerTimesBot/1.0)"}

# Cache
CACHE: Dict[str, Dict] = {}

# Vaqt patternlari
TIME_TOKEN = r'([0-2]?\d)\s*[:٫：]\s*([0-5]\d)'
TIME_RE = re.compile(TIME_TOKEN)

# 3 alifbo: Lotin/Kiril/Arab sinonimlari
LABELS = {
    "bomdod": r'(Бомдод|Bomdod|Tong|الفجر|فجر|Fajr)',
    "peshin": r'(Пешин|Peshin|Tush|الظهر|ظهر|Dhuhr|Zuhr)',
    "asr":    r'(Аср|Asr|العصر|عصر)',
    "shom":   r'(Шом|Shom|Iftor|المغرب|مغرب|Maghrib)',
    "xufton": r'(Хуфтон|Xufton|Isha|العشاء|عشاء)'
}

MASJID_HINT = re.compile(r'(масжиди|masjidi|masjid|jome|jom[eai]|мечеть|mosque|جام[ع]|مسجد)', re.I)

# ------------ Transport ------------
def _get(url: str, timeout=40) -> str:
    with httpx.Client(timeout=timeout, headers=UA) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text

def _get_bytes(url: str, timeout=60) -> bytes:
    with httpx.Client(timeout=timeout, headers=UA) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.content

# ------------ HTML helpers ------------
def _extract_posts(soup: BeautifulSoup):
    return soup.select(".tgme_widget_message_bubble")

def _post_text(post) -> str:
    el = post.select_one(".tgme_widget_message_text")
    return el.get_text("\n", strip=True) if el else ""

def _post_images(post) -> List[str]:
    urls = []
    a = post.select_one(".tgme_widget_message_photo_wrap")
    if a and a.get("href"):
        urls.append(a["href"])
    img = post.select_one("img.tgme_widget_message_photo")
    if img and img.get("src"):
        urls.append(img["src"])
    return urls

# ------------ Parsing ------------
def _normalize_time(text: str) -> str:
    m = TIME_RE.search(text)
    if not m:
        return ""
    h = int(m.group(1)); mi = int(m.group(2))
    return f"{h:02d}:{mi:02d}"

def _times_from_text(txt: str) -> Dict[str, str]:
    def pick(lbl_pat):
        m = re.search(rf'{lbl_pat}[^\d\n]*{TIME_TOKEN}', txt, re.I)
        return _normalize_time(m.group(0)) if m else ""
    return {k: pick(v) for k, v in LABELS.items()}

def _masjid_name(lines: List[str]) -> str:
    for l in lines[:4]:
        if MASJID_HINT.search(l):
            return re.sub(r'#\S+','', l).strip()
    for l in lines:
        if len(l.strip()) >= 3:
            return re.sub(r'#\S+','', l).strip()
    return "Masjid"

# ------------ OCR (fallback) ------------
try:
    import numpy as np
    from PIL import Image
    from io import BytesIO
    import easyocr
    _ocr_reader = easyocr.Reader(['ru', 'en', 'ar'], gpu=False)
except Exception:
    _ocr_reader = None

def _ocr_from_bytes(b: bytes) -> str:
    if _ocr_reader is None:
        return ""
    try:
        im = Image.open(BytesIO(b)).convert("RGB")
        arr = np.array(im)
        res = _ocr_reader.readtext(arr, detail=0, paragraph=True)
        return "\n".join(res) if res else ""
    except Exception:
        return ""

def _enhance_with_ocr_if_needed(post, base_txt: str) -> Tuple[str, Dict[str, str]]:
    times = _times_from_text(base_txt)
    if sum(1 for v in times.values() if v) >= 3:
        return base_txt, times
    for u in _post_images(post):
        b = _get_bytes(u)
        ocr_txt = _ocr_from_bytes(b)
        if not ocr_txt:
            continue
        t2 = _times_from_text(ocr_txt)
        if sum(1 for v in t2.values() if v) >= 3:
            txt2 = (base_txt + "\n\n" + ocr_txt).strip() if base_txt else ocr_txt
            return txt2, t2
    return base_txt, times

# ------------ Public API ------------
def get_latest_table() -> List[Dict[str, str]]:
    """
    Kanaldagi eng so‘nggi postlardan namoz vaqtlarini chiqaradi.
    Natija: [{masjid, bomdod, peshin, asr, shom, xufton}, ...]
    """
    now = time.time()
    if "latest" in CACHE and now - CACHE["latest"]["ts"] < TTL:
        return CACHE["latest"]["data"]

    html_text = _get(CHANNEL_URL)
    soup = BeautifulSoup(html_text, "html.parser")
    posts = _extract_posts(soup)

    rows: List[Dict[str, str]] = []
    for p in posts[::-1]:  # eski->yangi; t.me/s da eng yangilari pastda
        txt = _post_text(p) or ""
        if not re.search(r'(Бомдод|Bomdod|Tong|الفجر|فجر|Fajr|Пешин|Peshin|Tush|الظهر|ظهر|Dhuhr|Zuhr|Аср|Asr|العصر|عصر|Шом|Shom|Iftor|المغرب|مغرب|Maghrib|Хуфтон|Xufton|Isha|العشاء|عشاء)', txt, re.I):
            if not _post_images(p):
                continue
        txt2, times = _enhance_with_ocr_if_needed(p, txt)
        if sum(1 for v in times.values() if v) < 3:
            continue

        lines = [l for l in (txt2 or txt).splitlines() if l.strip()]
        masjid = _masjid_name(lines)

        rows.append({
            "masjid": masjid,
            "bomdod": times.get("bomdod", ""),
            "peshin": times.get("peshin", ""),
            "asr":    times.get("asr", ""),
            "shom":   times.get("shom", ""),
            "xufton": times.get("xufton", "")
        })

    CACHE["latest"] = {"ts": now, "data": rows}
    return rows

def to_text_table(rows: List[Dict[str, str]]) -> str:
    header = "Masjid | Bomdod | Peshin | Asr | Shom | Xufton"
    sep    = "------ | ------- | ------ | --- | ---- | ------"
    out = [header, sep]
    for r in rows:
        out.append(f"{r['masjid']} | {r['bomdod']} | {r['peshin']} | {r['asr']} | {r['shom']} | {r['xufton']}")
    return "\n".join(out)
