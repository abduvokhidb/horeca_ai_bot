import os
import json
import asyncio
import logging
import threading
import math
import re
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Set, Optional
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import openai
from difflib import SequenceMatcher
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto
import pytesseract
from PIL import Image
import io
import requests

# Health check uchun Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return 'Bot ishlaydi', 200

@app.route('/')
def home():
    return 'Masjidlar Bot', 200

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
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'quqonnamozvaqti')  # Default production channel

# Telethon uchun - telegram.org dan olinadi
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'channel_monitor'

# Environment variables mavjudligini tekshirish
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable kerak!")
    exit(1)

if not API_ID or not API_HASH:
    logger.warning("⚠️ TELEGRAM_API_ID va TELEGRAM_API_HASH yo'q. Kanal monitoring ishlamaydi!")
    logger.info("📋 Telegram API credentials olish uchun: https://my.telegram.org")

# Test mode detection
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
if TEST_MODE:
    logger.info("🧪 TEST MODE faol!")
    CHANNEL_USERNAME = os.getenv('TEST_CHANNEL_USERNAME', CHANNEL_USERNAME)

# OpenAI sozlamalari
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Foydalanuvchi sozlamalari saqlash
user_settings = {}

# Masjidlar royxati - 3 xil alifboda
MASJIDLAR = {
    "NORBUTABEK": {
        "full_name": "NORBUTABEK JOME MASJIDI",
        "patterns": {
            "latin": ["norbutabek", "norbu tabek", "norbu-tabek"],
            "cyrillic": ["норбутабек", "норбу табек", "норбу-табек"],
            "arabic": ["نوربوتابيك", "نوربو تابيك"]
        }
    },
    "GISHTLIK": {
        "full_name": "GISHTLIK JOME MASJIDI",
        "patterns": {
            "latin": ["gishtlik", "g'ishtlik", "gʻishtlik"],
            "cyrillic": ["гиштлик", "ғиштлик"],
            "arabic": ["غیشتلیك", "گشتلیك"]
        }
    },
    "SHAYXULISLOM": {
        "full_name": "SHAYXULISLOM JOME MASJIDI", 
        "patterns": {
            "latin": ["shayxulislom", "shayx ul islom", "shaykh ul islam"],
            "cyrillic": ["шайхулислом", "шайх ул ислом"],
            "arabic": ["شیخ الاسلام", "شایخ الاسلام"]
        }
    },
    "HADYA_HOJI": {
        "full_name": "HADYA HOJI SHALDIRAMOQ JOME MASJIDI",
        "patterns": {
            "latin": ["hadya hoji", "hadiya hoji", "shaldiramoq"],
            "cyrillic": ["хадя ходжи", "хадия ходжи", "шалдирамок"],
            "arabic": ["هادیة حاجی", "شلدیرامق"]
        }
    },
    "AFGONBOG": {
        "full_name": "AFGONBOG JOME MASJIDI",
        "patterns": {
            "latin": ["afgonbog", "afg'onbog", "avgonbog"],
            "cyrillic": ["афгонбог", "авғонбог"],
            "arabic": ["افغونبوغ", "افغانبوغ"]
        }
    },
    "SAYYID_AXMADHON": {
        "full_name": "SAYYID AXMADHON HOJI JOME MASJIDI",
        "patterns": {
            "latin": ["sayyid axmadhon", "sayyid ahmad", "axmadhon hoji"],
            "cyrillic": ["саййид ахмадхон", "саййид ахмад", "ахмадхон ходжи"],
            "arabic": ["سید احمدخان", "سید احمد", "احمدخان حاجی"]
        }
    },
    "DEGRIZLIK": {
        "full_name": "DEGRIZLIK JOME MASJIDI",
        "patterns": {
            "latin": ["degrizlik", "deg'rizlik", "degrızlik"],
            "cyrillic": ["дегризлик", "деғризлик"],
            "arabic": ["دگریزلیك", "دغریزلیك"]
        }
    },
    "SHAYXON": {
        "full_name": "SHAYXON JOME MASJIDI",
        "patterns": {
            "latin": ["shayxon", "shayx on", "sheikh on"],
            "cyrillic": ["шайхон", "шайх он"],
            "arabic": ["شیخون", "شیخ اون"]
        }
    },
    "ZINBARDOR": {
        "full_name": "ZINBARDOR JOME MASJIDI",
        "patterns": {
            "latin": ["zinbardor", "zin bardor", "zinbar dor"],
            "cyrillic": ["зинбардор", "зин бардор"],
            "arabic": ["زینبردور", "زین بردور"]
        }
    },
    "ZAYNUL_OBIDIN": {
        "full_name": "ZAYNUL OBIDIN AYRILISH JOME MASJIDI",
        "patterns": {
            "latin": ["zaynul obidin", "zayn ul obidin", "ayrilish"],
            "cyrillic": ["зайнул обидин", "зайн ул обидин", "айрилиш"],
            "arabic": ["زین العابدین", "آیریلیش"]
        }
    },
    "HAZRATI_ABBOS": {
        "full_name": "HAZRATI ABBOS MOLBOZORI JOME MASJIDI",
        "patterns": {
            "latin": ["hazrati abbos", "hazrat abbos", "molbozor"],
            "cyrillic": ["хазрати аббос", "хазрат аббос", "молбозор"],
            "arabic": ["حضرت عباس", "مولبازار"]
        }
    },
    "SAODAT": {
        "full_name": "SAODAT JOME MASJIDI",
        "patterns": {
            "latin": ["saodat", "sa'odat", "saadat"],
            "cyrillic": ["саодат", "саъодат"],
            "arabic": ["سعادت", "صعادت"]
        }
    },
    "TOLABOY": {
        "full_name": "MUHAMMAD SAID XUJA TOLABOY JOME MASJIDI",
        "patterns": {
            "latin": ["tolaboy", "tola boy", "muhammad said", "said xuja"],
            "cyrillic": ["толабой", "тола бой", "мухаммад саид", "саид хужа"],
            "arabic": ["طلابوی", "محمد سعید", "سعید خواجه"]
        }
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

# Namaz vaqtlari pattern - har xil formatda
PRAYER_PATTERNS = {
    "latin": {
        "bomdod": r'(?:bomdod|fajr|subh|sahar)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "peshin": r'(?:peshin|zuhr|zuhur|öyle)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "asr": r'(?:asr|ikindi|digar)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "shom": r'(?:shom|maghrib|mag\'rib|axshom)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "hufton": r'(?:hufton|isha|xufton|kech)\s*[:]\s*(\d{1,2}[:]\d{2})'
    },
    "cyrillic": {
        "bomdod": r'(?:бомдод|фажр|субх|сахар)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "peshin": r'(?:пешин|зухр|зухур|ойле)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "asr": r'(?:аср|икинди|дигар)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "shom": r'(?:шом|магриб|ағриб|ахшом)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "hufton": r'(?:хуфтон|иша|хуфтон|кеч)\s*[:]\s*(\d{1,2}[:]\d{2})'
    },
    "arabic": {
        "bomdod": r'(?:فجر|صبح|سحر)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "peshin": r'(?:ظهر|زهر)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "asr": r'(?:عصر|عشر)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "shom": r'(?:مغرب|مغریب)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "hufton": r'(?:عشاء|عشا|عیشا)\s*[:]\s*(\d{1,2}[:]\d{2})'
    }
}

# Global bot application
bot_app = None

def similarity(a, b):
    """String similarity checker"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_mosque_in_text(text: str, threshold: float = 0.7) -> Optional[str]:
    """Masjid nomini matndan topish - 3 alifbo"""
    text = text.lower().strip()
    best_match = None
    best_score = 0
    
    for mosque_key, mosque_data in MASJIDLAR.items():
        for script_type, patterns in mosque_data["patterns"].items():
            for pattern in patterns:
                score = similarity(text, pattern)
                if score > threshold and score > best_score:
                    best_score = score
                    best_match = mosque_key
                    
                # Barcha vaqtlar
        message += f"🕐 Vaqtlar: {times['Bomdod']} | {times['Peshin']} | {times['Asr']} | {times['Shom']} | {times['Hufton']}\n"
        
        # Map links
        lat, lon = coordinates
        message += f"🗺️ [Google Maps](https://maps.google.com/?q={lat},{lon}) | [Yandex](https://yandex.com/maps/?pt={lon},{lat}&z=18)\n\n"
    
    message += f"⏰ Hozirgi vaqt: {current_time} (Qo'qon vaqti)"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=True
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
            name = MASJIDLAR[masjid_key]["full_name"]
            
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

💡 *Eslatma:* Ma'lumotlar @{CHANNEL_USERNAME} kanalidan real-time yangilanadi!"""
    else:
        message = f"""📍 Bugun uchun barcha namaz vaqtlari o'tdi.
Ertaga Bomdod vaqti bilan davom etadi.

⏰ Hozirgi vaqt: {current_time} (Qo'qon vaqti)"""
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam bolimi"""
    help_text = f"""ℹ️ *YORDAM*

🔄 *REAL-TIME YANGILANISHLAR:*
Bot @{CHANNEL_USERNAME} kanalini doimiy kuzatib turadi va namaz vaqtlarini avtomatik yangilaydi!

*Bot funksiyalari:*
🕐 Barcha vaqtlar - Tanlangan masjidlar namaz vaqtlari
⏰ Eng yaqin vaqt - Keyingi namaz vaqti
📍 3 ta yaqin masjid - Eng yaqin 3 ta masjid (xarita bilan)
🕌 Masjidlar - Barcha masjidlar ro'yxati
⚙️ Sozlamalar - Masjidlarni tanlash

🤖 *KANAL MONITORING:*
• Yangi post kelsa avtomatik tahlil qilinadi
• 3 xil alifbo tanib olinadi (Lotin, Kiril, Arab)
• Rasmlardan OCR orqali matn o'qiladi
• Masjid nomi va vaqtlar avtomatik yangilanadi

🗺️ *XARITA INTEGRATSIYASI:*
• Google Maps
• Yandex Maps
• To'g'ridan-to'g'ri yo'l ko'rsatish

*Vaqt zonasi:* Qo'qon mahalliy vaqti (UTC+5)

*Kanal:* @{CHANNEL_USERNAME}"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

def get_masjid_selection_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Masjidlarni tanlash klaviaturasi"""
    selected = get_user_selected_masjids(user_id)
    keyboard = []
    
    # Masjidlar royxati (2 tadan qatorda)
    masjid_items = list(MASJIDLAR.items())
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

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sozlamalar"""
    user_id = update.effective_user.id
    selected = get_user_selected_masjids(str(user_id))
    
    message = f"""⚙️ *BILDIRISHNOMALAR SOZLAMALARI*

Siz hozirda *{len(selected)} ta masjid* uchun bildirishnoma olasiz.

🔄 *Real-time yangilanishlar:*
@{CHANNEL_USERNAME} kanalidan avtomatik yangilanadi!

Quyida masjidlarni tanlang/bekor qiling:
✅ - Tanlangan 
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
        save_user_masjids(user_id, set(MASJIDLAR.keys()))
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
        mosque_names = [MASJIDLAR[key]["full_name"].replace('JOME MASJIDI', '').strip() for key in selected]
        await query.edit_message_text(
            f"✅ *Sozlamalar saqlandi!*\n\n"
            f"Siz {len(selected)} ta masjid uchun bildirishnoma olasiz:\n"
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
            name = MASJIDLAR[masjid_key]["full_name"]
            
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
    message += f"🔄 Ma'lumotlar @{CHANNEL_USERNAME} dan avtomatik yangilanadi"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_all_masjids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha masjidlar (korish uchun)"""
    message = "🕌 *BARCHA MASJIDLAR ROYXATI:*\n\n"
    
    for i, (key, data) in enumerate(MASJIDLAR.items(), 1):
        message += f"{i}. {data['full_name']}\n"
    
    message += f"\n📊 Jami: {len(MASJIDLAR)} ta masjid"
    message += "\n\n⚙️ *Sozlamalar* orqali kerakli masjidlarni tanlashingiz mumkin."
    message += f"\n🔄 Barcha vaqtlar @{CHANNEL_USERNAME} dan real-time yangilanadi!"
    
    await update.message.reply_text(
        message,
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
        
        # Telegram kanal monitoring'ni background'da ishga tushirish
        asyncio.create_task(start_channel_monitor())
        
        logger.info("✅ Bot ishga tushmoqda...")
        logger.info(f"👀 Kanal monitoring: @{CHANNEL_USERNAME}")
        print("Bot ishga tushdi! ✅")
        print(f"📺 Kanal kuzatilmoqda: @{CHANNEL_USERNAME}")
        print("🔄 Real-time yangilanishlar faol!")
        
        # Background Worker uchun polling ishlatish
        bot_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        print(f"❌ Xatolik: {e}")

if __name__ == '__main__':
    main() Pattern bo'yicha ham tekshirish
                if pattern in text:
                    return mosque_key
    
    return best_match

def extract_prayer_times(text: str) -> Dict[str, str]:
    """Namaz vaqtlarini matndan ajratib olish"""
    prayer_times = {}
    text = text.lower()
    
    # Har 3 alifbo uchun pattern check
    for script_type, patterns in PRAYER_PATTERNS.items():
        for prayer_name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Capitalize qilish
                prayer_key = prayer_name.capitalize()
                if prayer_key == "Peshin":
                    prayer_key = "Peshin"
                elif prayer_key == "Bomdod":
                    prayer_key = "Bomdod"
                elif prayer_key == "Asr":
                    prayer_key = "Asr"
                elif prayer_key == "Shom":
                    prayer_key = "Shom"
                elif prayer_key == "Hufton":
                    prayer_key = "Hufton"
                    
                prayer_times[prayer_key] = matches[0]
    
    return prayer_times

async def process_image_ocr(image_bytes: bytes) -> str:
    """Rasmdan matn olish (OCR)"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # OCR - Uzbek, Russian, Arabic tillarini qo'llab-quvvatlash
        text = pytesseract.image_to_string(
            image, 
            lang='uzb+rus+ara+eng',
            config='--psm 6'
        )
        return text
    except Exception as e:
        logger.error(f"OCR xatolik: {e}")
        return ""

async def update_mosque_data(mosque_key: str, prayer_times: Dict[str, str]):
    """Masjid ma'lumotlarini yangilash"""
    if mosque_key in masjidlar_data:
        # Faqat to'g'ri vaqt formatdagi ma'lumotlarni yangilash
        for prayer, time in prayer_times.items():
            if re.match(r'\d{1,2}:\d{2}', time):
                masjidlar_data[mosque_key][prayer] = time
                
        logger.info(f"✅ {MASJIDLAR[mosque_key]} vaqtlari yangilandi: {prayer_times}")
        
        # Bot foydalanuvchilariga xabar yuborish (opsional)
        if bot_app:
            await notify_users_about_update(mosque_key, prayer_times)

async def notify_users_about_update(mosque_key: str, prayer_times: Dict[str, str]):
    """Foydalanuvchilarga yangilanish haqida xabar"""
    mosque_name = MASJIDLAR[mosque_key]
    message = f"🔄 *VAQT YANGILANDI*\n\n🕌 {mosque_name}\n\n"
    
    for prayer, time in prayer_times.items():
        message += f"🕐 {prayer}: *{time}*\n"
    
    message += f"\n📅 Yangilangan: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    # Bu yerda barcha foydalanuvchilarga yoki faqat shu masjidni tanlaganlarga yuborish mumkin
    # Hozircha log qilamiz
    logger.info(f"📢 Yangilanish xabari: {message}")

# Telethon Client
async def start_channel_monitor():
    """Telegram kanal monitoring"""
    if not API_ID or not API_HASH:
        logger.warning("❌ Telegram API_ID va API_HASH yo'q. Kanal monitoring ishlamaydi!")
        return
    
    try:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
        logger.info("✅ Telegram client ishga tushdi")
        
        @client.on(events.NewMessage(chats=CHANNEL_USERNAME))
        async def handler(event):
            logger.info(f"📥 Yangi xabar: {CHANNEL_USERNAME}")
            
            text_content = ""
            
            # Matn bo'lsa
            if event.message.message:
                text_content = event.message.message
                logger.info(f"📝 Matn: {text_content[:100]}...")
            
            # Rasm bo'lsa
            if hasattr(event.message, 'media') and isinstance(event.message.media, MessageMediaPhoto):
                logger.info("🖼️ Rasm aniqlandi, OCR ishga tushirilmoqda...")
                try:
                    # Rasmni yuklash
                    image_bytes = await client.download_media(event.message, file=bytes)
                    ocr_text = await process_image_ocr(image_bytes)
                    text_content += " " + ocr_text
                    logger.info(f"📝 OCR matn: {ocr_text[:100]}...")
                except Exception as e:
                    logger.error(f"❌ Rasm processing xatolik: {e}")
            
            # Masjid va vaqtlarni topish
            if text_content:
                mosque_key = find_mosque_in_text(text_content)
                if mosque_key:
                    prayer_times = extract_prayer_times(text_content)
                    if prayer_times:
                        await update_mosque_data(mosque_key, prayer_times)
                        logger.info(f"✅ Yangilandi: {mosque_key} - {prayer_times}")
                    else:
                        logger.info(f"⚠️ Masjid topildi ({mosque_key}) lekin vaqtlar topilmadi")
                else:
                    logger.info("⚠️ Masjid nomi topilmadi")
        
        logger.info(f"👀 Kanal monitoring boshlandi: @{CHANNEL_USERNAME}")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Telegram client xatolik: {e}")

# Masjidlar koordinatalari (3 ta yaqin uchun)
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

def get_user_selected_masjids(user_id: str) -> Set[str]:
    """Foydalanuvchi tanlagan masjidlar"""
    return set(user_settings.get(str(user_id), {}).get('selected_masjids', []))

def save_user_masjids(user_id: str, selected_masjids: Set[str]):
    """Foydalanuvchi tanlagan masjidlarni saqlash"""
    user_id_str = str(user_id)
    if user_id_str not in user_settings:
        user_settings[user_id_str] = {}
    user_settings[user_id_str]['selected_masjids'] = list(selected_masjids)

def get_main_keyboard():
    """Asosiy klaviatura"""
    keyboard = [
        ['🕐 Barcha vaqtlar', '⏰ Eng yaqin vaqt'],
        ['🕌 Masjidlar', '📍 3 ta yaqin masjid'],
        ['⚙️ Sozlamalar', 'ℹ️ Yordam']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_location_keyboard():
    """Location so'rash klaviaturasi"""
    keyboard = [
        [KeyboardButton("📍 Joylashuvni yuborish", request_location=True)],
        [KeyboardButton("🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrugi"""
    user_id = update.effective_user.id
    
    # Agar yangi foydalanuvchi bolsa, barcha masjidlarni tanlangan qilib qoyish
    if str(user_id) not in user_settings:
        save_user_masjids(user_id, set(MASJIDLAR.keys()))
    
    welcome_message = """🕌 Assalomu alaykum!

*Qo'qon Masjidlari Namaz Vaqti Botiga xush kelibsiz!*

🔄 *REAL-TIME YANGILANISHLAR:*
Bot @quqonnamozvaqti kanalini kuzatib turadi va namaz vaqtlarini avtomatik yangilaydi!

⚙️ *Sozlamalar* orqali kerakli masjidlarni belgilashingiz mumkin.

📍 *3 ta yaqin masjid* funksiyasi mavjud!

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
        # Simplified approach - don't ask for location, show general nearby
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
        mosque_name = MASJIDLAR[mosque_key]["full_name"]
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
        
        #
