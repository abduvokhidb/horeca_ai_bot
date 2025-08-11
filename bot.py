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

# Health check uchun Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return 'Bot ishlaydi', 200

@app.route('/')
def home():
    return 'Masjidlar Bot - Admin Panel Active', 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot sozlamalari
BOT_TOKEN = os.getenv('BOT_TOKEN')
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

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable kerak!")
    exit(1)

# ADMIN PANEL TIZIMI
ADMIN_PASSWORD = "menadminman"
admin_sessions = set()
admin_temp_data = {}

# ANALYTICS VA STATISTIKA
user_activity = defaultdict(int)
user_join_dates = {}
user_last_activity = {}
masjid_popularity = defaultdict(int)
daily_stats = defaultdict(lambda: defaultdict(int))
push_notification_stats = defaultdict(int)

def log_user_activity(user_id: str, action: str):
    """Foydalanuvchi faolligini yozish"""
    user_activity[user_id] += 1
    user_last_activity[user_id] = datetime.now()
    
    today = datetime.now().strftime('%Y-%m-%d')
    daily_stats[today]['total_actions'] += 1
    daily_stats[today][action] += 1

def log_user_join(user_id: str):
    """Yangi foydalanuvchi qo'shilishini yozish"""
    if user_id not in user_join_dates:
        user_join_dates[user_id] = datetime.now()
        today = datetime.now().strftime('%Y-%m-%d')
        daily_stats[today]['new_users'] += 1

def is_admin(user_id: str) -> bool:
    """Admin ekanligini tekshirish"""
    return str(user_id) in admin_sessions

# Global variables
bot_app = None
user_settings = {}
last_posts_hash = {}

# MASJIDLAR MA'LUMOTLARI
MASJIDLAR_3_ALIFBO = {
    "NORBUTABEK": {
        "full_name": "NORBUTABEK JOME MASJIDI",
        "coordinates": [40.3925, 71.7412],
        "patterns": {
            "lotin": ["norbutabek", "norbu tabek"],
            "kiril": ["норбутабек", "норбу табек"],
            "arab": ["نوربوتابيك", "نوربو تابيك"]
        }
    },
    "GISHTLIK": {
        "full_name": "GISHTLIK JOME MASJIDI",
        "coordinates": [40.3901, 71.7389],
        "patterns": {
            "lotin": ["gishtlik", "g'ishtlik"],
            "kiril": ["гиштлик", "ғиштлик"],
            "arab": ["غیشتلیك", "گشتلیك"]
        }
    },
    "SHAYXULISLOM": {
        "full_name": "SHAYXULISLOM JOME MASJIDI",
        "coordinates": [40.3867, 71.7435],
        "patterns": {
            "lotin": ["shayxulislom", "shayx ul islom"],
            "kiril": ["шайхулислом", "шайх ул ислом"],
            "arab": ["شیخ الاسلام", "شایخ الاسلام"]
        }
    }
}

# NAMAZ VAQTLARI PATTERNS
NAMAZ_VAQTLARI_3_ALIFBO = {
    "lotin": {
        "bomdod": r'(?:bomdod|fajr|subh)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:peshin|zuhr|zuhur)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:asr|ikindi)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:shom|maghrib)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:hufton|isha)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    },
    "kiril": {
        "bomdod": r'(?:бомдод|фажр|субх)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:пешин|зухр)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:аср|икинди)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:шом|магриб)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:хуфтон|иша)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    },
    "arab": {
        "bomdod": r'(?:فجر|صبح)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:ظهر|زهر)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:عصر)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:مغرب)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:عشاء|عشا)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    }
}

# Default namaz vaqtlari
masjidlar_data = {
    "NORBUTABEK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:45", "Shom": "19:35", "Hufton": "21:15"},
    "GISHTLIK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:15", "Shom": "19:30", "Hufton": "21:00"},
    "SHAYXULISLOM": {"Bomdod": "04:45", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"}
}

# ADMIN FUNCTIONS
async def admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin login"""
    user_id = str(update.effective_user.id)
    
    if update.message.text == ADMIN_PASSWORD:
        admin_sessions.add(user_id)
        await update.message.reply_text(
            "🔐 *ADMIN PANEL*\n\nXush kelibsiz, Admin!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_keyboard()
        )
        logger.info(f"👨‍💼 Admin login: {user_id}")

def get_admin_keyboard():
    """Admin klaviaturasi"""
    keyboard = [
        ['📊 User Analytics', '🕌 Masjid Management'],
        ['📢 Push Notifications', '📈 Statistics'],
        ['🔧 Manual Update', '🚪 Admin Exit']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel handler"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if not is_admin(user_id):
        return
    
    if text == '📊 User Analytics':
        await show_user_analytics(update, context)
    elif text == '📢 Push Notifications':
        await show_push_notifications(update, context)
    elif text == '📈 Statistics':
        await show_statistics(update, context)
    elif text == '🔧 Manual Update':
        await handle_manual_update(update, context)
    elif text == '🚪 Admin Exit':
        admin_sessions.discard(user_id)
        await update.message.reply_text(
            "👋 Admin paneldan chiqildi",
            reply_markup=get_main_keyboard()
        )

async def show_user_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User analytics ko'rsatish"""
    total_users = len(user_settings)
    active_users = len([u for u, last in user_last_activity.items() 
                       if last > datetime.now() - timedelta(days=7)])
    
    # Yangi userlar (oxirgi 7 kun)
    week_ago = datetime.now() - timedelta(days=7)
    new_users = len([d for d in user_join_dates.values() if d > week_ago])
    
    message = f"""📊 *USER ANALYTICS*

👥 *Umumiy statistika:*
• Jami foydalanuvchilar: *{total_users}*
• Faol foydalanuvchilar (7 kun): *{active_users}*
• Yangi foydalanuvchilar (7 kun): *{new_users}*

🔥 *Faollik:*
• Jami harakatlar: *{sum(user_activity.values())}*"""
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def show_push_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Push notification panel"""
    total_sent = sum(push_notification_stats.values())
    
    message = f"""📢 *PUSH NOTIFICATIONS*

📊 *Statistika:*
• Jami yuborilgan: *{total_sent}*

💡 *Test yuborish:*"""
    
    keyboard = [
        [InlineKeyboardButton("🧪 Test notification", callback_data="admin_test_push")],
        [InlineKeyboardButton("📢 Ommaviy xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Umumiy statistika"""
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = daily_stats[today]
    
    message = f"""📈 *BOT STATISTIKA*

📅 *Bugun:*
• Jami harakatlar: *{today_stats['total_actions']}*
• Yangi foydalanuvchilar: *{today_stats['new_users']}*
• Start buyruqlari: *{today_stats.get('start', 0)}*"""
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def handle_manual_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual yangilanish"""
    # Hozirgi vaqt + 5 daqiqa
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    
    test_times = {
        "Bomdod": (now.replace(hour=5, minute=0) + timedelta(minutes=5)).strftime("%H:%M"),
        "Peshin": (now.replace(hour=12, minute=30) + timedelta(minutes=5)).strftime("%H:%M"),
        "Asr": (now.replace(hour=15, minute=45) + timedelta(minutes=5)).strftime("%H:%M"),
        "Shom": (now.replace(hour=18, minute=20) + timedelta(minutes=5)).strftime("%H:%M"),
        "Hufton": (now.replace(hour=20, minute=0) + timedelta(minutes=5)).strftime("%H:%M")
    }
    
    # Barcha masjidlar uchun vaqtlarni yangilash
    for masjid_key in MASJIDLAR_3_ALIFBO.keys():
        if masjid_key in masjidlar_data:
            masjidlar_data[masjid_key].update(test_times)
    
    # Push notification yuborish
    notification_message = f"""🔄 *ADMIN TOMONIDAN YANGILANDI*

Barcha masjidlar vaqti yangilandi:

🌅 Bomdod: *{test_times['Bomdod']}*
☀️ Peshin: *{test_times['Peshin']}*
🌆 Asr: *{test_times['Asr']}*
🌇 Shom: *{test_times['Shom']}*
🌙 Hufton: *{test_times['Hufton']}*

📅 {now.strftime("%d.%m.%Y %H:%M")}"""
    
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
        f"✅ Yangilanish muvaffaqiyatli!\n📤 {sent_count} ta userga yuborildi",
        reply_markup=get_admin_keyboard()
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin callback handler"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if not is_admin(user_id):
        return
    
    data = query.data
    
    if data == "admin_test_push":
        test_message = """🧪 *TEST NOTIFICATION*

Bu test xabari. Push notification tizimi ishlayapti! ✅

📅 """ + datetime.now().strftime("%d.%m.%Y %H:%M")
        
        try:
            await bot_app.bot.send_message(
                chat_id=int(user_id),
                text=test_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            await query.edit_message_text(
                "✅ Test notification muvaffaqiyatli yuborildi!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
                ])
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Xatolik: {e}")
    
    elif data == "admin_broadcast":
        admin_temp_data[user_id] = {'action': 'broadcast_message'}
        await query.edit_message_text(
            "📢 Ommaviy xabar uchun matnni yozing:\n\n(Bekor qilish: /cancel)"
        )
    
    elif data == "admin_back":
        await query.edit_message_text(
            "🔐 *ADMIN PANEL*",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast xabarini yuborish"""
    user_id = str(update.effective_user.id)
    
    if not is_admin(user_id) or user_id not in admin_temp_data:
        return
    
    if update.message.text == '/cancel':
        del admin_temp_data[user_id]
        await update.message.reply_text("❌ Bekor qilindi", reply_markup=get_admin_keyboard())
        return
    
    broadcast_text = update.message.text
    
    # Yuborish
    sent_count = 0
    for target_user_id in user_settings.keys():
        try:
            await bot_app.bot.send_message(
                chat_id=int(target_user_id),
                text=f"📢 *ADMIN XABARI*\n\n{broadcast_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent_count += 1
            await asyncio.sleep(0.1)
        except:
            pass
    
    push_notification_stats['broadcast'] += sent_count
    
    await update.message.reply_text(
        f"✅ Broadcast yakunlandi!\n📤 {sent_count} ta userga yuborildi",
        reply_markup=get_admin_keyboard()
    )
    
    del admin_temp_data[user_id]

# UTILITY FUNCTIONS
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def detect_script_type(text: str) -> str:
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
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
    
    for mosque_key, mosque_data in MASJIDLAR_3_ALIFBO.items():
        for alifbo, patterns in mosque_data["patterns"].items():
            for pattern in patterns:
                if pattern in text or similarity(text, pattern) > threshold:
                    logger.info(f"✅ Masjid topildi: {mosque_key}")
                    return mosque_key
    
    return None

def extract_prayer_times_3_alifbo(text: str) -> Dict[str, str]:
    prayer_times = {}
    text = text.lower()
    
    for alifbo, patterns in NAMAZ_VAQTLARI_3_ALIFBO.items():
        for prayer_name, pattern in patterns.items():
            if prayer_name not in prayer_times:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    time_str = matches[0].replace('-', ':').replace('–', ':').replace('.', ':')
                    prayer_times[prayer_name.capitalize()] = time_str
    
    return prayer_times

# CHANNEL MONITORING
async def scrape_telegram_channel_3_alifbo():
    global last_posts_hash
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(CHANNEL_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        posts = soup.find_all('div', class_='tgme_widget_message')
        
        if posts:
            logger.info(f"📥 {len(posts)} ta post topildi")
            for post in posts[-2:]:
                await process_telegram_post_3_alifbo(post)
        
    except Exception as e:
        logger.error(f"❌ Kanal scraping xatolik: {e}")

async def process_telegram_post_3_alifbo(post):
    try:
        post_content = str(post)
        post_hash = hashlib.md5(post_content.encode()).hexdigest()
        
        text_div = post.find('div', class_='tgme_widget_message_text')
        if text_div:
            all_text = text_div.get_text(strip=True, separator=' ')
            
            mosque_key = find_mosque_3_alifbo(all_text)
            if mosque_key:
                prayer_times = extract_prayer_times_3_alifbo(all_text)
                if prayer_times:
                    await update_mosque_data_and_notify(mosque_key, prayer_times)
        
    except Exception as e:
        logger.error(f"❌ Post tahlil xatolik: {e}")

async def update_mosque_data_and_notify(mosque_key: str, new_prayer_times: Dict[str, str]):
    if mosque_key not in masjidlar_data:
        return
    
    mosque_name = MASJIDLAR_3_ALIFBO[mosque_key]["full_name"]
    old_times = masjidlar_data[mosque_key].copy()
    changes = {}
    
    for prayer, new_time in new_prayer_times.items():
        if prayer in old_times and old_times[prayer] != new_time:
            changes[prayer] = {'old': old_times[prayer], 'new': new_time}
            masjidlar_data[mosque_key][prayer] = new_time
    
    if changes:
        logger.info(f"✅ {mosque_name} yangilandi: {changes}")
        await send_push_notifications(mosque_key, mosque_name, changes)

async def send_push_notifications(mosque_key: str, mosque_name: str, changes: Dict[str, Dict]):
    if not bot_app:
        return
    
    message = f"🔔 *NAMAZ VAQTI YANGILANDI*\n\n🕌 *{mosque_name.replace('JOME MASJIDI', '').strip()}*\n\n"
    
    for prayer, change in changes.items():
        message += f"🕐 {prayer}: {change['old']} → *{change['new']}*\n"
    
    message += f"\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n📺 @{CHANNEL_USERNAME}"
    
    sent_count = 0
    for user_id, settings in user_settings.items():
        selected_mosques = set(settings.get('selected_masjids', []))
        if mosque_key in selected_mosques:
            try:
                await bot_app.bot.send_message(
                    chat_id=int(user_id),
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
                sent_count += 1
                await asyncio.sleep(0.1)
            except:
                pass
    
    logger.info(f"📤 {sent_count} ta userga notification yuborildi")

async def start_channel_monitoring_3_alifbo():
    logger.info(f"👀 Kanal monitoring boshlandi: @{CHANNEL_USERNAME}")
    
    while True:
        try:
            await scrape_telegram_channel_3_alifbo()
            await asyncio.sleep(120)
        except Exception as e:
            logger.error(f"❌ Monitoring xatolik: {e}")
            await asyncio.sleep(300)

# USER FUNCTIONS
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
        ['🕌 Masjidlar', '⚙️ Sozlamalar'],
        ['ℹ️ Yordam']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# BOT HANDLERS
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_user_join(str(user_id))
    log_user_activity(str(user_id), 'start')
    
    if str(user_id) not in user_settings:
        save_user_masjids(user_id, set(MASJIDLAR_3_ALIFBO.keys()))
    
    welcome_message = f"""🕌 Assalomu alaykum!

*Qo'qon Masjidlari Namaz Vaqti Botiga xush kelibsiz!*

🔄 Real-time yangilanishlar: @{CHANNEL_USERNAME}
🔤 3 alifbo: Lotin, Kiril, Arab
👨‍💼 Admin: `{ADMIN_PASSWORD}` yozing

⚙️ Sozlamalar orqali masjidlarni tanlang."""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)
    
    log_user_activity(user_id, 'message')
    
    # Admin login check
    if text == ADMIN_PASSWORD:
        await admin_login(update, context)
        return
    
    # Admin panel check
    if is_admin(user_id):
        if user_id in admin_temp_data and admin_temp_data[user_id].get('action') == 'broadcast_message':
            await handle_broadcast_message(update, context)
            return
        elif text in ['📊 User Analytics', '📢 Push Notifications', '📈 Statistics', '🔧 Manual Update', '🚪 Admin Exit']:
            await handle_admin_panel(update, context)
            return
    
    # Regular user commands
    if text == '🕐 Barcha vaqtlar':
        await handle_all_times(update, context)
    elif text == '🕌 Masjidlar':
        await handle_all_masjids(update, context)
    elif text == 'ℹ️ Yordam':
        await handle_help(update, context)
    else:
        await update.message.reply_text(
            "Quyidagi knopkalardan foydalaning:",
            reply_markup=get_main_keyboard()
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query handler"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if is_admin(user_id):
        await handle_admin_callback(update, context)

async def handle_all_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🕐 *NAMAZ VAQTLARI:*\n\n"
    
    for masjid_key in MASJIDLAR_3_ALIFBO.keys():
        if masjid_key in masjidlar_data:
            times = masjidlar_data[masjid_key]
            name = MASJIDLAR_3_ALIFBO[masjid_key]["full_name"]
            
            message += f"🕌 *{name.replace('JOME MASJIDI', '').strip()}*\n"
            message += f"🌅 Bomdod: *{times['Bomdod']}* ☀️ Peshin: *{times['Peshin']}*\n"
            message += f"🌆 Asr: *{times['Asr']}* 🌇 Shom: *{times['Shom']}* 🌙 Hufton: *{times['Hufton']}*\n\n"
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    message += f"⏰ Hozirgi vaqt: {current_time}\n🔄 @{CHANNEL_USERNAME} dan real-time yangilanadi"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_all_masjids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🕌 *BARCHA MASJIDLAR:*\n\n"
    
    for i, (key, data) in enumerate(MASJIDLAR_3_ALIFBO.items(), 1):
        message += f"{i}. {data['full_name']}\n"
    
    message += f"\n📊 Jami: {len(MASJIDLAR_3_ALIFBO)} ta masjid"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""ℹ️ *YORDAM*

🔄 *REAL-TIME MONITORING:*
Bot @{CHANNEL_USERNAME} kanalini kuzatadi

🔤 *3 ALIFBO:* Lotin, Kiril, Arab

👨‍💼 *Admin panel:* `{ADMIN_PASSWORD}` yozing

*Funksiyalar:*
🕐 Barcha vaqtlar
🕌 Masjidlar ro'yxati
⚙️ Sozlamalar

*Admin funksiyalar:*
📊 User Analytics - statistika
📢 Push Notifications - test va broadcast
📈 Statistics - bot statistika
🔧 Manual Update - vaqtlarni yangilash"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Xatolik yuz berdi:", exc_info=context.error)

def main():
    """Asosiy funksiya"""
    global bot_app
    
    try:
        # Flask
        threading.Thread(target=run_flask, daemon=True).start()
        
        # Bot
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Handlers
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot_app.add_handler(CallbackQueryHandler(handle_callback_query))
        bot_app.add_error_handler(error_handler)
        
        logger.info("✅ Bot ishga tushmoqda...")
        logger.info(f"🎯 Monitoring kanal: @{CHANNEL_USERNAME}")
        logger.info(f"👨‍💼 Admin parol: {ADMIN_PASSWORD}")
        
        print("🚀 Bot ishga tushdi! ✅")
        print(f"📺 Kanal: @{CHANNEL_USERNAME}")
        print(f"👨‍💼 Admin: '{ADMIN_PASSWORD}' yozing")
        
        # Monitoring thread
        def run_monitoring():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logger.info("🔄 Monitoring thread boshlandi")
                loop.run_until_complete(start_channel_monitoring_3_alifbo())
            except Exception as e:
                logger.error(f"❌ Monitoring xatolik: {e}")
            finally:
                loop.close()
        
        monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
        monitoring_thread.start()
        
        logger.info("✅ Monitoring thread ishga tushirildi")
        
        # Bot polling
        bot_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        print(f"❌ Xatolik: {e}")

if __name__ == '__main__':
    main()
