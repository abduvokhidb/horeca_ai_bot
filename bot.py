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
except ImportError:
    OCR_AVAILABLE = False

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
    }
}

# 3 ALIFBO NAMAZ VAQTLARI PATTERNS
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

# Default namaz vaqtlari
masjidlar_data = {
    "NORBUTABEK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:45", "Shom": "19:35", "Hufton": "21:15"},
    "GISHTLIK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:15", "Shom": "19:30", "Hufton": "21:00"},
    "SHAYXULISLOM": {"Bomdod": "04:45", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"}
}

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def detect_script_type(text: str) -> str:
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F')
    cyrillic_chars = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
    latin_chars = sum(1 for char in text if 'a' <= char.lower() <= 'z')
    
    total_chars = arabic_chars + cyrillic_chars + latin_chars
    
    if total_chars == 0:
        return "lotin"
    
    if arabic_chars / total_chars > 0.3:
        return "arab"
    elif cyrillic_chars / total_chars > 0.3:
        return "kiril"
    else:
        return "lotin"

def find_mosque_3_alifbo(text: str, threshold: float = 0.7) -> Optional[str]:
    text = text.lower().strip()
    script_type = detect_script_type(text)
    
    logger.info(f"🔍 Masjid qidirilmoqda: '{text[:50]}...' ({script_type} alifbosi)")
    
    best_match = None
    best_score = 0
    
    for mosque_key, mosque_data in MASJIDLAR_3_ALIFBO.items():
        for alifbo, patterns in mosque_data["patterns"].items():
            weight = 1.0 if alifbo == script_type else 0.8
            
            for pattern in patterns:
                score = similarity(text, pattern) * weight
                if score > threshold and score > best_score:
                    best_score = score
                    best_match = mosque_key
                
                if pattern in text:
                    logger.info(f"✅ To'g'ridan-to'g'ri mos keldi: {mosque_key} ({alifbo})")
                    return mosque_key
    
    if best_match:
        logger.info(f"🎯 Eng yaxshi mos kelishi: {best_match} ({best_score:.2f})")
    else:
        logger.info(f"❌ Masjid topilmadi (threshold: {threshold})")
    
    return best_match

def extract_prayer_times_3_alifbo(text: str) -> Dict[str, str]:
    prayer_times = {}
    text = text.lower()
    script_type = detect_script_type(text)
    
    logger.info(f"🕐 Namaz vaqtlari qidirilmoqda ({script_type} alifbosi)...")
    
    for alifbo, patterns in NAMAZ_VAQTLARI_3_ALIFBO.items():
        for prayer_name, pattern in patterns.items():
            if prayer_name not in prayer_times:
                matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
                if matches:
                    time_str = matches[0].replace('-', ':').replace('–', ':').replace('—', ':').replace('.', ':')
                    prayer_key = prayer_name.capitalize()
                    if prayer_key not in prayer_times:
                        prayer_times[prayer_key] = time_str
                        logger.info(f"    ✅ {prayer_key}: {time_str} ({alifbo})")
    
    return prayer_times

async def scrape_telegram_channel_3_alifbo():
    global last_posts_hash
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        logger.info(f"🌐 Kanal tekshirilmoqda: {CHANNEL_URL}")
        
        response = requests.get(CHANNEL_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        posts = soup.find_all('div', class_='tgme_widget_message')
        
        if not posts:
            logger.warning("⚠️ Hech qanday post topilmadi")
            return
        
        logger.info(f"📥 {len(posts)} ta post topildi")
        
        # Eng yangi post'larni tekshirish
        for post in posts[-3:]:
            await process_telegram_post_3_alifbo(post)
            
    except Exception as e:
        logger.error(f"❌ Kanal scraping xatolik: {e}")

async def process_telegram_post_3_alifbo(post):
    try:
        post_link = post.find('a', class_='tgme_widget_message_date')
        post_id = post_link.get('href', '').split('/')[-1] if post_link else 'unknown'
        
        post_content = str(post)
        post_hash = hashlib.md5(post_content.encode()).hexdigest()
        
        if post_id in last_posts_hash and last_posts_hash[post_id] == post_hash:
            return
        
        last_posts_hash[post_id] = post_hash
        
        logger.info(f"📋 Yangi post tahlil qilinmoqda: {post_id}")
        
        all_text = ""
        
        text_div = post.find('div', class_='tgme_widget_message_text')
        if text_div:
            all_text += text_div.get_text(strip=True, separator=' ')
            logger.info(f"📝 Matn topildi: {all_text[:100]}...")
        
        if all_text.strip():
            await analyze_post_content_3_alifbo(all_text, post_id)
        
    except Exception as e:
        logger.error(f"❌ Post tahlil xatolik: {e}")

async def analyze_post_content_3_alifbo(text: str, post_id: str):
    logger.info(f"🔍 Post {post_id} tahlil qilinmoqda...")
    
    mosque_key = find_mosque_3_alifbo(text)
    
    if not mosque_key:
        logger.info(f"⚠️ Post {post_id}da masjid nomi topilmadi")
        return
    
    prayer_times = extract_prayer_times_3_alifbo(text)
    
    if not prayer_times:
        logger.info(f"⚠️ Post {post_id}da namaz vaqtlari topilmadi")
        return
    
    await update_mosque_data_and_notify(mosque_key, prayer_times, post_id)

async def update_mosque_data_and_notify(mosque_key: str, new_prayer_times: Dict[str, str], post_id: str):
    if mosque_key not in masjidlar_data:
        logger.warning(f"⚠️ Noma'lum masjid: {mosque_key}")
        return
    
    mosque_name = MASJIDLAR_3_ALIFBO[mosque_key]["full_name"]
    old_times = masjidlar_data[mosque_key].copy()
    changes = {}
    
    for prayer, new_time in new_prayer_times.items():
        if prayer in old_times:
            if old_times[prayer] != new_time:
                changes[prayer] = {
                    'old': old_times[prayer],
                    'new': new_time
                }
                masjidlar_data[mosque_key][prayer] = new_time
    
    if changes:
        logger.info(f"✅ {mosque_name} vaqtlari yangilandi: {changes}")
        await send_push_notifications(mosque_key, mosque_name, changes, post_id)
    else:
        logger.info(f"ℹ️ {mosque_name} vaqtlari o'zgarmagan")

async def send_push_notifications(mosque_key: str, mosque_name: str, changes: Dict[str, Dict], post_id: str):
    if not bot_app:
        logger.warning("⚠️ Bot app mavjud emas")
        return
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%d.%m.%Y")
    
    message = f"🔔 *NAMAZ VAQTI YANGILANDI*\n\n"
    message += f"🕌 *{mosque_name.replace('JOME MASJIDI', '').strip()}*\n\n"
    
    prayer_emojis = {
        "Bomdod": "🌅",
        "Peshin": "☀️",
        "Asr": "🌆", 
        "Shom": "🌇",
        "Hufton": "🌙"
    }
    
    for prayer, change in changes.items():
        emoji = prayer_emojis.get(prayer, "🕐")
        message += f"{emoji} *{prayer}:* {change['old']} → *{change['new']}*\n"
    
    message += f"\n📅 Yangilangan: {current_date} {current_time}\n"
    message += f"📺 Manba: @{CHANNEL_USERNAME}\n"
    message += f"🆔 Post: {post_id}"
    
    notified_users = 0
    
    for user_id, settings in user_settings.items():
        selected_mosques = set(settings.get('selected_masjids', []))
        
        if mosque_key in selected_mosques:
            try:
                await bot_app.bot.send_message(
                    chat_id=int(user_id),
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                notified_users += 1
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"⚠️ User {user_id}ga xabar yuborilmadi: {e}")
    
    logger.info(f"📤 {notified_users} ta foydalanuvchiga notification yuborildi")

async def start_channel_monitoring_3_alifbo():
    logger.info(f"👀 Kanal monitoring boshlandi: @{CHANNEL_USERNAME}")
    logger.info(f"🔤 3 alifbo qo'llab-quvvatlanadi: Lotin, Kiril, Arab")
    
    while True:
        try:
            await scrape_telegram_channel_3_alifbo()
            await asyncio.sleep(120)  # 2 daqiqa
            
        except Exception as e:
            logger.error(f"❌ Monitoring xatolik: {e}")
            await asyncio.sleep(300)  # 5 daqiqa

# USER SETTINGS
def get_user_selected_masjids(user_id: str) -> Set[str]:
    return set(user_settings.get(str(user_id), {}).get('selected_masjids', []))

def save_user_masjids(user_id: str, selected_masjids: Set[str]):
    user_id_str = str(user_id)
    if user_id_str not in user_settings:
        user_settings[user_id_str] = {}
    user_settings[user_id_str]['selected_masjids'] = list(selected_masjids)

def get_main_keyboard():
    keyboard = [
        ['🕐 Barcha vaqtlar', '⏰ Eng yaqin vaqt'],
        ['🕌 Masjidlar', '⚙️ Sozlamalar']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# BOT HANDLERS
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if str(user_id) not in user_settings:
        save_user_masjids(user_id, set(MASJIDLAR_3_ALIFBO.keys()))
    
    welcome_message = f"""🕌 Assalomu alaykum!

*Qo'qon Masjidlari Namaz Vaqti Botiga xush kelibsiz!*

🔄 *REAL-TIME YANGILANISHLAR:*
Bot @{CHANNEL_USERNAME} kanalini kuzatib turadi!

🔤 *3 ALIFBO QOLLAB-QUVVATLASH:*
• Lotin, Kiril, Arab

⚙️ Sozlamalar orqali masjidlarni tanlang."""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⚙️ Sozlamalar':
        await handle_settings(update, context)
    elif text == '🕌 Masjidlar':
        await handle_all_masjids(update, context)
    elif text == '🕐 Barcha vaqtlar':
        await handle_selected_masjids_times(update, context)
    elif text == '⏰ Eng yaqin vaqt':
        await handle_next_prayer(update, context)
    else:
        await update.message.reply_text(
            "Quyidagi knopkalardan foydalaning:",
            reply_markup=get_main_keyboard()
        )

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ Sozlamalar bo'limi",
        reply_markup=get_main_keyboard()
    )

async def handle_all_masjids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🕌 *BARCHA MASJIDLAR:*\n\n"
    
    for i, (key, data) in enumerate(MASJIDLAR_3_ALIFBO.items(), 1):
        message += f"{i}. {data['full_name']}\n"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_selected_masjids_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🕐 *NAMAZ VAQTLARI:*\n\n"
    
    for masjid_key in MASJIDLAR_3_ALIFBO.keys():
        if masjid_key in masjidlar_data:
            times = masjidlar_data[masjid_key]
            name = MASJIDLAR_3_ALIFBO[masjid_key]["full_name"]
            
            message += f"🕌 *{name.replace('JOME MASJIDI', '').strip()}*\n"
            message += f"🌅 Bomdod: *{times['Bomdod']}*\n"
            message += f"☀️ Peshin: *{times['Peshin']}*\n"
            message += f"🌆 Asr: *{times['Asr']}*\n"
            message += f"🌇 Shom: *{times['Shom']}*\n"
            message += f"🌙 Hufton: *{times['Hufton']}*\n\n"
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    message += f"⏰ Hozirgi vaqt: {current_time}\n"
    message += f"🔄 @{CHANNEL_USERNAME} dan real-time yangilanadi"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_next_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    message = f"⏰ *ENG YAQIN NAMOZ VAQTI*\n\nHozirgi vaqt: {current_time}"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Xatolik yuz berdi:", exc_info=context.error)

def main():
    """Asosiy funksiya - FIXED VERSION"""
    global bot_app
    
    try:
        # Flask'ni background'da ishga tushirish
        threading.Thread(target=run_flask, daemon=True).start()
        
        # Application yaratish
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Handlerlarni qoshish
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
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
        
        # Monitoring'ni alohida thread'da ishga tushirish
        def run_monitoring():
            """Monitoring'ni alohida thread'da ishga tushirish"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logger.info("🔄 Monitoring thread boshlandi")
                loop.run_until_complete(start_channel_monitoring_3_alifbo())
            except Exception as e:
                logger.error(f"❌ Monitoring thread xatolik: {e}")
            finally:
                loop.close()
        
        # Monitoring'ni alohida thread'da ishga tushirish
        monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
        monitoring_thread.start()
        
        logger.info("✅ Monitoring thread ishga tushirildi")
        
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
