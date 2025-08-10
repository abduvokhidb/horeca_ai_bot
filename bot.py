import os
import json
import asyncio
import logging
import threading
import math
import re
import requests
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Set, Optional
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import openai
from bs4 import BeautifulSoup
import schedule
import time
from difflib import SequenceMatcher
import hashlib

# OCR uchun (agar mavjud bo'lsa)
try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ OCR kutubxonalari mavjud")
except ImportError:
    OCR_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ OCR kutubxonalari yo'q - faqat matn tahlili")

# Health check uchun Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return 'Bot ishlaydi', 200

@app.route('/')
def home():
    return 'Masjidlar Bot - Kanal Monitoring Active', 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot sozlamalari - Environment variables dan olish
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'quqonnamozvaqti')
CHANNEL_URL = f'https://t.me/s/{CHANNEL_USERNAME}'

# Test mode detection
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
if TEST_MODE:
    logger.info("🧪 TEST MODE faol!")
    test_channel = os.getenv('TEST_CHANNEL_USERNAME', CHANNEL_USERNAME)
    CHANNEL_USERNAME = test_channel
    CHANNEL_URL = f'https://t.me/s/{CHANNEL_USERNAME}'

logger.info(f"🎯 Monitoring kanal: @{CHANNEL_USERNAME}")
logger.info(f"🌐 Kanal URL: {CHANNEL_URL}")

# Environment variables mavjudligini tekshirish
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable kerak!")
    exit(1)

# OpenAI sozlamalari
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Global variables
bot_app = None
user_settings = {}
last_posts_hash = {}  # Post'larning hash'ini saqlash uchun

# 3 ALIFBO PATTERN MATCHING SYSTEM
# =====================================

MASJIDLAR_3_ALIFBO = {
    "NORBUTABEK": {
        "full_name": "NORBUTABEK JOME MASJIDI",
        "patterns": {
            "lotin": ["norbutabek", "norbu tabek", "norbu-tabek", "norbutabek jome", "norbutabek masjid"],
            "kiril": ["норбутабек", "норбу табек", "норбу-табек", "норбутабек жоме", "норбутабек масжид"],
            "arab": ["نوربوتابيك", "نوربو تابيك", "نوربوتابيك جومعه", "مسجد نوربوتابيك"]
        }
    },
    "GISHTLIK": {
        "full_name": "GISHTLIK JOME MASJIDI",
        "patterns": {
            "lotin": ["gishtlik", "g'ishtlik", "gʻishtlik", "gishtlik jome", "gishtlik masjid"],
            "kiril": ["гиштлик", "ғиштлик", "гиштлик жоме", "гиштлик масжид"],
            "arab": ["غیشتلیك", "گشتلیك", "غیشتلیك جومعه", "مسجد غیشتلیك"]
        }
    },
    "SHAYXULISLOM": {
        "full_name": "SHAYXULISLOM JOME MASJIDI",
        "patterns": {
            "lotin": ["shayxulislom", "shayx ul islom", "shaykh ul islam", "shayxulislom jome"],
            "kiril": ["шайхулислом", "шайх ул ислом", "шайхулислом жоме"],
            "arab": ["شیخ الاسلام", "شایخ الاسلام", "شیخ الاسلام جومعه"]
        }
    },
    "HADYA_HOJI": {
        "full_name": "HADYA HOJI SHALDIRAMOQ JOME MASJIDI",
        "patterns": {
            "lotin": ["hadya hoji", "hadiya hoji", "shaldiramoq", "hadya hoji jome"],
            "kiril": ["хадя ходжи", "хадия ходжи", "шалдирамок", "хадя ходжи жоме"],
            "arab": ["هادیة حاجی", "شلدیرامق", "هادیة حاجی جومعه"]
        }
    },
    "AFGONBOG": {
        "full_name": "AFGONBOG JOME MASJIDI",
        "patterns": {
            "lotin": ["afgonbog", "afg'onbog", "avgonbog", "afgonbog jome"],
            "kiril": ["афгонбог", "авғонбог", "афгонбог жоме"],
            "arab": ["افغونبوغ", "افغانبوغ", "افغونبوغ جومعه"]
        }
    },
    "SAYYID_AXMADHON": {
        "full_name": "SAYYID AXMADHON HOJI JOME MASJIDI",
        "patterns": {
            "lotin": ["sayyid axmadhon", "sayyid ahmad", "axmadhon hoji", "sayyid axmadhon jome"],
            "kiril": ["саййид ахмадхон", "саййид ахмад", "ахмадхон ходжи", "саййид ахмадхон жоме"],
            "arab": ["سید احمدخان", "سید احمد", "احمدخان حاجی", "سید احمدخان جومعه"]
        }
    },
    "DEGRIZLIK": {
        "full_name": "DEGRIZLIK JOME MASJIDI",
        "patterns": {
            "lotin": ["degrizlik", "deg'rizlik", "degrızlik", "degrizlik jome"],
            "kiril": ["дегризлик", "деғризлик", "дегризлик жоме"],
            "arab": ["دگریزلیك", "دغریزلیك", "دگریزلیك جومعه"]
        }
    },
    "SHAYXON": {
        "full_name": "SHAYXON JOME MASJIDI",
        "patterns": {
            "lotin": ["shayxon", "shayx on", "sheikh on", "shayxon jome"],
            "kiril": ["шайхон", "шайх он", "шайхон жоме"],
            "arab": ["شیخون", "شیخ اون", "شیخون جومعه"]
        }
    },
    "ZINBARDOR": {
        "full_name": "ZINBARDOR JOME MASJIDI",
        "patterns": {
            "lotin": ["zinbardor", "zin bardor", "zinbar dor", "zinbardor jome"],
            "kiril": ["зинбардор", "зин бардор", "зинбардор жоме"],
            "arab": ["زینبردور", "زین بردور", "زینبردور جومعه"]
        }
    },
    "ZAYNUL_OBIDIN": {
        "full_name": "ZAYNUL OBIDIN AYRILISH JOME MASJIDI",
        "patterns": {
            "lotin": ["zaynul obidin", "zayn ul obidin", "ayrilish", "zaynul obidin jome"],
            "kiril": ["зайнул обидин", "зайн ул обидин", "айрилиш", "зайнул обидин жоме"],
            "arab": ["زین العابدین", "آیریلیش", "زین العابدین جومعه"]
        }
    },
    "HAZRATI_ABBOS": {
        "full_name": "HAZRATI ABBOS MOLBOZORI JOME MASJIDI",
        "patterns": {
            "lotin": ["hazrati abbos", "hazrat abbos", "molbozor", "hazrati abbos jome"],
            "kiril": ["хазрати аббос", "хазрат аббос", "молбозор", "хазрати аббос жоме"],
            "arab": ["حضرت عباس", "مولبازار", "حضرت عباس جومعه"]
        }
    },
    "SAODAT": {
        "full_name": "SAODAT JOME MASJIDI",
        "patterns": {
            "lotin": ["saodat", "sa'odat", "saadat", "saodat jome"],
            "kiril": ["саодат", "саъодат", "саодат жоме"],
            "arab": ["سعادت", "صعادت", "سعادت جومعه"]
        }
    },
    "TOLABOY": {
        "full_name": "MUHAMMAD SAID XUJA TOLABOY JOME MASJIDI",
        "patterns": {
            "lotin": ["tolaboy", "tola boy", "muhammad said", "said xuja", "tolaboy jome"],
            "kiril": ["толабой", "тола бой", "мухаммад саид", "саид хужа", "толабой жоме"],
            "arab": ["طلابوی", "محمد سعید", "سعید خواجه", "طلابوی جومعه"]
        }
    }
}

# 3 ALIFBO NAMAZ VAQTLARI PATTERNS
# ===================================

NAMAZ_VAQTLARI_3_ALIFBO = {
    "lotin": {
        "bomdod": r'(?:bomdod|fajr|subh|sahar|tong)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:peshin|zuhr|zuhur|öyle|tush)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:asr|ikindi|digar|tush)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:shom|maghrib|mag\'rib|axshom|kech)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:hufton|isha|xufton|kech|tun)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    },
    "kiril": {
        "bomdod": r'(?:бомдод|фажр|субх|сахар|тонг)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:пешин|зухр|зухур|ойле|туш)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:аср|икинди|дигар|туш)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:шом|магриб|мағриб|ахшом|кеч)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:хуфтон|иша|хуфтон|кеч|тун)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    },
    "arab": {
        "bomdod": r'(?:فجر|صبح|سحر|فجر)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:ظهر|زهر|ظهر)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:عصر|عشر|عصر)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:مغرب|مغریب|مغرب)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:عشاء|عشا|عیشا|عشاء)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    }
}

# Default namaz vaqtlari (backup uchun)
masjidlar_data = {
    "NORBUTABEK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:45", "Shom": "19:35", "Hufton": "21:15"},
    "GISHTLIK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:15", "Shom": "19:30", "Hufton": "21:00"},
    "SHAYXULISLOM": {"Bomdod": "04:45", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"},
    "HADYA_HOJI": {"Bomdod": "04:55", "Peshin": "12:50", "Asr": "17:30", "Shom": "19:15", "Hufton": "20:55"},
    "AFGONBOG": {"Bomdod": "04:50", "Peshin": "12:50", "Asr": "17:30", "Shom": "19:20", "Hufton": "20:55"},
    "SAYYID_AXMADHON": {"Bomdod": "04:50", "Peshin": "12:50", "Asr": "17:20", "Shom": "19:20", "Hufton": "21:15"},
    "DEGRIZLIK": {"Bomdod": "04:30", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"},
    "SHAYXON": {"Bomdod": "04:40", "Peshin": "12:45", "Asr": "17:30", "Shom": "19:30", "Hufton": "21:00"},
    "ZINBARDOR": {"Bomdod": "04:30", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"},
    "ZAYNUL_OBIDIN": {"Bomdod": "04:40", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"},
    "HAZRATI_ABBOS": {"Bomdod": "04:40", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"},
    "SAODAT": {"Bomdod": "04:55", "Peshin": "12:50", "Asr": "17:20", "Shom": "19:10", "Hufton": "21:00"},
    "TOLABOY": {"Bomdod": "04:40", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"}
}

# UTILITY FUNCTIONS
# =================

def similarity(a, b):
    """String similarity checker"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def detect_script_type(text: str) -> str:
    """Matnning alifbo turini aniqlash"""
    # Arab alifbosini tekshirish
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F')
    
    # Kiril alifbosini tekshirish  
    cyrillic_chars = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
    
    # Lotin alifbosini tekshirish
    latin_chars = sum(1 for char in text if 'a' <= char.lower() <= 'z')
    
    total_chars = arabic_chars + cyrillic_chars + latin_chars
    
    if total_chars == 0:
        return "lotin"  # Default
    
    if arabic_chars / total_chars > 0.3:
        return "arab"
    elif cyrillic_chars / total_chars > 0.3:
        return "kiril"
    else:
        return "lotin"

def find_mosque_3_alifbo(text: str, threshold: float = 0.7) -> Optional[str]:
    """3 alifboda masjid nomini topish"""
    text = text.lower().strip()
    script_type = detect_script_type(text)
    
    logger.info(f"🔍 Masjid qidirilmoqda: '{text[:50]}...' ({script_type} alifbosi)")
    
    best_match = None
    best_score = 0
    
    for mosque_key, mosque_data in MASJIDLAR_3_ALIFBO.items():
        # Barcha alifbolarda qidirish, lekin aniqlangan alifboga ustunlik berish
        for alifbo, patterns in mosque_data["patterns"].items():
            weight = 1.0 if alifbo == script_type else 0.8  # Aniqlangan alifbo uchun ustunlik
            
            for pattern in patterns:
                # Similarity check
                score = similarity(text, pattern) * weight
                if score > threshold and score > best_score:
                    best_score = score
                    best_match = mosque_key
                
                # Direct substring check
                if pattern in text:
                    logger.info(f"✅ To'g'ridan-to'g'ri mos keldi: {mosque_key} ({alifbo})")
                    return mosque_key
    
    if best_match:
        logger.info(f"🎯 Eng yaxshi mos kelishi: {best_match} ({best_score:.2f})")
    else:
        logger.info(f"❌ Masjid topilmadi (threshold: {threshold})")
    
    return best_match

def extract_prayer_times_3_alifbo(text: str) -> Dict[str, str]:
    """3 alifboda namaz vaqtlarini ajratib olish"""
    prayer_times = {}
    text = text.lower()
    script_type = detect_script_type(text)
    
    logger.info(f"🕐 Namaz vaqtlari qidirilmoqda ({script_type} alifbosi)...")
    
    # Barcha alifbolarda qidirish, lekin aniqlangan alifboga ustunlik berish
    for alifbo, patterns in NAMAZ_VAQTLARI_3_ALIFBO.items():
        priority = 1 if alifbo == script_type else 2  # Aniqlangan alifbo birinchi
        
        for prayer_name, pattern in patterns.items():
            if prayer_name not in prayer_times:  # Agar allaqachon topilmagan bo'lsa
                matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
                if matches:
                    # Vaqt formatini standartlashtirish
                    time_str = matches[0].replace('-', ':').replace('–', ':').replace('—', ':').replace('.', ':')
                    
                    # Prayer name'ni to'g'ri formatga keltirish
                    prayer_key = prayer_name.capitalize()
                    if prayer_key not in prayer_times:
                        prayer_times[prayer_key] = time_str
                        logger.info(f"    ✅ {prayer_key}: {time_str} ({alifbo})")
    
    return prayer_times

async def process_image_ocr_3_alifbo(image_url: str) -> str:
    """Rasmdan 3 alifboda matn olish (OCR)"""
    if not OCR_AVAILABLE:
        logger.warning("⚠️ OCR kutubxonalari yo'q")
        return ""
    
    try:
        # Rasmni yuklash
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # PIL Image'ga o'tkazish
        image = Image.open(io.BytesIO(response.content))
        
        # OCR - 3 alifbo uchun
        text = pytesseract.image_to_string(
            image, 
            lang='uzb+rus+ara+eng',  # Uzbek, Russian, Arabic, English
            config='--psm 6 -c tessedit_char_whitelist=0123456789АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzġʻ'
        )
        
        logger.info(f"📖 OCR natija: {text[:100]}...")
        return text
        
    except Exception as e:
        logger.error(f"❌ OCR xatolik: {e}")
        return ""

async def scrape_telegram_channel_3_alifbo():
    """Telegram kanalini web scraping orqali tekshirish - 3 alifbo"""
    global last_posts_hash
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        logger.info(f"🌐 Kanal tekshirilmoqda: {CHANNEL_URL}")
        
        response = requests.get(CHANNEL_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Telegram preview'da post'larni topish
        posts = soup.find_all('div', class_='tgme_widget_message')
        
        if not posts:
            logger.warning("⚠️ Hech qanday post topilmadi")
            return
        
        logger.info(f"📥 {len(posts)} ta post topildi")
        
        # Eng yangi post'larni tekshirish (oxirgi 3 ta)
        for post in posts[-3:]:
            await process_telegram_post_3_alifbo(post)
            
    except Exception as e:
        logger.error(f"❌ Kanal scraping xatolik: {e}")

async def process_telegram_post_3_alifbo(post):
    """Telegram postni 3 alifboda tahlil qilish"""
    try:
        # Post ID olish
        post_link = post.find('a', class_='tgme_widget_message_date')
        post_id = post_link.get('href', '').split('/')[-1] if post_link else 'unknown'
        
        # Post hash yaratish (takrorlanishni oldini olish uchun)
        post_content = str(post)
        post_hash = hashlib.md5(post_content.encode()).hexdigest()
        
        # Agar bu post allaqachon qaralgan bo'lsa, o'tkazib yuborish
        if post_id in last_posts_hash and last_posts_hash[post_id] == post_hash:
            return
        
        last_posts_hash[post_id] = post_hash
        
        logger.info(f"📋 Yangi post tahlil qilinmoqda: {post_id}")
        
        all_text = ""
        
        # Matn kontentni olish
        text_div = post.find('div', class_='tgme_widget_message_text')
        if text_div:
            all_text += text_div.get_text(strip=True, separator=' ')
            logger.info(f"📝 Matn topildi: {all_text[:100]}...")
        
        # Rasm kontentni tekshirish va OCR
        photo_div = post.find('a', class_='tgme_widget_message_photo_wrap')
        if photo_div and OCR_AVAILABLE:
            # Rasm URL'ni olish
            style = photo_div.get('style', '')
            if 'background-image:url(' in style:
                import re
                url_match = re.search(r'background-image:url\(([^)]+)\)', style)
                if url_match:
                    image_url = url_match.group(1)
                    logger.info(f"🖼️ Rasm topildi, OCR ishga tushirilmoqda...")
                    ocr_text = await process_image_ocr_3_alifbo(image_url)
                    all_text += " " + ocr_text
        
        # Agar matn bo'lsa, tahlil qilish
        if all_text.strip():
            await analyze_post_content_3_alifbo(all_text, post_id)
        
    except Exception as e:
        logger.error(f"❌ Post tahlil xatolik: {e}")

async def analyze_post_content_3_alifbo(text: str, post_id: str):
    """Post kontentini 3 alifboda tahlil qilish"""
    logger.info(f"🔍 Post {post_id} tahlil qilinmoqda...")
    
    # Masjid nomini topish
    mosque_key = find_mosque_3_alifbo(text)
    
    if not mosque_key:
        logger.info(f"⚠️ Post {post_id}da masjid nomi topilmadi")
        return
    
    # Namaz vaqtlarini topish
    prayer_times = extract_prayer_times_3_alifbo(text)
    
    if not prayer_times:
        logger.info(f"⚠️ Post {post_id}da namaz vaqtlari topilmadi")
        return
    
    # Ma'lumotlarni yangilash va push notification
    await update_mosque_data_and_notify(mosque_key, prayer_times, post_id)

async def update_mosque_data_and_notify(mosque_key: str, new_prayer_times: Dict[str, str], post_id: str):
    """Masjid ma'lumotlarini yangilash va push notification yuborish"""
    if mosque_key not in masjidlar_data:
        logger.warning(f"⚠️ Noma'lum masjid: {mosque_key}")
        return
    
    mosque_name = MASJIDLAR_3_ALIFBO[mosque_key]["full_name"]
    old_times = masjidlar_data[mosque_key].copy()
    changes = {}
    
    # O'zgarishlarni tekshirish
    for prayer, new_time in new_prayer_times.items():
        if prayer in old_times:
            if old_times[prayer] != new_time:
                changes[prayer] = {
                    'old': old_times[prayer],
                    'new': new_time
                }
                masjidlar_data[mosque_key][prayer] = new_time
    
    # Agar o'zgarishlar bo'lsa, push notification yuborish
    if changes:
        logger.info(f"✅ {mosque_name} vaqtlari yangilandi: {changes}")
        await send_push_notifications(mosque_key, mosque_name, changes, post_id)
    else:
        logger.info(f"ℹ️ {mosque_name} vaqtlari o'zgarmagan")

async def send_push_notifications(mosque_key: str, mosque_name: str, changes: Dict[str, Dict], post_id: str):
    """Barcha foydalanuvchilarga push notification yuborish"""
    if not bot_app:
        logger.warning("⚠️ Bot app mavjud emas")
        return
    
    # Qo'qon vaqt zonasi
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%d.%m.%Y")
    
    # Xabar tayyorlash
    message = f"🔔 *NAMAZ VAQTI YANGILANDI*\n\n"
    message += f"🕌 *{mosque_name.replace('JOME MASJIDI', '').strip()}*\n\n"
    
    # O'zgarishlarni ko'rsatish
    for prayer, change in changes.items():
        old_time = change['old']
        new_time = change['new']
        
        # Emoji tanlash
        prayer_emojis = {
            "Bomdod": "🌅",
            "Peshin": "☀️",
            "Asr": "🌆", 
            "Shom": "🌇",
            "Hufton": "🌙"
        }
        emoji = prayer_emojis.get(prayer, "🕐")
        
        message += f"{emoji} *{prayer}:* {old_time} → *{new_time}*\n"
    
    message += f"\n📅 Yangilangan: {current_date} {current_time}\n"
    message += f"📺 Manba: @{CHANNEL_USERNAME}\n"
    message += f"🆔 Post: {post_id}"
    
    # Tanlangan masjidga obuna bo'lgan foydalanuvchilarni topish
    notified_users = 0
    
    for user_id, settings in user_settings.items():
        selected_mosques = set(settings.get('selected_masjids', []))
        
        # Agar foydalanuvchi bu masjidni tanlagan bo'lsa
        if mosque_key in selected_mosques:
            try:
                await bot_app.bot.send_message(
                    chat_id=int(user_id),
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                notified_users += 1
                
                # Spam oldini olish uchun kichik pause
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"⚠️ User {user_id}ga xabar yuborilmadi: {e}")
    
    logger.info(f"📤 {notified_users} ta foydalanuvchiga notification yuborildi")

# CHANNEL MONITORING SCHEDULER
# ============================

async def start_channel_monitoring_3_alifbo():
    """3 alifbo kanal monitoringni boshlash"""
    logger.info(f"👀 Kanal monitoring boshlandi: @{CHANNEL_USERNAME}")
    logger.info(f"🔤 3 alifbo qo'llab-quvvatlanadi: Lotin, Kiril, Arab")
    logger.info(f"🖼️ OCR {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}")
    
    while True:
        try:
            await scrape_telegram_channel_3_alifbo()
            # Har 2 daqiqada tekshirish
            await asyncio.sleep(120)
            
        except Exception as e:
            logger.error(f"❌ Monitoring xatolik: {e}")
            # Xatolik bo'lsa 5 daqiqa kutish
            await asyncio.sleep(300)

# MASJIDLAR KOORDINATALARI
# ========================

MASJID_COORDINATES = {
    "NORBUTABEK": (40.3925, 71.7412),
    "GISHTLIK": (40.3901, 71.7389),
    "SHAYXULISLOM": (40.3867, 71.7435),
    "HADYA_HOJI": (40.3823, 71.7298),
    "AFGONBOG": (40.3889, 71.7478),
    "SAYYID_AXMADHON": (40.3934, 71.7523),
    "DEGRIZLIK": (40.3756, 71.7334),
    "SHAYXON": (40.3812, 71.7367),
    "ZINBARDOR": (40.3598, 71.7123),
    "ZAYNUL_OBIDIN": (40.3878, 71.7445),
    "HAZRATI_ABBOS": (40.3845, 71.7401),
    "SAODAT": (40.3834, 71.7423),
    "TOLABOY": (40.3889, 71.7467)
}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Ikki nuqta orasidagi masofani hisoblash (km)"""
    R = 6371  # Yer radiusi km da
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# USER SETTINGS FUNCTIONS
# =======================

def get_user_selected_masjids(user_id: str) -> Set[str]:
    """Foydalanuvchi tanlagan masjidlar"""
    return set(user_settings.get(str(user_id), {}).get('selected_masjids', []))

def save_user_masjids(user_id: str, selected_masjids: Set[str]):
    """Foydalanuvchi tanlagan masjidlarni saqlash"""
    user_id_str = str(user_id)
    if user_id_str not in user_settings:
        user_settings[user_id_str] = {}
    user_settings[user_id_str]['selected_masjids'] = list(selected_masjids)

# TELEGRAM BOT UI FUNCTIONS
# =========================

def get_main_keyboard():
    """Asosiy klaviatura"""
    keyboard = [
        ['🕐 Barcha vaqtlar', '⏰ Eng yaqin vaqt'],
        ['🕌 Masjidlar', '📍 3 ta yaqin masjid'],
        ['⚙️ Sozlamalar', 'ℹ️ Yordam']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_masjid_selection_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Masjidlarni tanlash klaviaturasi"""
    selected = get_user_selected_masjids(user_id)
    keyboard = []
    
    # Masjidlar royxati (2 tadan qatorda)
    masjid_items = list(MASJIDLAR_3_ALIFBO.items())
    for i in range(0, len(masjid_items), 2):
        row = []
        for j in range(2):
            if i + j < len(masjid_items):
                key, data = masjid_items[i + j]
                # Tanlangan bolsa tick, tanlanmagan bolsa box
                icon = "✅" if key in selected else "⬜"
                # Masjid nomini qisqartirish
                short_name = data["full_name"].replace("JOME MASJIDI", "").replace("MASJIDI", "").strip()
                if len(short_name) > 15:
                    short_name = short_name[:15] + "..."
                row.append(InlineKeyboardButton(
                    f"{icon} {short_name}", 
                    callback_data=f"toggle_{key}"
                ))
        keyboard.append(row)
    
    # Boshqaruv tugmalari
    control_buttons = [
        [
            InlineKeyboardButton("✅ Barchasini tanlash", callback_data="select_all"),
            InlineKeyboardButton("❌ Barchasini bekor qilish", callback_data="deselect_all")
        ],
        [
            InlineKeyboardButton("💾 Saqlash", callback_data="save_settings"),
            InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")
        ]
    ]
    keyboard.extend(control_buttons)
    
    return InlineKeyboardMarkup(keyboard)

# TELEGRAM BOT HANDLERS
# =====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrugi"""
    user_id = update.effective_user.id
    
    # Agar yangi foydalanuvchi bolsa, barcha masjidlarni tanlangan qilib qoyish
    if str(user_id) not in user_settings:
        save_user_masjids(user_id, set(MASJIDLAR_3_ALIFBO.keys()))
    
    welcome_message = f"""🕌 Assalomu alaykum!

*Qo'qon Masjidlari Namaz Vaqti Botiga xush kelibsiz!*

🔄 *REAL-TIME YANGILANISHLAR:*
Bot @{CHANNEL_USERNAME} kanalini kuzatib turadi va namaz vaqtlarini avtomatik yangilaydi!

🔤 *3 ALIFBO QOLLAB-QUVVATLASH:*
• 🔤 Lotin (norbutabek, gishtlik)
• 🔠 Kiril (норбутабек, гиштлик) 
• 🔡 Arab (نوربوتابيك, غیشتلیك)

🖼️ *OCR RASM TAHLILI:*
{'✅ Faol - rasmlardan matn o\'qiladi' if OCR_AVAILABLE else '⚠️ Faol emas - faqat matn tahlili'}

⚙️ *Sozlamalar* orqali kerakli masjidlarni belgilashingiz mumkin.

📍 Barcha vaqtlar Qo'qon mahalliy vaqti bo'yicha."""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabarlarni qayta ishlash"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == '⚙️ Sozlamalar':
        await handle_settings(update, context)
    elif text == '🕌 Masjidlar':
        await handle_all_masjids(update, context)
    elif text == '🕐 Barcha vaqtlar':
        await handle_selected_masjids_times(update, context)
    elif text == 'ℹ️ Yordam':
        await handle_help(update, context)
    elif text == '⏰ Eng yaqin vaqt':
        await handle_next_prayer(update, context)
    elif text == '📍 3 ta yaqin masjid':
        await handle_three_nearest_mosques_simple(update, context)
    elif text == '🔙 Orqaga':
        await update.message.reply_text(
            "🔙 Asosiy menyuga qaytdingiz",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "Quyidagi knopkalardan foydalaning:",
            reply_markup=get_main_keyboard()
        )

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sozlamalar"""
    user_id = update.effective_user.id
    selected = get_user_selected_masjids(str(user_id))
    
    message = f"""⚙️ *PUSH NOTIFICATION SOZLAMALARI*

Siz hozirda *{len(selected)} ta masjid* uchun bildirishnoma olasiz.

🔄 *Real-time yangilanishlar:*
@{CHANNEL_USERNAME} kanalidan avtomatik yangilanadi!

🔤 *3 alifbo qo'llab-quvvatlanadi:*
• Lotin, Kiril, Arab

🖼️ *OCR:* {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}

Quyida masjidlarni tanlang/bekor qiling:
✅ - Tanlangan (push olasiz)
⬜ - Tanlanmagan"""
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_masjid_selection_keyboard(str(user_id))
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button bosilganda"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    if data.startswith("toggle_"):
        # Masjidni tanlash/bekor qilish
        masjid_key = data.replace("toggle_", "")
        selected = get_user_selected_masjids(user_id)
        
        if masjid_key in selected:
            selected.remove(masjid_key)
        else:
            selected.add(masjid_key)
        
        save_user_masjids(user_id, selected)
        
        # Klaviaturani yangilash
        await query.edit_message_reply_markup(
            reply_markup=get_masjid_selection_keyboard(user_id)
        )
        
    elif data == "select_all":
        # Barchasini tanlash
        save_user_masjids(user_id, set(MASJIDLAR_3_ALIFBO.keys()))
        await query.edit_message_reply_markup(
            reply_markup=get_masjid_selection_keyboard(user_id)
        )
        
    elif data == "deselect_all":
        # Barchasini bekor qilish
        save_user_masjids(user_id, set())
        await query.edit_message_reply_markup(
            reply_markup=get_masjid_selection_keyboard(user_id)
        )
        
    elif data == "save_settings":
        # Sozlamalarni saqlash
        selected = get_user_selected_masjids(user_id)
        mosque_names = [MASJIDLAR_3_ALIFBO[key]["full_name"].replace('JOME MASJIDI', '').strip() for key in selected]
        await query.edit_message_text(
            f"✅ *Sozlamalar saqlandi!*\n\n"
            f"Siz {len(selected)} ta masjid uchun push notification olasiz:\n"
            f"{', '.join(mosque_names)}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "back_main":
        # Orqaga
        await query.edit_message_text("🔙 Asosiy menyuga qaytdingiz.")

async def handle_selected_masjids_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tanlangan masjidlar vaqtlari"""
    user_id = str(update.effective_user.id)
    selected = get_user_selected_masjids(user_id)
    
    if not selected:
        await update.message.reply_text(
            "❌ Hech qanday masjid tanlanmagan!\n⚙️ Sozlamalar orqali masjidlarni tanlang.",
            reply_markup=get_main_keyboard()
        )
        return
    
    message = "🕐 *TANLANGAN MASJIDLAR VAQTLARI:*\n\n"
    
    for masjid_key in selected:
        if masjid_key in masjidlar_data:
            times = masjidlar_data[masjid_key]
            name = MASJIDLAR_3_ALIFBO[masjid_key]["full_name"]
            
            message += f"🕌 *{name.replace('JOME MASJIDI', '').strip()}*\n"
            message += f"🌅 Bomdod: *{times['Bomdod']}*\n"
            message += f"☀️ Peshin: *{times['Peshin']}*\n"
            message += f"🌆 Asr: *{times['Asr']}*\n"
            message += f"🌇 Shom: *{times['Shom']}*\n"
            message += f"🌙 Hufton: *{times['Hufton']}*\n\n"
    
    # Real-time info
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    message += f"⏰ Hozirgi vaqt: {current_time} (Qo'qon vaqti)\n"
    message += f"🔄 Ma'lumotlar @{CHANNEL_USERNAME} dan real-time yangilanadi\n"
    message += f"🔤 3 alifbo qo'llab-quvvatlanadi"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_next_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Eng yaqin namoz vaqti"""
    user_id = str(update.effective_user.id)
    selected = get_user_selected_masjids(user_id)
    
    if not selected:
        await update.message.reply_text(
            "❌ Hech qanday masjid tanlanmagan!\n⚙️ Sozlamalar orqali masjidlarni tanlang.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Qo'qon vaqt zonasi
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    # Namaz nomlari
    prayer_names = ["Bomdod", "Peshin", "Asr", "Shom", "Hufton"]
    
    # Hozirgi vaqtga qarab eng yaqin namozni topish
    next_prayers = []
    
    for masjid_key in selected:
        if masjid_key in masjidlar_data:
            times = masjidlar_data[masjid_key]
            name = MASJIDLAR_3_ALIFBO[masjid_key]["full_name"]
            
            for prayer in prayer_names:
                prayer_time = times[prayer]
                if prayer_time > current_time:
                    next_prayers.append({
                        'masjid': name,
                        'prayer': prayer,
                        'time': prayer_time
                    })
                    break
    
    if next_prayers:
        next_prayers.sort(key=lambda x: x['time'])
        next_prayer = next_prayers[0]
        
        message = f"""🕐 *ENG YAQIN NAMOZ VAQTI*

🕌 {next_prayer['masjid'].replace('JOME MASJIDI', '').strip()}
⏰ {next_prayer['prayer']}: *{next_prayer['time']}*

📅 Hozirgi vaqt: {current_time} (Qo'qon vaqti)

🔔 *Push notification:* Vaqt yangilanishi bilan avtomatik xabar olasiz!
🔤 *3 alifbo:* Lotin, Kiril, Arab
📺 *Manba:* @{CHANNEL_USERNAME}"""
    else:
        message = f"""📍 Bugun uchun barcha namaz vaqtlari o'tdi.
Ertaga Bomdod vaqti bilan davom etadi.

⏰ Hozirgi vaqt: {current_time} (Qo'qon vaqti)"""
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_three_nearest_mosques_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """3 ta yaqin masjid - soddalashtirilgan versiya"""
    # Qo'qon markaziga eng yaqin 3 ta masjidni ko'rsatish
    qoqon_center = (40.3867, 71.7435)  # Taxminan shahar markazi
    
    distances = []
    for mosque_key, coordinates in MASJID_COORDINATES.items():
        distance = calculate_distance(
            qoqon_center[0], qoqon_center[1],
            coordinates[0], coordinates[1]
        )
        distances.append((mosque_key, distance, coordinates))
    
    # Eng yaqin 3 tasini tanlash
    distances.sort(key=lambda x: x[1])
    nearest_three = distances[:3]
    
    message = "📍 *QO'QON MARKAZIGA ENG YAQIN 3 TA MASJID:*\n\n"
    
    for i, (mosque_key, distance, coordinates) in enumerate(nearest_three, 1):
        mosque_name = MASJIDLAR_3_ALIFBO[mosque_key]["full_name"]
        times = masjidlar_data[mosque_key]
        
        # Hozirgi vaqt
        qoqon_tz = pytz.timezone('Asia/Tashkent')
        now = datetime.now(qoqon_tz)
        current_time = now.strftime("%H:%M")
        
        # Keyingi namaz vaqti
        prayer_names = ["Bomdod", "Peshin", "Asr", "Shom", "Hufton"]
        next_prayer = None
        
        for prayer in prayer_names:
            prayer_time = times[prayer]
            if prayer_time > current_time:
                next_prayer = {'name': prayer, 'time': prayer_time}
                break
        
        message += f"**{i}. {mosque_name.replace('JOME MASJIDI', '').strip()}**\n"
        if distance < 1:
            message += f"📏 Masofa: {int(distance * 1000)} metr\n"
        else:
            message += f"📏 Masofa: {distance:.1f} km\n"
            
        if next_prayer:
            message += f"⏰ Keyingi: {next_prayer['name']} - *{next_prayer['time']}*\n"
        
        # Barcha vaqtlar
        message += f"🕐 Vaqtlar: {times['Bomdod']} | {times['Peshin']} | {times['Asr']} | {times['Shom']} | {times['Hufton']}\n"
        
        # Map links
        lat, lon = coordinates
        message += f"🗺️ [Google Maps](https://maps.google.com/?q={lat},{lon}) | [Yandex](https://yandex.com/maps/?pt={lon},{lat}&z=18)\n\n"
    
    message += f"⏰ Hozirgi vaqt: {current_time} (Qo'qon vaqti)\n"
    message += f"🔄 Real-time yangilanishlar faol!"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=True
    )

async def handle_all_masjids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha masjidlar (korish uchun)"""
    message = "🕌 *BARCHA MASJIDLAR ROYXATI:*\n\n"
    
    for i, (key, data) in enumerate(MASJIDLAR_3_ALIFBO.items(), 1):
        message += f"{i}. {data['full_name']}\n"
    
    message += f"\n📊 Jami: {len(MASJIDLAR_3_ALIFBO)} ta masjid"
    message += "\n\n⚙️ *Sozlamalar* orqali kerakli masjidlarni tanlashingiz mumkin."
    message += f"\n🔄 Barcha vaqtlar @{CHANNEL_USERNAME} dan real-time yangilanadi!"
    message += f"\n🔤 3 alifbo qo'llab-quvvatlanadi: Lotin, Kiril, Arab"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam bolimi"""
    help_text = f"""ℹ️ *YORDAM*

🔄 *REAL-TIME KANAL MONITORING:*
Bot @{CHANNEL_USERNAME} kanalini doimiy kuzatib turadi va namaz vaqtlarini avtomatik yangilaydi!

🔤 *3 ALIFBO QOLLAB-QUVVATLASH:*
• **Lotin:** norbutabek, gishtlik, bomdod, peshin
• **Kiril:** норбутабек, гиштлик, бомдод, пешин  
• **Arab:** نوربوتابيك, غیشتلیك, فجر, ظهر

🖼️ *OCR RASM TAHLILI:*
{'✅ Faol - rasmlardan matn avtomatik o\'qiladi' if OCR_AVAILABLE else '⚠️ Faol emas - faqat matn tahlili'}

*Bot funksiyalari:*
🕐 Barcha vaqtlar - Tanlangan masjidlar namaz vaqtlari
⏰ Eng yaqin vaqt - Keyingi namaz vaqti
📍 3 ta yaqin masjid - Eng yaqin 3 ta masjid (xarita bilan)
🕌 Masjidlar - Barcha masjidlar ro'yxati
⚙️ Sozlamalar - Push notification uchun masjidlarni tanlash

🔔 *PUSH NOTIFICATION TIZIMI:*
• Namaz vaqti yangilanishi bilan avtomatik xabar
• Faqat tanlangan masjidlar uchun
• Real-time o'zgarishlar haqida xabar

🤖 *MONITORING JARAYONI:*
1. Kanalda yangi post paydo bo'ladi
2. 3 alifboda masjid nomi qidiriladi  
3. Namaz vaqtlari ajratib olinadi
4. Botdagi ma'lumotlar bilan solishtiriladi
5. O'zgarish bo'lsa push notification yuboriladi

*Vaqt zonasi:* Qo'qon mahalliy vaqti (UTC+5)
*Kanal:* @{CHANNEL_USERNAME}
*Monitoring interval:* Har 2 daqiqada"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xatolik handleri"""
    logger.error(msg="Xatolik yuz berdi:", exc_info=context.error)

def main():
    """Asosiy funksiya"""
    global bot_app
    
    try:
        # Flask'ni background'da ishga tushirish
        threading.Thread(target=run_flask, daemon=True).start()
        
        # Application yaratish
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Handlerlarni qoshish
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot_app.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Xatolik handlerini qoshish
        bot_app.add_error_handler(error_handler)
        
        logger.info("✅ Bot ishga tushmoqda...")
        logger.info(f"🎯 Monitoring kanal: @{CHANNEL_USERNAME}")
        logger.info(f"🔤 3 alifbo qo'llab-quvvatlanadi: Lotin, Kiril, Arab")
        logger.info(f"🖼️ OCR: {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}")
        print("🚀 Bot ishga tushdi! ✅")
        print(f"📺 Kanal kuzatilmoqda: @{CHANNEL_USERNAME}")
        print(f"🔄 Real-time monitoring har 2 daqiqada")
        print(f"🔤 3 alifbo pattern matching faol")
        print(f"🖼️ OCR rasm tahlili: {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}")
        
        # Background'da kanal monitoring'ni boshlash
        async def start_monitoring():
            await start_channel_monitoring_3_alifbo()
        
        # Monitoring task'ni background'da ishga tushirish
        asyncio.create_task(start_monitoring())
        
        # Bot polling'ni ishga tushirish
        bot_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        print(f"❌ Xatolik: {e}")

if __name__ == '__main__':
    main()
