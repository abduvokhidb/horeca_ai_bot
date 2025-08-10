# source_quqon.py
import os
import re
import tempfile
import httpx
import easyocr
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

load_dotenv()

CHANNEL_URL = os.getenv("CHANNEL_URL")
if not CHANNEL_URL:
    raise RuntimeError("CHANNEL_URL .env faylda ko‘rsatilmagan")

# OCR initial
ocr_reader = easyocr.Reader(['en', 'ru', 'ar'], gpu=False)

def fetch_channel_posts(limit=10):
    """Telegram kanalini (t.me/s/<kanal>) yuklab olish."""
    r = httpx.get(CHANNEL_URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    posts = soup.select(".tgme_widget_message")
    return posts[:limit]

def parse_text_times(text):
    """
    Matndan masjid nomi va vaqtlarni ajratib olish.
    Uch alifbo: lotin, kiril, arab.
    """
    rows = []
    lines = text.split("\n")
    for line in lines:
        parts = re.split(r"\s{2,}|\t", line.strip())
        if len(parts) >= 2:
            masjid = parts[0].strip()
            vaqtlar = [p.strip() for p in parts[1:] if re.match(r"\d{1,2}:\d{2}", p)]
            if masjid and vaqtlar:
                rows.append({"masjid": masjid, "vaqtlar": vaqtlar})
    return rows

def ocr_image_times(image_bytes):
    """Rasmdan OCR orqali vaqtlarni o‘qish."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    try:
        result = ocr_reader.readtext(tmp_path, detail=0)
        text = "\n".join(result)
        return parse_text_times(text)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def get_latest_table():
    """
    Kanaldagi eng so‘nggi postlardan jadval olish.
    Avval matndan, bo‘lmasa rasm OCR’dan.
    """
    posts = fetch_channel_posts(limit=10)
    all_rows = []
    for post in posts:
        # Matnli qismi
        text_block = post.select_one(".tgme_widget_message_text")
        if text_block:
            rows = parse_text_times(text_block.get_text("\n"))
            if rows:
                all_rows.extend(rows)
                continue
        # Rasmli qismi
        img_tag = post.select_one("a.tgme_widget_message_photo_wrap")
        if img_tag and 'style' in img_tag.attrs:
            style = img_tag['style']
            match = re.search(r"url\('(.*?)'\)", style)
            if match:
                img_url = match.group(1)
                img_data = httpx.get(img_url, timeout=20).content
                rows = ocr_image_times(img_data)
                if rows:
                    all_rows.extend(rows)
    return all_rows

def to_text_table(rows):
    """Natijani matnli jadvalga aylantirish."""
    lines = []
    for r in rows:
        line = f"{r['masjid']}: " + ", ".join(r['vaqtlar'])
        lines.append(line)
    return "\n".join(lines)
