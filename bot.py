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
from bs4 import BeautifulSoup
import time
from difflib import SequenceMatcher
import hashlib
from collections import defaultdict, Counter

# OCR uchun (agar mavjud bo'lsa)
try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR kutubxonalari o'rnatilmagan. Faqat matn tahlili faol.")

# Flask Health Check
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'Bot ishlaydi', 'timestamp': datetime.now().isoformat()}, 200

@app.route('/')
def home():
    return {'service': 'Qoqon Masjidlar Bot', 'admin': 'menadminman', 'features': ['3-alifbo', 'OCR', 'Real-time']}, 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========================================
# CONFIGURATION VA ENVIRONMENT VARIABLES
# ========================================

BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Opsional
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'quqonnamozvaqti')

# Test mode
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
if TEST_MODE:
    test_channel = os.getenv('TEST_CHANNEL_USERNAME', 'namozvaqtitest')
    CHANNEL_USERNAME = test_channel
    logger.info(f"🧪 TEST MODE: @{CHANNEL_USERNAME}")

CHANNEL_URL = f'https://t.me/s/{CHANNEL_USERNAME}'

# Environment validation
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable majburiy!")
    exit(1)

logger.info(f"🎯 Monitoring kanal: @{CHANNEL_USERNAME}")
logger.info(f"🌐 Kanal URL: {CHANNEL_URL}")
logger.info(f"🖼️ OCR: {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}")

# ========================================
# ADMIN PANEL TIZIMI
# ========================================

ADMIN_PASSWORD = "menadminman"
admin_sessions = set()
admin_temp_data = {}

# Analytics va statistika
user_activity = defaultdict(int)
user_join_dates = {}
user_last_activity = {}
masjid_popularity = defaultdict(int)
daily_stats = defaultdict(lambda: defaultdict(int))
push_notification_stats = defaultdict(int)

def log_user_activity(user_id: str, action: str):
    """Foydalanuvchi faolligini log qilish"""
    user_activity[user_id] += 1
    user_last_activity[user_id] = datetime.now()
    
    today = datetime.now().strftime('%Y-%m-%d')
    daily_stats[today]['total_actions'] += 1
    daily_stats[today][action] += 1

def log_user_join(user_id: str):
    """Yangi foydalanuvchi qo'shilishini log qilish"""
    if user_id not in user_join_dates:
        user_join_dates[user_id] = datetime.now()
        today = datetime.now().strftime('%Y-%m-%d')
        daily_stats[today]['new_users'] += 1
        logger.info(f"👤 Yangi foydalanuvchi: {user_id}")

def log_masjid_selection(user_id: str, selected_masjids: List[str]):
    """Masjid tanlanishini log qilish"""
    for masjid_key in selected_masjids:
        masjid_popularity[masjid_key] += 1

def is_admin(user_id: str) -> bool:
    """Admin ekanligini tekshirish"""
    return str(user_id) in admin_sessions

# ========================================
# MASJIDLAR VA PATTERN MATCHING TIZIMI
# ========================================

MASJIDLAR_3_ALIFBO = {
    "NORBUTABEK": {
        "full_name": "NORBUTABEK JOME MASJIDI",
        "coordinates": [40.3925, 71.7412],
        "patterns": {
            "lotin": ["norbutabek", "norbu tabek", "norbu-tabek", "norbutabek jome", "norbutabek masjid"],
            "kiril": ["норбутабек", "норбу табек", "норбу-табек", "норбутабек жоме", "норбутабек масжид"],
            "arab": ["نوربوتابيك", "نوربو تابيك", "مسجد نوربوتابيك"]
        },
        "created_date": "2025-01-01",
        "last_updated": datetime.now().strftime('%Y-%m-%d')
    },
    "GISHTLIK": {
        "full_name": "GISHTLIK JOME MASJIDI",
        "coordinates": [40.3901, 71.7389],
        "patterns": {
            "lotin": ["gishtlik", "g'ishtlik", "gʻishtlik", "gishtlik jome", "gishtlik masjid"],
            "kiril": ["гиштлик", "ғиштлик", "гиштлик жоме", "гиштлик масжид"],
            "arab": ["غیشتلیك", "گشتلیك", "مسجد غیشتلیك"]
        },
        "created_date": "2025-01-01",
        "last_updated": datetime.now().strftime('%Y-%m-%d')
    },
    "SHAYXULISLOM": {
        "full_name": "SHAYXULISLOM JOME MASJIDI",
        "coordinates": [40.3867, 71.7435],
        "patterns": {
            "lotin": ["shayxulislom", "shayx ul islom", "shaykh ul islam", "shayxulislom jome"],
            "kiril": ["шайхулислом", "шайх ул ислом", "шайхулислом жоме"],
            "arab": ["شیخ الاسلام", "شایخ الاسلام", "مسجد شیخ الاسلام"]
        },
        "created_date": "2025-01-01",
        "last_updated": datetime.now().strftime('%Y-%m-%d')
    }
}

# Flexible namaz vaqtlari patterns - real telegram formatlar uchun
NAMAZ_VAQTLARI_PATTERNS = {
    "lotin": {
        "bomdod": r'(?:bomdod|fajr|subh|sahar|tong)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "peshin": r'(?:peshin|zuhr|zuhur|öyle|tush)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "asr": r'(?:asr|ikindi|digar)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "shom": r'(?:shom|maghrib|mag\'rib|axshom|kech)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "hufton": r'(?:hufton|isha|xufton|kech|tun)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})'
    },
    "kiril": {
        "bomdod": r'(?:бомдод|фажр|субх|сахар|тонг)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "peshin": r'(?:пешин|зухр|зухур|ойле|туш)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "asr": r'(?:аср|икинди|дигар)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "shom": r'(?:шом|магриб|мағриб|ахшом|кеч)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "hufton": r'(?:хуфтон|иша|кеч|тун)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})'
    },
    "arab": {
        "bomdod": r'(?:فجر|صبح|سحر)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "peshin": r'(?:ظهر|زهر)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "asr": r'(?:عصر)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "shom": r'(?:مغرب|مغریب)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})',
        "hufton": r'(?:عشاء|عشا|عیشا)\s*[:\-–—.]\s*(\d{1,2})[:\-–—.](\d{2})'
    }
}

# Default namaz vaqtlari (backup)
masjidlar_data = {
    "NORBUTABEK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:45", "Shom": "19:35", "Hufton": "21:15"},
    "GISHTLIK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:15", "Shom": "19:30", "Hufton": "21:00"},
    "SHAYXULISLOM": {"Bomdod": "04:45", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"}
}

# Global variables
bot_app = None
user_settings = {}
last_posts_hash = {}

# ========================================
# UTILITY FUNCTIONS
# ========================================

def similarity(a: str, b: str) -> float:
    """String similarity"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def detect_script_type(text: str) -> str:
    """Matnning alifbo turini aniqlash"""
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F')
    cyrillic_chars = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
    latin_chars = sum(1 for char in text if char.isalpha() and char.isascii())
    
    total_chars = arabic_chars + cyrillic_chars + latin_chars
    if total_chars == 0:
        return "lotin"
    
    if arabic_chars / total_chars > 0.3:
        return "arab"
    elif cyrillic_chars / total_chars > 0.3:
        return "kiril"
    else:
        return "lotin"

def clean_text_for_matching(text: str) -> str:
    """Matnni pattern matching uchun tozalash"""
    # Emojiler va maxsus belgilarni olib tashlash
    text = re.sub(r'[🌅☀️🌆🌇🌙📍📅🕐🕌]', '', text)
    # Qo'shimcha bo'shliqlarni tozalash
    text = ' '.join(text.split())
    return text.strip()

def find_mosque_advanced(text: str, threshold: float = 0.6) -> Optional[str]:
    """Kengaytirilgan masjid qidirish algoritmi"""
    text = clean_text_for_matching(text)
    text_lower = text.lower()
    script_type = detect_script_type(text)
    
    logger.info(f"🔍 Masjid qidirilmoqda: '{text}' ({script_type} alifbosi)")
    
    best_match = None
    best_score = 0
    
    for mosque_key, mosque_data in MASJIDLAR_3_ALIFBO.items():
        # Har xil alifboda qidirish
        for alifbo, patterns in mosque_data["patterns"].items():
            weight = 1.0 if alifbo == script_type else 0.8
            
            for pattern in patterns:
                # To'g'ridan-to'g'ri mavjudlik
                if pattern.lower() in text_lower:
                    logger.info(f"✅ TO'G'RIDAN-TO'G'RI: {mosque_key} pattern '{pattern}' topildi")
                    return mosque_key
                
                # Similarity check
                score = similarity(text, pattern) * weight
                if score > threshold and score > best_score:
                    best_score = score
                    best_match = mosque_key
                    logger.info(f"🎯 Similarity match: {mosque_key} pattern '{pattern}' score: {score:.2f}")
        
        # Masjid nomining qismlarini alohida tekshirish
        name_parts = mosque_data["full_name"].lower().replace("jome masjidi", "").split()
        for part in name_parts:
            if len(part) > 3 and part in text_lower:
                logger.info(f"✅ NOM QISMI ORQALI: {mosque_key} part '{part}' topildi")
                return mosque_key
    
    if best_match:
        logger.info(f"🎯 ENG YAXSHI: {best_match} (score: {best_score:.2f})")
        return best_match
    
    logger.warning(f"❌ Hech qanday masjid topilmadi: '{text}'")
    return None

def extract_prayer_times_advanced(text: str) -> Dict[str, str]:
    """Kengaytirilgan namaz vaqtlari ajratish"""
    prayer_times = {}
    text_clean = clean_text_for_matching(text)
    script_type = detect_script_type(text)
    
    logger.info(f"🕐 Namaz vaqtlari qidirilmoqda ({script_type}): '{text_clean[:100]}...'")
    
    # Barcha alifbolarda qidirish
    for alifbo, patterns in NAMAZ_VAQTLARI_PATTERNS.items():
        for prayer_name, pattern in patterns.items():
            if prayer_name.capitalize() not in prayer_times:
                matches = re.findall(pattern, text_clean, re.IGNORECASE | re.UNICODE)
                if matches:
                    if len(matches[0]) == 2:  # (hour, minute) tuple
                        hour, minute = matches[0]
                        time_str = f"{hour.zfill(2)}:{minute.zfill(2)}"
                    else:
                        time_str = matches[0]
                    
                    prayer_key = prayer_name.capitalize()
                    prayer_times[prayer_key] = time_str
                    logger.info(f"    ✅ {prayer_key}: {time_str} ({alifbo})")
    
    # Fallback: oddiy raqamlar qidirish
    if not prayer_times:
        simple_times = re.findall(r'(\d{1,2})[:\-.](\d{2})', text_clean)
        if len(simple_times) >= 5:
            prayer_names = ["Bomdod", "Peshin", "Asr", "Shom", "Hufton"]
            for i, (hour, minute) in enumerate(simple_times[:5]):
                prayer_times[prayer_names[i]] = f"{hour.zfill(2)}:{minute.zfill(2)}"
                logger.info(f"    🔄 FALLBACK {prayer_names[i]}: {hour}:{minute}")
    
    return prayer_times

# ========================================
# OCR VA RASM TAHLILI
# ========================================

async def process_image_ocr(image_url: str) -> str:
    """Rasmdan OCR orqali matn olish"""
    if not OCR_AVAILABLE:
        logger.warning("⚠️ OCR kutubxonalari yo'q")
        return ""
    
    try:
        logger.info(f"🖼️ OCR boshlandi: {image_url}")
        
        # Rasmni yuklash
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # PIL Image
        image = Image.open(io.BytesIO(response.content))
        
        # OCR with multiple languages
        ocr_text = pytesseract.image_to_string(
            image, 
            lang='uzb+rus+ara+eng',
            config='--psm 6 --oem 3'
        )
        
        logger.info(f"📖 OCR natija ({len(ocr_text)} belgi): {ocr_text[:200]}...")
        return ocr_text
        
    except Exception as e:
        logger.error(f"❌ OCR xatolik: {e}")
        return ""

# ========================================
# TELEGRAM CHANNEL MONITORING
# ========================================

async def scrape_telegram_channel():
    """Telegram kanalini scraping qilish"""
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
        
        response = requests.get(CHANNEL_URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        logger.info(f"📥 Response: {response.status_code}, Length: {len(response.content)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Telegram post'larini topish - turli selector'lar
        posts = soup.find_all('div', class_='tgme_widget_message')
        if not posts:
            # Alternative selectors
            posts = soup.find_all('div', attrs={'data-post': True})
        
        if not posts:
            logger.warning("⚠️ Hech qanday post topilmadi")
            logger.info(f"HTML snippet: {str(soup)[:500]}...")
            return
        
        logger.info(f"📥 {len(posts)} ta post topildi")
        
        # Eng yangi 3 ta postni tekshirish
        for post in posts[-3:]:
            await process_telegram_post(post)
            
    except Exception as e:
        logger.error(f"❌ Kanal scraping xatolik: {e}")

async def process_telegram_post(post):
    """Telegram postni to'liq tahlil qilish"""
    try:
        # Post ID
        post_link = post.find('a', class_='tgme_widget_message_date')
        if not post_link:
            post_link = post.find('a', attrs={'href': True})
        post_id = post_link.get('href', '').split('/')[-1] if post_link else 'unknown'
        
        # Hash check (dublikatlarni oldini olish)
        post_content = str(post)
        post_hash = hashlib.md5(post_content.encode()).hexdigest()
        
        if post_id in last_posts_hash and last_posts_hash[post_id] == post_hash:
            return
        
        last_posts_hash[post_id] = post_hash
        logger.info(f"📋 Yangi post tahlil qilinmoqda: {post_id}")
        
        all_text = ""
        
        # 1. TEXT CONTENT
        text_selectors = [
            'div.tgme_widget_message_text',
            'div.js-message_text',
            'div[class*="message_text"]'
        ]
        
        for selector in text_selectors:
            text_div = post.select_one(selector)
            if text_div:
                text_content = text_div.get_text(strip=True, separator=' ')
                all_text += text_content + " "
                logger.info(f"📝 Matn topildi ({selector}): {text_content[:100]}...")
                break
        
        # 2. PHOTO OCR
        photo_selectors = [
            'a.tgme_widget_message_photo_wrap',
            'div.tgme_widget_message_photo',
            'img[src*="telegram"]'
        ]
        
        for selector in photo_selectors:
            photo_element = post.select_one(selector)
            if photo_element:
                image_url = None
                
                # Style'dan URL olish
                style = photo_element.get('style', '')
                if 'background-image:url(' in style:
                    url_match = re.search(r'background-image:url\(([^)]+)\)', style)
                    if url_match:
                        image_url = url_match.group(1).strip('"\'')
                
                # img src'dan URL olish
                elif photo_element.name == 'img':
                    image_url = photo_element.get('src')
                
                if image_url and OCR_AVAILABLE:
                    logger.info(f"🖼️ Rasm topildi: {image_url}")
                    ocr_text = await process_image_ocr(image_url)
                    if ocr_text:
                        all_text += " " + ocr_text
                break
        
        # 3. CONTENT ANALYSIS
        if all_text.strip():
            await analyze_post_content(all_text.strip(), post_id)
        else:
            logger.warning(f"⚠️ Post {post_id} da matn topilmadi")
            # Debug uchun HTML structure
            logger.info(f"Post HTML: {str(post)[:300]}...")
        
    except Exception as e:
        logger.error(f"❌ Post {post_id} tahlil xatolik: {e}")

async def analyze_post_content(text: str, post_id: str):
    """Post mazmunini tahlil qilish"""
    logger.info(f"🔍 Post {post_id} mazmuni tahlil qilinmoqda...")
    logger.info(f"📄 Matn: {text[:200]}...")
    
    # Masjid nomini topish
    mosque_key = find_mosque_advanced(text)
    
    if not mosque_key:
        logger.info(f"⚠️ Post {post_id} da masjid nomi topilmadi")
        return
    
    # Namaz vaqtlarini topish
    prayer_times = extract_prayer_times_advanced(text)
    
    if not prayer_times:
        logger.info(f"⚠️ Post {post_id} da namaz vaqtlari topilmadi")
        return
    
    # Ma'lumotlarni yangilash va notification yuborish
    await update_mosque_data_and_notify(mosque_key, prayer_times, post_id)

async def update_mosque_data_and_notify(mosque_key: str, new_prayer_times: Dict[str, str], post_id: str):
    """Masjid ma'lumotlarini yangilash va push notification"""
    if mosque_key not in masjidlar_data:
        logger.warning(f"⚠️ Noma'lum masjid kaliti: {mosque_key}")
        return
    
    mosque_name = MASJIDLAR_3_ALIFBO[mosque_key]["full_name"]
    old_times = masjidlar_data[mosque_key].copy()
    changes = {}
    
    # O'zgarishlarni aniqlash
    for prayer, new_time in new_prayer_times.items():
        if prayer in old_times:
            if old_times[prayer] != new_time:
                changes[prayer] = {
                    'old': old_times[prayer],
                    'new': new_time
                }
                masjidlar_data[mosque_key][prayer] = new_time
    
    # Yangilanish bo'lsa
    if changes:
        logger.info(f"✅ {mosque_name} vaqtlari yangilandi: {changes}")
        # Update timestamp
        MASJIDLAR_3_ALIFBO[mosque_key]["last_updated"] = datetime.now().strftime('%Y-%m-%d')
        # Push notification yuborish
        await send_push_notifications(mosque_key, mosque_name, changes, post_id)
    else:
        logger.info(f"ℹ️ {mosque_name} vaqtlari o'zgarmagan")

async def send_push_notifications(mosque_key: str, mosque_name: str, changes: Dict[str, Dict], post_id: str):
    """Push notification yuborish"""
    if not bot_app:
        logger.warning("⚠️ Bot app mavjud emas")
        return
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    
    # Xabar tayyorlash
    message = f"🔔 *NAMAZ VAQTI YANGILANDI*\n\n"
    message += f"🕌 *{mosque_name.replace('JOME MASJIDI', '').strip()}*\n\n"
    
    # Emoji'lar
    prayer_emojis = {
        "Bomdod": "🌅",
        "Peshin": "☀️", 
        "Asr": "🌆",
        "Shom": "🌇",
        "Hufton": "🌙"
    }
    
    # O'zgarishlarni ko'rsatish
    for prayer, change in changes.items():
        emoji = prayer_emojis.get(prayer, "🕐")
        message += f"{emoji} *{prayer}:* {change['old']} → *{change['new']}*\n"
    
    message += f"\n📅 Yangilangan: {now.strftime('%d.%m.%Y %H:%M')}"
    message += f"\n📺 Manba: @{CHANNEL_USERNAME}"
    message += f"\n🆔 Post: {post_id}"
    
    # Foydalanuvchilarga yuborish
    sent_count = 0
    error_count = 0
    
    logger.info(f"📤 Push notification boshlandi. Jami userlar: {len(user_settings)}")
    
    for user_id, settings in user_settings.items():
        selected_mosques = set(settings.get('selected_masjids', []))
        logger.info(f"👤 User {user_id} selected: {selected_mosques}")
        
        if mosque_key in selected_mosques:
            try:
                await bot_app.bot.send_message(
                    chat_id=int(user_id),
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                sent_count += 1
                logger.info(f"✅ User {user_id} ga yuborildi")
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                error_count += 1
                logger.warning(f"⚠️ User {user_id} ga yuborilmadi: {e}")
    
    # Statistika
    push_notification_stats['auto_update'] += sent_count
    push_notification_stats['error'] += error_count
    
    logger.info(f"📤 Push notification yakunlandi: {sent_count} muvaffaq, {error_count} xatolik")

async def start_channel_monitoring():
    """Kanal monitoring loop"""
    logger.info(f"👀 Kanal monitoring boshlandi: @{CHANNEL_USERNAME}")
    logger.info(f"🔤 3 alifbo qo'llab-quvvatlanadi: Lotin, Kiril, Arab")
    logger.info(f"🖼️ OCR: {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}")
    
    while True:
        try:
            await scrape_telegram_channel()
            # Har 2 daqiqada tekshirish
            await asyncio.sleep(120)
            
        except Exception as e:
            logger.error(f"❌ Monitoring loop xatolik: {e}")
            # Xatolik bo'lsa 5 daqiqa kutish
            await asyncio.sleep(300)

# ========================================
# USER MANAGEMENT FUNCTIONS
# ========================================

def get_user_selected_masjids(user_id: str) -> Set[str]:
    """Foydalanuvchi tanlagan masjidlar"""
    return set(user_settings.get(str(user_id), {}).get('selected_masjids', []))

def save_user_masjids(user_id: str, selected_masjids: Set[str]):
    """Foydalanuvchi tanlagan masjidlarni saqlash"""
    user_id_str = str(user_id)
    if user_id_str not in user_settings:
        user_settings[user_id_str] = {}
    user_settings[user_id_str]['selected_masjids'] = list(selected_masjids)
    
    # Analytics
    log_masjid_selection(user_id, list(selected_masjids))
    
    logger.info(f"💾 User {user_id} masjidlari saqlandi: {len(selected_masjids)} ta")

def get_main_keyboard():
    """Asosiy foydalanuvchi klaviaturasi"""
    keyboard = [
        ['🕐 Barcha vaqtlar', '⏰ Eng yaqin vaqt'],
        ['🕌 Masjidlar', '⚙️ Sozlamalar'],
        ['ℹ️ Yordam']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_masjid_selection_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Masjid tanlash klaviaturasi"""
    selected = get_user_selected_masjids(user_id)
    keyboard = []
    
    # Masjidlar ro'yxati (2 tadan qatorda)
    masjid_items = list(MASJIDLAR_3_ALIFBO.items())
    for i in range(0, len(masjid_items), 2):
        row = []
        for j in range(2):
            if i + j < len(masjid_items):
                key, data = masjid_items[i + j]
                # Icon
                icon = "✅" if key in selected else "⬜"
                # Qisqa nom
                short_name = data["full_name"].replace("JOME MASJIDI", "").strip()
                if len(short_name) > 12:
                    short_name = short_name[:12] + "..."
                
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

# ========================================
# ADMIN PANEL FUNCTIONS
# ========================================

def get_admin_keyboard():
    """Admin klaviaturasi"""
    keyboard = [
        ['📊 User Analytics', '🕌 Masjid Management'],
        ['📢 Push Notifications', '📈 Statistics'],
        ['🔧 Manual Update', '⚙️ Bot Settings'],
        ['🚪 Admin Exit']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin login"""
    user_id = str(update.effective_user.id)
    
    admin_sessions.add(user_id)
    await update.message.reply_text(
        "🔐 *ADMIN PANEL*\n\nXush kelibsiz, Admin!\n\n"
        "🎯 Monitoring faol\n"
        f"📺 Kanal: @{CHANNEL_USERNAME}\n"
        f"👥 Userlar: {len(user_settings)}\n"
        f"🕌 Masjidlar: {len(MASJIDLAR_3_ALIFBO)}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )
    logger.info(f"👨‍💼 Admin login: {user_id}")

async def show_user_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User analytics"""
    total_users = len(user_settings)
    active_users = len([u for u, last in user_last_activity.items() 
                       if last > datetime.now() - timedelta(days=7)])
    
    # Yangi userlar (7 kun)
    week_ago = datetime.now() - timedelta(days=7)
    new_users = len([d for d in user_join_dates.values() if d > week_ago])
    
    # Top faol userlar
    top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Masjid statistikasi
    avg_selected = sum(len(settings.get('selected_masjids', [])) 
                      for settings in user_settings.values()) / max(total_users, 1)
    
    message = f"""📊 *USER ANALYTICS*

👥 *Umumiy:*
• Jami foydalanuvchilar: *{total_users}*
• Faol (7 kun): *{active_users}*
• Yangi (7 kun): *{new_users}*
• O'rtacha tanlangan: *{avg_selected:.1f}* masjid

🔥 *Eng faol:*"""
    
    for i, (user_id, activity) in enumerate(top_users, 1):
        try:
            user_info = await bot_app.bot.get_chat(int(user_id))
            name = user_info.first_name or "Noma'lum"
        except:
            name = "Noma'lum"
        message += f"\n{i}. {name}: {activity} ta harakat"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def handle_manual_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual vaqt yangilash"""
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    
    # +5 daqiqa qo'shib test vaqtlari
    test_times = {
        "Bomdod": (now.replace(hour=5, minute=0) + timedelta(minutes=5)).strftime("%H:%M"),
        "Peshin": (now.replace(hour=12, minute=30) + timedelta(minutes=5)).strftime("%H:%M"),
        "Asr": (now.replace(hour=15, minute=45) + timedelta(minutes=5)).strftime("%H:%M"),
        "Shom": (now.replace(hour=18, minute=20) + timedelta(minutes=5)).strftime("%H:%M"),
        "Hufton": (now.replace(hour=20, minute=0) + timedelta(minutes=5)).strftime("%H:%M")
    }
    
    # Barcha masjidlarni yangilash
    updated_count = 0
    for masjid_key in MASJIDLAR_3_ALIFBO.keys():
        if masjid_key in masjidlar_data:
            masjidlar_data[masjid_key].update(test_times)
            MASJIDLAR_3_ALIFBO[masjid_key]["last_updated"] = now.strftime('%Y-%m-%d')
            updated_count += 1
    
    # Barcha foydalanuvchilarga push
    notification_message = f"""🔄 *ADMIN TOMONIDAN YANGILANDI*

Barcha masjidlar vaqti yangilandi:

🌅 Bomdod: *{test_times['Bomdod']}*
☀️ Peshin: *{test_times['Peshin']}*
🌆 Asr: *{test_times['Asr']}*
🌇 Shom: *{test_times['Shom']}*
🌙 Hufton: *{test_times['Hufton']}*

📅 Yangilangan: {now.strftime("%d.%m.%Y %H:%M")}
👨‍💼 Admin tomonidan manual yangilanish"""
    
    sent_count = 0
    for user_id in user_settings.keys():
        try:
            await bot_app.bot.send_message(
                chat_id=int(user_id),
                text=notification_message,
                parse_mode=ParseMode.MARKDOWN
            )
            sent_count += 1
            await asyncio.sleep(0.1)
        except:
            pass
    
    push_notification_stats['admin_update'] += sent_count
    
    await update.message.reply_text(
        f"""✅ *MANUAL UPDATE MUVAFFAQIYATLI*

• Yangilangan masjidlar: *{updated_count}*
• Push yuborilgan userlar: *{sent_count}*

🕐 Yangi vaqtlar faol!""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

# ========================================
# BOT COMMAND HANDLERS
# ========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    # Analytics
    log_user_join(user_id_str)
    log_user_activity(user_id_str, 'start')
    
    # Default masjidlarni tanlash
    if user_id_str not in user_settings:
        save_user_masjids(user_id, set(MASJIDLAR_3_ALIFBO.keys()))
        logger.info(f"👤 Yangi user: {user_id} - barcha masjidlar tanlandi")
    
    # Welcome message
    welcome_message = f"""🕌 *Assalomu alaykum!*

*Qo'qon Masjidlari Namaz Vaqti Botiga xush kelibsiz!*

🔄 *REAL-TIME YANGILANISHLAR:*
Bot @{CHANNEL_USERNAME} kanalini doimiy kuzatib turadi va namaz vaqtlarini avtomatik yangilaydi!

🔤 *3 ALIFBO QOLLAB-QUVVATLASH:*
• **Lotin:** norbutabek, gishtlik, bomdod
• **Kiril:** норбутабек, гиштлик, бомдод  
• **Arab:** نوربوتابيك, غیشتلیك, فجر

🖼️ *OCR RASM TAHLILI:*
{'✅ Rasmlardan avtomatik matn o\'qish faol' if OCR_AVAILABLE else '⚠️ Faqat matn tahlili (OCR faol emas)'}

⚙️ *Sozlamalar* orqali kerakli masjidlarni tanlashingiz mumkin.

👨‍💼 *Admin:* `{ADMIN_PASSWORD}` yozing

📍 Barcha vaqtlar Qo'qon mahalliy vaqti bo'yicha."""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha xabarlarni boshqarish"""
    text = update.message.text
    user_id = str(update.effective_user.id)
    
    # Analytics
    log_user_activity(user_id, 'message')
    
    # Admin login check
    if text == ADMIN_PASSWORD:
        await admin_login(update, context)
        return
    
    # Admin panel commands
    if is_admin(user_id):
        admin_commands = {
            '📊 User Analytics': show_user_analytics,
            '🔧 Manual Update': handle_manual_update,
            '🚪 Admin Exit': handle_admin_exit
        }
        
        if text in admin_commands:
            await admin_commands[text](update, context)
            return
    
    # Regular user commands
    user_commands = {
        '🕐 Barcha vaqtlar': handle_all_times,
        '⏰ Eng yaqin vaqt': handle_next_prayer,
        '🕌 Masjidlar': handle_all_masjids,
        '⚙️ Sozlamalar': handle_settings,
        'ℹ️ Yordam': handle_help
    }
    
    if text in user_commands:
        await user_commands[text](update, context)
    else:
        await update.message.reply_text(
            "Quyidagi knopkalardan foydalaning:",
            reply_markup=get_main_keyboard()
        )

async def handle_admin_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin paneldan chiqish"""
    user_id = str(update.effective_user.id)
    admin_sessions.discard(user_id)
    
    await update.message.reply_text(
        "👋 Admin paneldan muvaffaqiyatli chiqildi.\n\nOddiy foydalanuvchi rejimiga qaytdingiz.",
        reply_markup=get_main_keyboard()
    )

# ========================================
# USER COMMAND HANDLERS
# ========================================

async def handle_all_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha namaz vaqtlari"""
    message = "🕐 *NAMAZ VAQTLARI*\n\n"
    
    for masjid_key in MASJIDLAR_3_ALIFBO.keys():
        if masjid_key in masjidlar_data:
            times = masjidlar_data[masjid_key]
            name = MASJIDLAR_3_ALIFBO[masjid_key]["full_name"]
            last_updated = MASJIDLAR_3_ALIFBO[masjid_key]["last_updated"]
            
            message += f"🕌 *{name.replace('JOME MASJIDI', '').strip()}*\n"
            message += f"🌅 Bomdod: *{times['Bomdod']}* ☀️ Peshin: *{times['Peshin']}*\n"
            message += f"🌆 Asr: *{times['Asr']}* 🌇 Shom: *{times['Shom']}* 🌙 Hufton: *{times['Hufton']}*\n"
            message += f"📅 Yangilangan: {last_updated}\n\n"
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    message += f"⏰ Hozirgi vaqt: {current_time} (Qo'qon vaqti)\n"
    message += f"🔄 @{CHANNEL_USERNAME} dan real-time yangilanadi\n"
    message += f"🔤 3 alifbo qo'llab-quvvatlanadi"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_next_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Eng yaqin namaz vaqti"""
    user_id = str(update.effective_user.id)
    selected = get_user_selected_masjids(user_id)
    
    if not selected:
        await update.message.reply_text(
            "❌ Hech qanday masjid tanlanmagan!\n⚙️ Sozlamalar orqali masjidlarni tanlang.",
            reply_markup=get_main_keyboard()
        )
        return
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    prayer_names = ["Bomdod", "Peshin", "Asr", "Shom", "Hufton"]
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
        
        message = f"""⏰ *ENG YAQIN NAMAZ VAQTI*

🕌 {next_prayer['masjid'].replace('JOME MASJIDI', '').strip()}
🕐 {next_prayer['prayer']}: *{next_prayer['time']}*

📅 Hozirgi vaqt: {current_time} (Qo'qon vaqti)

🔔 Vaqt yangilanishi bilan avtomatik xabar olasiz!"""
    else:
        message = f"""📅 Bugun uchun barcha namaz vaqtlari o'tdi.

Ertaga Bomdod vaqti bilan davom etadi.

⏰ Hozirgi vaqt: {current_time} (Qo'qon vaqti)"""
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_all_masjids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha masjidlar ro'yxati"""
    message = "🕌 *BARCHA MASJIDLAR*\n\n"
    
    for i, (key, data) in enumerate(MASJIDLAR_3_ALIFBO.items(), 1):
        coords = data['coordinates']
        popularity = masjid_popularity[key]
        
        message += f"{i}. *{data['full_name']}*\n"
        message += f"   📍 {coords[0]:.3f}, {coords[1]:.3f}\n"
        message += f"   📊 {popularity} marta tanlangan\n\n"
    
    message += f"📊 Jami: {len(MASJIDLAR_3_ALIFBO)} ta masjid\n\n"
    message += "⚙️ *Sozlamalar* orqali kerakli masjidlarni tanlang.\n"
    message += f"🔄 Vaqtlar @{CHANNEL_USERNAME} dan real-time yangilanadi!"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi sozlamalari"""
    user_id = str(update.effective_user.id)
    selected = get_user_selected_masjids(user_id)
    
    log_user_activity(user_id, 'settings')
    
    message = f"""⚙️ *PUSH NOTIFICATION SOZLAMALARI*

Siz hozirda *{len(selected)} ta masjid* uchun bildirishnoma olasiz.

🔔 *Real-time yangilanishlar:*
@{CHANNEL_USERNAME} kanalidan avtomatik yangilanadi!

🔤 *3 alifbo qo'llab-quvvatlanadi:*
• Lotin, Kiril, Arab alifbolari

🖼️ *OCR:* {'✅ Rasm tahlili faol' if OCR_AVAILABLE else '❌ Faqat matn tahlili'}

Quyida masjidlarni tanlang/bekor qiling:
✅ - Tanlangan (push olasiz)
⬜ - Tanlanmagan"""
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_masjid_selection_keyboard(user_id)
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    help_text = f"""ℹ️ *YORDAM*

🔄 *REAL-TIME KANAL MONITORING:*
Bot @{CHANNEL_USERNAME} kanalini doimiy kuzatib turadi va namaz vaqtlarini avtomatik yangilaydi!

🔤 *3 ALIFBO QOLLAB-QUVVATLASH:*
• **Lotin:** norbutabek, gishtlik, bomdod, peshin
• **Kiril:** норбутабек, гиштлик, бомдод, пешин  
• **Arab:** نوربوتابيك, غیشتلیك, فجر, ظهر

🖼️ *OCR RASM TAHLILI:*
{'✅ Faol - rasmlardan avtomatik matn o\'qish' if OCR_AVAILABLE else '⚠️ Faol emas - faqat matn tahlili'}

*Bot funksiyalari:*
🕐 Barcha vaqtlar - Hamma masjidlar vaqti
⏰ Eng yaqin vaqt - Keyingi namaz vaqti
🕌 Masjidlar - To'liq ro'yxat va koordinatalar
⚙️ Sozlamalar - Push notification uchun masjid tanlash

🔔 *PUSH NOTIFICATION:*
• Namaz vaqti yangilanishi bilan avtomatik xabar
• Faqat tanlangan masjidlar uchun
• Real-time o'zgarishlar haqida darhol xabar

👨‍💼 *ADMIN PANEL:*
`{ADMIN_PASSWORD}` yozib admin funksiyalariga kiring

*Vaqt zonasi:* Qo'qon mahalliy vaqti (UTC+5)
*Kanal:* @{CHANNEL_USERNAME}
*Monitoring:* Har 2 daqiqada avtomatik"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========================================
# CALLBACK QUERY HANDLERS
# ========================================

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query'larni boshqarish"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    # User settings callback'lar
    if data.startswith("toggle_"):
        await handle_masjid_toggle(query, context)
    elif data == "select_all":
        await handle_select_all(query, context)
    elif data == "deselect_all":
        await handle_deselect_all(query, context)
    elif data == "save_settings":
        await handle_save_settings(query, context)
    elif data == "back_main":
        await handle_back_main(query, context)

async def handle_masjid_toggle(query, context):
    """Masjid tanlash/bekor qilish"""
    user_id = str(query.from_user.id)
    masjid_key = query.data.replace("toggle_", "")
    
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

async def handle_select_all(query, context):
    """Barcha masjidlarni tanlash"""
    user_id = str(query.from_user.id)
    save_user_masjids(user_id, set(MASJIDLAR_3_ALIFBO.keys()))
    
    await query.edit_message_reply_markup(
        reply_markup=get_masjid_selection_keyboard(user_id)
    )

async def handle_deselect_all(query, context):
    """Barcha masjidlarni bekor qilish"""
    user_id = str(query.from_user.id)
    save_user_masjids(user_id, set())
    
    await query.edit_message_reply_markup(
        reply_markup=get_masjid_selection_keyboard(user_id)
    )

async def handle_save_settings(query, context):
    """Sozlamalarni saqlash"""
    user_id = str(query.from_user.id)
    selected = get_user_selected_masjids(user_id)
    
    if selected:
        mosque_names = [MASJIDLAR_3_ALIFBO[key]["full_name"].replace('JOME MASJIDI', '').strip() 
                       for key in selected]
        
        await query.edit_message_text(
            f"""✅ *SOZLAMALAR SAQLANDI!*

Siz {len(selected)} ta masjid uchun push notification olasiz:

{', '.join(mosque_names)}

🔔 Namaz vaqti yangilanishi bilan avtomatik xabar olasiz!""",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "⚠️ *HECH QANDAY MASJID TANLANMADI*\n\nSiz hech qanday push notification olmaysiz.\n\nKerak bo'lsa qaytadan sozlamalarni ochib masjid tanlang.",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_back_main(query, context):
    """Asosiy menyuga qaytish"""
    await query.edit_message_text("🔙 Asosiy menyuga qaytdingiz.")

# ========================================
# ERROR HANDLER
# ========================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler"""
    logger.error(f"❌ Update {update} xatolik keltirib chiqardi: {context.error}")

# ========================================
# MAIN FUNCTION
# ========================================

def main():
    """Asosiy funksiya"""
    global bot_app
    
    try:
        # Flask health check server
        threading.Thread(target=run_flask, daemon=True).start()
        logger.info("🌐 Flask server ishga tushdi")
        
        # Telegram bot
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Command handlers
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot_app.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Error handler
        bot_app.add_error_handler(error_handler)
        
        # Logging
        logger.info("✅ Bot handlerlar qo'shildi")
        logger.info(f"🎯 Monitoring kanal: @{CHANNEL_USERNAME}")
        logger.info(f"🧪 Test mode: {'✅ Faol' if TEST_MODE else '❌ Faol emas'}")
        logger.info(f"🔤 3 alifbo qo'llab-quvvatlanadi: Lotin, Kiril, Arab")
        logger.info(f"🖼️ OCR: {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}")
        logger.info(f"👨‍💼 Admin parol: {ADMIN_PASSWORD}")
        
        # Console output
        print("=" * 60)
        print("🚀 QOQON MASJIDLAR BOT ISHGA TUSHDI!")
        print("=" * 60)
        print(f"📺 Kanal: @{CHANNEL_USERNAME}")
        print(f"🧪 Test mode: {'✅ Faol' if TEST_MODE else '❌ Production'}")
        print(f"🔄 Monitoring: Har 2 daqiqada")
        print(f"🔤 3 alifbo: Lotin, Kiril, Arab")
        print(f"🖼️ OCR: {'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}")
        print(f"👨‍💼 Admin: '{ADMIN_PASSWORD}' yozing")
        print(f"🕌 Masjidlar: {len(MASJIDLAR_3_ALIFBO)} ta")
        print("=" * 60)
        
        # Kanal monitoring thread
        def run_monitoring():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logger.info("🔄 Monitoring thread ishga tushdi")
                loop.run_until_complete(start_channel_monitoring())
            except Exception as e:
                logger.error(f"❌ Monitoring thread xatolik: {e}")
            finally:
                loop.close()
        
        monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
        monitoring_thread.start()
        
        logger.info("✅ Monitoring thread ishga tushirildi")
        
        # Bot polling
        logger.info("🚀 Bot polling boshlandi...")
        bot_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️ Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Bot ishga tushirishda xatolik: {e}")
        print(f"❌ KRITIK XATOLIK: {e}")
    finally:
        print("👋 Bot to'xtatildi")

if __name__ == '__main__':
    main()
