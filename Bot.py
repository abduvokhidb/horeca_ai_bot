#!/usr/bin/env python3
"""
Horeca AI Bot - Production Version
Deploy ready for Render.com
"""

import asyncio
import sqlite3
import os
import json
import random
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8005801479:AAENfmXu1fCX7srHvBxLPhLaKNwydC_r23A")
DATABASE_PATH = os.getenv("DATABASE_PATH", "horeca_bot.db")
PORT = int(os.getenv("PORT", 8000))

# Initialize bot
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Create necessary directories
Path("photos").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# Test employees data
TEST_EMPLOYEES = [
    {"name": "Admin", "phone": "+998900007747", "position": "Admin"},
    {"name": "Akmal Karimov", "phone": "+998901234567", "position": "Barista"},
    {"name": "Dilnoza Rakhimova", "phone": "+998901234568", "position": "Kassir"}, 
    {"name": "Maryam Tosheva", "phone": "+998901234569", "position": "Tozalovchi"},
    {"name": "Jasur Olimov", "phone": "+998901234570", "position": "Servis Manager"},
]

# Database functions
def init_database():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Employees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                position TEXT NOT NULL,
                telegram_id INTEGER UNIQUE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cleaning checks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cleaning_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                photo_path TEXT,
                ai_result TEXT,
                is_approved BOOLEAN DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        # Restaurant info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurant_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                info_key TEXT UNIQUE NOT NULL,
                info_value TEXT NOT NULL,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # AI requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        # Insert test employees
        for emp in TEST_EMPLOYEES:
            cursor.execute("""
                INSERT OR IGNORE INTO employees (name, phone, position)
                VALUES (?, ?, ?)
            """, (emp["name"], emp["phone"], emp["position"]))
        
        # Insert default restaurant info
        default_info = [
            ('name', 'Demo Restoran'),
            ('description', 'Zamonaviy restoran - sifatli xizmat va mazali taomlar'),
            ('working_hours', '09:00 - 23:00'),
            ('contact', '+998900007747'),
        ]
        
        for key, value in default_info:
            cursor.execute("""
                INSERT OR IGNORE INTO restaurant_info (info_key, info_value, updated_by)
                VALUES (?, ?, 'system')
            """, (key, value))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def get_employee_by_telegram(telegram_id):
    """Get employee by Telegram ID"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, phone, position, telegram_id, is_active
            FROM employees 
            WHERE telegram_id = ? AND is_active = 1
        """, (telegram_id,))
        employee = cursor.fetchone()
        conn.close()
        return employee
    except Exception as e:
        print(f"Get employee error: {e}")
        return None

def register_employee_telegram(phone, telegram_id):
    """Register employee's Telegram ID"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees 
            SET telegram_id = ? 
            WHERE phone = ? AND is_active = 1
        """, (telegram_id, phone))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    except Exception as e:
        print(f"Register employee error: {e}")
        return False

def is_admin(telegram_id):
    """Check if user is admin"""
    employee = get_employee_by_telegram(telegram_id)
    return employee and employee[3].lower() == 'admin'

def save_ai_request(employee_id, question, answer):
    """Save AI request to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_requests (employee_id, question, answer)
            VALUES (?, ?, ?)
        """, (employee_id, question, answer))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Save AI request error: {e}")

def save_cleaning_check(employee_id, photo_path, ai_result, is_approved):
    """Save cleaning check result"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cleaning_checks (employee_id, photo_path, ai_result, is_approved)
            VALUES (?, ?, ?, ?)
        """, (employee_id, photo_path, json.dumps(ai_result), is_approved))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Save cleaning check error: {e}")

# AI response system
def get_ai_response(question):
    """Simple AI response system"""
    question_lower = question.lower()
    
    responses = {
        # Coffee related
        'kofe': """☕ KOFE TAYYORLASH:

🎯 Espresso:
• 18-20g maydalangan kofe
• 25-30 soniya ekstraktsiya
• 92-96°C suv harorati
• 9 bar bosim

📏 Nisbatlar:
• 1:2 (kofe:suv) - Espresso
• 1:15-17 - Filter kofe""",

        'latte': """🥛 LATTE RETSEPTI:

🎯 Tarkibi:
• 1 shot espresso (30ml)
• 150ml buglangan sut
• 1cm sut ko'pigi

📋 Tayyorlash:
1. Espresso tayyorlang
2. Sutni 60-65°C gacha isiting
3. Microfoam yarating
4. Latte art qiling""",

        'cappuccino': """☕ CAPPUCCINO:

🎯 Tarkibi:
• 1 shot espresso (30ml)
• 100ml buglangan sut
• Ko'p sut ko'pigi

📋 Tayyorlash:
1. Espresso tayyorlang
2. Dense microfoam yarating
3. 1/3 espresso, 1/3 sut, 1/3 ko'pik
4. Kakao bilan bezatish mumkin""",

        # Customer service
        'mijoz': """🤝 MIJOZLAR BILAN ISHLASH:

✅ Asosiy qoidalar:
• Doimo jilmayib qarshi oling
• Ko'z bilan aloqa o'rnating
• Faol tinglang
• Savollarni sabr bilan javoblang

🎯 Xizmat bosqichlari:
1. Salomlashing (3 soniya ichida)
2. Buyurtmani qabul qilish
3. Taklif berish
4. Rahmat aytish

🚨 Shikoyatlar bilan:
• Tinglang va tushunganingizni ko'rsating
• Kechirim so'rang
• Yechim taklif qiling
• Rahbar bilan bog'laning (kerak bo'lsa)""",

        # Cleaning
        'tozalash': """🧹 TOZALASH QOIDALARI:

⏰ Vaqt jadvali:
• Har 30 daqiqada hojatxona
• Har soatda ish joylari
• Har 2 soatda pollarni supurish
• Kuniga 3 marta chuqur tozalash

🧴 Dezinfeksiya:
• Barcha tegish sirtlari
• Eshiklar va tutqichlar
• Stollar va stullar
• Idish-tovoq

✅ Tekshiruv ro'yxati:
• Axloqsizliklar yo'q
• Sirtlar quruq
• Yaxshi hid
• Tartib-intizom""",

        # General greetings
        'salom': """👋 Salom! Men AI yordamchiman.

🤖 Men sizga quyidagi mavzularda yordam bera olaman:
• ☕ Kofe tayyorlash
• 🤝 Mijozlar bilan muomala
• 🧹 Tozalash qoidalari
• 📋 Ish jarayonlari
• 🍽️ Menyu haqida savollar

💡 Savolingizni oddiy tilda yozing!""",

        'rahmat': """😊 Marhamat!

🎯 Boshqa yordam kerak bo'lsa:
• Savolingizni yozing
• AI Yordam tugmasini bosing
• Yoki menu orqali kerakli bo'limni tanlang

🚀 Muvaffaqiyatli ish faoliyati!""",
    }
    
    # Find best matching response
    for keyword, response in responses.items():
        if keyword in question_lower:
            return response
    
    # Default response
    return """🤖 Savolingizni to'liq tushunmadim.

💡 Quyidagi mavzularda yordam bera olaman:
• "kofe" - kofe tayyorlash haqida
• "latte" - latte retsepti
• "cappuccino" - cappuccino retsepti  
• "mijoz" - mijozlar bilan ishlash
• "tozalash" - tozalash qoidalari

📝 Savolingizni boshqacha so'zlar bilan yozing!"""

async def analyze_bathroom_photo(photo_data):
    """Simulate AI photo analysis"""
    await asyncio.sleep(2)  # Simulate processing time
    
    # Random analysis results for demo
    analysis = {
        'toilet_paper': random.choice([True, False]),
        'soap': random.choice(['full', 'half', 'empty']),
        'toilet': random.choice(['clean', 'dirty', 'very_dirty']),
        'floor': random.choice(['dry', 'wet', 'flooded']),
        'sink': random.choice(['clean', 'dirty']),
        'overall': 'approved',
        'notes': 'AI analysis completed'
    }
    
    # Calculate overall result
    issues = []
    if not analysis['toilet_paper']:
        issues.append("tualet qog'ozi yo'q")
    if analysis['soap'] == 'empty':
        issues.append("sovun tugagan") 
    if analysis['toilet'] in ['dirty', 'very_dirty']:
        issues.append("unitaz iflos")
    if analysis['floor'] in ['wet', 'flooded']:
        issues.append("pol nam")
    if analysis['sink'] == 'dirty':
        issues.append("lavabo iflos")
    
    if issues:
        analysis['overall'] = 'rejected'
        analysis['notes'] = f"Muammolar: {', '.join(issues)}"
    else:
        analysis['overall'] = 'approved'
        analysis['notes'] = "Hammasi tartibda!"
    
    return analysis

# Keyboard builders
def main_menu_keyboard(is_admin_user=False):
    """Main menu keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Hodimlar", callback_data="employees"),
        InlineKeyboardButton(text="🧹 Tozalik", callback_data="cleaning")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Hisobotlar", callback_data="reports"),
        InlineKeyboardButton(text="🤖 AI Yordam", callback_data="ai_help")
    )
    builder.row(
        InlineKeyboardButton(text="🏢 Restoran", callback_data="restaurant"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings")
    )
    
    if is_admin_user:
        builder.row(
            InlineKeyboardButton(text="🛠️ Admin Panel", callback_data="admin")
        )
    
    return builder.as_markup()

def back_to_menu_keyboard():
    """Back to main menu keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    ]])

# Message handlers
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Foydalanuvchi"
    
    employee = get_employee_by_telegram(user_id)
    
    if employee:
        is_admin_user = is_admin(user_id)
        welcome_text = f"""🎉 Salom {employee[1]}!

🏢 Horeca AI Bot'ga xush kelibsiz!
🎯 Lavozim: {employee[3]}
⭐ Status: {'Admin' if is_admin_user else 'Hodim'}

📱 Quyidagi menyudan kerakli bo'limni tanlang:"""
        
        await message.answer(
            welcome_text,
            reply_markup=main_menu_keyboard(is_admin_user)
        )
    else:
        welcome_text = f"""👋 Salom {username}!

🤖 **Horeca AI Bot**ga xush kelibsiz!

📱 Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:

📝 **Namuna:** +998901234567

🎯 **Mavjud test raqamlar:**
👨‍💼 Admin: +998900007747
☕ Barista: +998901234567  
💰 Kassir: +998901234568
🧹 Tozalovchi: +998901234569
🎩 Manager: +998901234570"""
        
        await message.answer(welcome_text)

@dp.message(F.text.regexp(r'\+998\d{9}'))
async def register_phone(message: types.Message):
    """Register phone number"""
    phone = message.text.strip()
    user_id = message.from_user.id
    
    if register_employee_telegram(phone, user_id):
        employee = get_employee_by_telegram(user_id)
        is_admin_user = is_admin(user_id)
        
        success_text = f"""✅ **Tabriklaymiz!** Muvaffaqiyatli ro'yxatdan o'tdingiz!

👤 **Ism:** {employee[1]}
🎯 **Lavozim:** {employee[3]}
⭐ **Status:** {'Admin huquqlari' if is_admin_user else 'Hodim huquqlari'}

🚀 Endi botdan to'liq foydalanishingiz mumkin!"""
        
        await message.answer(
            success_text,
            reply_markup=main_menu_keyboard(is_admin_user)
        )
    else:
        await message.answer("""❌ **Telefon raqam topilmadi!**

🔍 Quyidagilarni tekshiring:
• To'g'ri formatda yozdingizmi? (+998xxxxxxxxx)
• Raqam ro'yxatda bormi?

📞 **Test raqamlar:**
• +998900007747 (Admin)
• +998901234567 (Barista)
• +998901234568 (Kassir)
• +998901234569 (Tozalovchi)
• +998901234570 (Manager)

🆘 Yordam kerak bo'lsa admin bilan bog'laning.""")

# AI text handler
@dp.message(F.text)
async def handle_text_message(message: types.Message):
    """Handle text messages with AI"""
    user_id = message.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await message.answer("❌ Avval ro'yxatdan o'ting! /start buyrug'ini bosing.")
        return
    
    user_question = message.text.strip()
    ai_response = get_ai_response(user_question)
    
    # Save AI request
    save_ai_request(employee[0], user_question, ai_response)
    
    await message.answer(ai_response, reply_markup=back_to_menu_keyboard())

# Callback query handlers
@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_admin_user = is_admin(user_id)
    
    await callback.message.edit_text(
        "🏠 **Bosh Menyu**\n\nKerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(is_admin_user)
    )

@dp.callback_query(F.data == "employees")
async def employees_callback(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Mening Grafigim", callback_data="my_schedule"),
        InlineKeyboardButton(text="📊 Statistikam", callback_data="my_stats")
    )
    builder.row(
        InlineKeyboardButton(text="⏰ Bugungi Ish", callback_data="today_work"),
        InlineKeyboardButton(text="🔔 Eslatmalar", callback_data="notifications")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        "👥 **Hodimlar Bo'limi**\n\nIsh grafigi va statistikalaringizni bu yerda ko'rishingiz mumkin:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "cleaning")
async def cleaning_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    builder = InlineKeyboardBuilder()
    
    # Show bathroom check only for cleaners
    if employee and 'tozalovchi' in employee[3].lower():
        builder.row(
            InlineKeyboardButton(text="📸 Hojatxona Tekshiruvi", callback_data="bathroom_check")
        )
    
    builder.row(
        InlineKeyboardButton(text="📊 Bugungi Tekshiruvlar", callback_data="today_checks"),
        InlineKeyboardButton(text="📈 Statistika", callback_data="cleaning_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        "🧹 **Tozalik Nazorati**\n\nTozalik tekshiruvlari va statistikalar:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "ai_help")
async def ai_help_callback(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="☕ Kofe", callback_data="help_coffee"),
        InlineKeyboardButton(text="🤝 Mijozlar", callback_data="help_customers")
    )
    builder.row(
        InlineKeyboardButton(text="🧹 Tozalash", callback_data="help_cleaning"),
        InlineKeyboardButton(text="📋 Jarayonlar", callback_data="help_processes")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        """🤖 **AI Yordamchi**

Menga savolingizni yozing yoki quyidagi mavzulardan birini tanlang:

💡 **Misol savollar:**
• "Latte qanday tayyorlanadi?"
• "Mijoz shikoyat qilsa nima qilaman?"
• "Hojatxonani qanday tozalash kerak?"

✨ Oddiy tilda so'rang, men tushunaman!""",
        reply_markup=builder.as_markup()
    )

# Photo handler (for cleaning checks)
waiting_for_photo = {}

@dp.callback_query(F.data == "bathroom_check")
async def bathroom_check_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee or 'tozalovchi' not in employee[3].lower():
        await callback.message.edit_text(
            "❌ **Ruxsat yo'q!**\n\nFaqat tozalovchilar hojatxona tekshiruvi qila oladi.",
            reply_markup=back_to_menu_keyboard()
        )
        return
    
    # Check timing (simplified - in real app check 30-minute intervals)
    
    await callback.message.edit_text(
        """📸 **Hojatxona Tekshiruvi**

Hojatxonaning umumiy holatini ko'rsatadigan **aniq rasm** yuboring.

🔍 **Tekshiriladigan narsalar:**
• ✅ Tualet qog'ozi mavjudligi
• 🧴 Suyuq sovun holati
• 🚽 Unitaz tozaligi
• 🪣 Pollar holati (quruq/nam)
• 🧽 Lavabo va peshtaxtalar

⏰ **Vaqt:** 40 daqiqa (10 daqiqa bonus)

📱 Rasmni yuborganingizdan so'ng AI tahlil qiladi.""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚫 Bekor qilish", callback_data="cleaning")
        ]])
    )
    
    waiting_for_photo[user_id] = "bathroom_check"

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    """Handle photo uploads"""
    user_id = message.from_user.id
    
    if user_id not in waiting_for_photo:
        await message.answer("❌ Hozir rasm kutilmayapti.")
        return
    
    employee = get_employee_by_telegram(user_id)
    if not employee:
        await message.answer("❌ Hodim ma'lumotlari topilmadi.")
        return
    
    # Get photo
    photo = message.photo[-1]  # Highest resolution
    
    # Send processing message
    processing_msg = await message.answer("🤖 **AI tahlil qilmoqda...**\n\n⏳ Iltimos, kuting...")
    
    try:
        # Download photo (in real app, save to cloud storage)
        file_info = await bot.get_file(photo.file_id)
        file_data = await bot.download_file(file_info.file_path)
        
        # Analyze with AI
        analysis_result = await analyze_bathroom_photo(file_data.read())
        
        # Save to database
        photo_path = f"photos/{photo.file_id}.jpg"
        is_approved = analysis_result['overall'] == 'approved'
        save_cleaning_check(employee[0], photo_path, analysis_result, is_approved)
        
        # Create result message
        result_text = "🤖 **AI Tahlil Natijasi:**\n\n"
        
        # Analysis details
        result_text += f"{'✅' if analysis_result['toilet_paper'] else '❌'} **Tualet qog'ozi:** {'Bor' if analysis_result['toilet_paper'] else 'Yo\'q'}\n"
        result_text += f"🧴 **Sovun:** {analysis_result['soap']}\n"
        result_text += f"🚽 **Unitaz:** {analysis_result['toilet']}\n"
        result_text += f"🪣 **Pollar:** {analysis_result['floor']}\n"
        result_text += f"🧽 **Lavabo:** {analysis_result['sink']}\n\n"
        
        if is_approved:
            result_text += "✅ **QABUL QILINDI!**\n\n"
            result_text += f"💬 {analysis_result['notes']}\n\n🎉 Ajoyib ish!"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")],
                [InlineKeyboardButton(text="🧹 Tozalik Bo'limi", callback_data="cleaning")]
            ])
        else:
            result_text += "❌ **RAD ETILDI!**\n\n"
            result_text += f"💬 {analysis_result['notes']}\n\n"
            result_text += "🔄 **Iltimos, tozalab qayta rasm yuboring.**"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Qayta Urinish", callback_data="bathroom_check")],
                [InlineKeyboardButton(text="☎️ Boshqaruvchini Chaqirish", callback_data="call_manager")],
                [InlineKeyboardButton(text="🧹 Tozalik Bo'limi", callback_data="cleaning")]
            ])
        
        await processing_msg.edit_text(result_text, reply_markup=keyboard)
        
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ **Xatolik yuz berdi!**\n\n{str(e)}\n\nIltimos, qayta urinib ko'ring.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 Qayta Urinish", callback_data="bathroom_check")
            ]])
        )
    
    finally:
        # Remove from waiting state
        if user_id in waiting_for_photo:
            del waiting_for_photo[user_id]

# Additional callback handlers
@dp.callback_query(F.data == "my_schedule")
async def my_schedule_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await callback.answer("❌ Xatolik!")
        return
    
    today = datetime.now().strftime("%d.%m.%Y")
    schedule_text = f"""📋 **{employee[1]} - Ish Grafigi**

📅 **Bugun:** {today}
🕘 **Smena:** 09:00 - 21:00  
⏰ **Tanaffus:** 13:00 - 14:00
📍 **Lavozim:** {employee[3]}

📊 **Haftalik jadval:**
• Dushanba-Shanba: 09:00-21:00
• Yakshanba: Dam olish kuni

ℹ️ *To'liq grafik tizimi keyingi versiyada qo'shiladi.*"""
    
    await callback.message.edit_text(
        schedule_text,
        reply_markup=back_to_menu_keyboard()
    )

@dp.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await callback.answer("❌ Xatolik!")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)