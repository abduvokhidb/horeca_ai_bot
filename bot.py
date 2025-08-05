# Updated keyboard functions to use current language
def main_menu_keyboard(user_id, is_admin_user=False):
    """Main menu keyboard with role-based access"""
    builder = ReplyKeyboardBuilder()
    
    if is_admin_user:
        # Admin sees all employees data
        builder.row(
            KeyboardButton(text=get_menu_text(user_id, 'menu_employees')),
            KeyboardButton(text=get_menu_text(user_id, 'menu_cleaning'))
        )
    else:
        # Regular employees see personal cabinet
        builder.row(
            KeyboardButton(text=get_menu_text(user_id, 'menu_personal')),
            KeyboardButton(text=get_menu_text(user_id, 'menu_cleaning'))
        )
    
    builder.row(
        KeyboardButton(text=get_menu_text(user_id, 'menu_reports')),
        KeyboardButton(text=get_menu_text(user_id, 'menu_ai_help'))
    )
    builder.row(
        KeyboardButton(text=get_menu_text(user_id, 'menu_restaurant')),
        KeyboardButton(text=get_menu_text(user_id, 'menu_settings'))
    )
    
    if is_admin_user:
        builder.row(
            KeyboardButton(text=get_menu_text(user_id, 'menu_admin'))
        )
    
    return builder.as_markup(resize_keyboard=True)

def back_to_menu_keyboard(user_id):
    """Back to main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=get_menu_text(user_id, 'main_menu')))
    return builder.as_markup(resize_keyboard=True)

def language_selection_keyboard():
    """Language selection keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🇺🇿 O'zbek tili"))
    builder.row(KeyboardButton(text="🇷🇺 Русский язык"))
    builder.row(KeyboardButton(text="🇬🇧 English Language"))
    builder.row(KeyboardButton(text="🔙 Orqaga / Назад / Back"))
    return builder.as_markup(resize_keyboard=True)

def personal_cabinet_keyboard(user_id):
    """Personal cabinet menu keyboard"""
    lang = get_user_language(user_id)
    
    if lang == 'ru':
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="📊 Моя Статистика"),
            KeyboardButton(text="📋 Мои Задачи")
        )
        builder.row(
            KeyboardButton(text="📅 Рабочее Расписание"),
            KeyboardButton(text="⏰ Рабочее Время")
        )
        builder.row(
            KeyboardButton(text="🏆 Рейтинг"),
            KeyboardButton(text="🎯 Цели")
        )
        builder.row(KeyboardButton(text="🏠 Главное Меню"))
    elif lang == 'en':
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="📊 My Statistics"),
            KeyboardButton(text="📋 My Tasks")
        )
        builder.row(
            KeyboardButton(text="📅 Work Schedule"),
            KeyboardButton(text="⏰ Work Time")
        )
        builder.row(
            KeyboardButton(text="🏆 Rating"),
            KeyboardButton(text="🎯 Goals")
        )
        builder.row(KeyboardButton(text="🏠 Main Menu"))
    else:  # uz
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="📊 Mening Statistikam"),
            KeyboardButton(text="📋 Mening Vazifalarim")
        )
        builder.row(
            KeyboardButton(text="📅 Ish Jadvali"),
            KeyboardButton(text="⏰ Ish Vaqti")
        )
        builder.row(
            KeyboardButton(text="🏆 Reyting"),
            KeyboardButton(text="🎯 Maqsadlar")
        )
        builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    
    return builder.as_markup(resize_keyboard=True)

def ai_help_keyboard(user_id):
    """AI help menu keyboard"""
    lang = get_user_language(user_id)
    builder = ReplyKeyboardBuilder()
    
    if lang == 'ru':
        builder.row(
            KeyboardButton(text="☕ Эспрессо"),
            KeyboardButton(text="🥛 Латте")
        )
        builder.row(
            KeyboardButton(text="☕ Капучино"),
            KeyboardButton(text="🫘 Кофейные Зерна")
        )
        builder.row(
            KeyboardButton(text="🥛 Взбивание Молока"),
            KeyboardButton(text="🎨 Латте Арт")
        )
        builder.row(KeyboardButton(text="🏠 Главное Меню"))
    elif lang == 'en':
        builder.row(
            KeyboardButton(text="☕ Espresso"),
            KeyboardButton(text="🥛 Latte")
        )
        builder.row(
            KeyboardButton(text="☕ Cappuccino"),
            KeyboardButton(text="🫘 Coffee Beans")
        )
        builder.row(
            KeyboardButton(text="🥛 Milk Steaming"),
            KeyboardButton(text="🎨 Latte Art")
        )
        builder.row(KeyboardButton(text="🏠 Main Menu"))
    else:  # uz
        builder.row(
            KeyboardButton(text="☕ Espresso"),
            KeyboardButton(text="🥛 Latte")
        )
        builder.row(
            KeyboardButton(text="☕ Cappuccino"),
            KeyboardButton(text="🫘 Kofe Donlari")
        )
        builder.row(
            KeyboardButton(text="🥛 Sut Ishlash"),
            KeyboardButton(text="🎨 Latte Art")
        )
        builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    
    return builder.as_markup(resize_keyboard=True)

def cleaning_keyboard(user_id, is_cleaner=False):
    """Cleaning menu keyboard"""
    lang = get_user_language(user_id) 
    builder = ReplyKeyboardBuilder()
    
    if lang == 'ru':
        if is_cleaner:
            builder.row(KeyboardButton(text="📸 Проверка Туалета"))
        builder.row(
            KeyboardButton(text="📊 Сегодняшние Проверки"),
            KeyboardButton(text="📈 Статистика")
        )
        builder.row(KeyboardButton(text="🏠 Главное Меню"))
    elif lang == 'en':
        if is_cleaner:
            builder.row(KeyboardButton(text="📸 Bathroom Check"))
        builder.row(
            KeyboardButton(text="📊 Today's Checks"),
            KeyboardButton(text="📈 Statistics")
        )
        builder.row(KeyboardButton(text="🏠 Main Menu"))
    else:  # uz
        if is_cleaner:
            builder.row(KeyboardButton(text="📸 Hojatxona Tekshiruvi"))
        builder.row(
            KeyboardButton(text="📊 Bugungi Tekshiruvlar"),
            KeyboardButton(text="📈 Statistika")
        )
        builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    
    return builder.as_markup(resize_keyboard=True)

def reports_keyboard(user_id, is_admin_user=False):
    """Reports menu keyboard"""
    lang = get_user_language(user_id)
    builder = ReplyKeyboardBuilder()
    
    if lang == 'ru':
        if is_admin_user:
            builder.row(
                KeyboardButton(text="📈 Дневной"),
                KeyboardButton(text="📊 Недельный")
            )
            builder.row(
                KeyboardButton(text="📅 Месячный"),
                KeyboardButton(text="👥 Сотрудники")
            )
        else:
            builder.row(
                KeyboardButton(text="📈 Мой Отчет"),
                KeyboardButton(text="📊 Командные Показатели")
            )
        builder.row(KeyboardButton(text="🏠 Главное Меню"))
    elif lang == 'en':
        if is_admin_user:
            builder.row(
                KeyboardButton(text="📈 Daily"),
                KeyboardButton(text="📊 Weekly")
            )
            builder.row(
                KeyboardButton(text="📅 Monthly"),
                KeyboardButton(text="👥 Employees")
            )
        else:
            builder.row(
                KeyboardButton(text="📈 My Report"),
                KeyboardButton(text="📊 Team Overview")
            )
        builder.row(KeyboardButton(text="🏠 Main Menu"))
    else:  # uz
        if is_admin_user:
            builder.row(
                KeyboardButton(text="📈 Kunlik"),
                KeyboardButton(text="📊 Haftalik")
            )
            builder.row(
                KeyboardButton(text="📅 Oylik"),
                KeyboardButton(text="👥 Hodimlar")
            )
        else:
            builder.row(
                KeyboardButton(text="📈 Mening Hisobotim"),
                KeyboardButton(text="📊 Jamoaviy Ko'rsatkichlar")
            )
        builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    
    return builder.as_markup(resize_keyboard=True)

def employees_keyboard(user_id):
    """Employees menu keyboard (Admin only)"""
    lang = get_user_language(user_id)
    builder = ReplyKeyboardBuilder()
    
    if lang == 'ru':
        builder.row(
            KeyboardButton(text="👥 Все Сотрудники"),
            KeyboardButton(text="📊 Общая Статистика")
        )
        builder.row(
            KeyboardButton(text="📋 Рабочие Графики"),
            KeyboardButton(text="🎯 Производительность")
        )
        builder.row(KeyboardButton(text="🏠 Главное Меню"))
    elif lang == 'en':
        builder.row(
            KeyboardButton(text="👥 All Employees"),
            KeyboardButton(text="📊 General Statistics")
        )
        builder.row(
            KeyboardButton(text="📋 Work Schedules"),
            KeyboardButton(text="🎯 Performance")
        )
        builder.row(KeyboardButton(text="🏠 Main Menu"))
    else:  # uz
        builder.row(
            KeyboardButton(text="👥 Barcha Hodimlar"),
            KeyboardButton(text="📊 Umumiy Statistika")
        )
        builder.row(
            KeyboardButton(text="📋 Ish Jadvallari"),
            KeyboardButton(text="🎯 Performance")
        )
        builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    
    return builder.as_markup(resize_keyboard=True)# Photo handler remains the same but updated for regular keyboards
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    """Handle photo uploads with real AI"""
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
    
    # Check API status and show appropriate message
    if AI_ENABLED:
        processing_msg = await message.answer("🤖 **Haqiqiy AI tahlil qilmoqda...**\n\n⏳ Iltimos, kuting...")
    else:
        processing_msg = await message.answer("🤖 **Demo AI tahlil qilmoqda...**\n\n⏳ (Haqiqiy AI uchun OPENAI_API_KEY sozlang)")
    
    try:
        # Download photo
        file_info = await bot.get_file(photo.file_id)
        file_data = await bot.download_file(file_info.file_path)
        photo_bytes = file_data.read()
        
        # AI Analysis
        analysis_result = await analyze_bathroom_photo(photo_bytes)
        
        if not analysis_result:
            await processing_msg.edit_text("❌ Tahlil xatosi! Qayta urinib ko'ring.")
            return
        
        # Save results
        photo_path = f"photos/{photo.file_id}.jpg"
        is_approved = analysis_result['overall'] == 'approved'
        save_cleaning_check(employee[0], photo_path, analysis_result, is_approved)
        
        # Format results
        score = analysis_result.get('score', 0)
        result_text = f"🤖 **AI Tahlil Natijasi:** {score}/100\n\n"
        
        # Details
        result_text += f"{'✅' if analysis_result['toilet_paper'] else '❌'} **Tualet qogozi:** {'Bor' if analysis_result['toilet_paper'] else 'Yo\'q'}\n"
        result_text += f"🧴 **Sovun:** {analysis_result['soap']}\n"
        result_text += f"🚽 **Unitaz:** {analysis_result['toilet']}\n"
        result_text += f"🪣 **Pollar:** {analysis_result['floor']}\n"
        result_text += f"🧽 **Lavabo:** {analysis_result['sink']}\n\n"
        
        if is_approved:
            result_text += f"✅ **QABUL QILINDI!** ({score}/100)\n\n"
            result_text += f"💬 {analysis_result['notes']}\n\n🎉 Ajoyib ish!"
        else:
            result_text += f"❌ **RAD ETILDI!** ({score}/100)\n\n"
            result_text += f"💬 {analysis_result['notes']}\n\n"
            result_text += "🔄 **Iltimos, tozalab qayta rasm yuboring.**"
        
        # Use regular keyboard for response
        await processing_msg.edit_text(result_text)
        await message.answer("Davom etish uchun menyudan tanlang:", reply_markup=back_to_menu_keyboard(user_id))
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Xatolik: {str(e)}")
        await message.answer("Davom etish uchun menyudan tanlang:", reply_markup=back_to_menu_keyboard(user_id))
    
    finally:
        if user_id in waiting_for_photo:
            del waiting_for_photo[user_id]

# Error handler
@dp.error()
async def error_handler(event, exception):
    """Global error handler"""
    print(f"Error occurred: {exception}")
    return True

# Health check endpoint (for Render)
from aiohttp import web
from aiohttp.web import Request, Response

async def health_check(request: Request) -> Response:
    return web.json_response({"status": "healthy", "bot": "running"})

async def setup_webapp():
    """Setup web app for health checks"""
    app = web.Application()
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    return app

# Main function
async def main():
    """Main function to run the bot"""
    try:
        print("🚀 Starting Enhanced Horeca AI Bot with Regular Keyboards...")
        print(f"📱 Python version: {__import__('sys').version}")
        print(f"💾 Database: {DATABASE_PATH}")
        print(f"🤖 AI Status: {'Real AI' if AI_ENABLED else 'Demo Mode'}")
        print(f"🌐 Multi-language: UZ/RU/EN support")
        print(f"👥 Role-based access: Admin vs Employee")
        print(f"⌨️ Interface: Regular Keyboards (more user-friendly)")
        
        # Initialize database
        print("📊 Initializing enhanced database...")
        if not init_database():
            print("❌ Database initialization failed!")
            return
        
        print("✅ Database ready!")
        print("🤖 Enhanced bot starting...")
        print("📱 Features:")
        print("  - Personal Cabinet for employees")
        print("  - Enhanced Coffee AI Assistant")
        print("  - Multi-language support (UZ/RU/EN)")
        print("  - Role-based permissions")
        print("  - Personal tasks and statistics")
        print("  - Regular keyboard interface")
        print("🎯 Admin: +998900007747")
        print("👥 Test users: +998901234567-70")
        print("🌐 Health check: /health")
        print("🛑 Stop with Ctrl+C")
        print("-" * 60)
        
        # Setup web app for health checks
        app = await setup_webapp()
        
        # Start web server for health checks (required by Render)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        print(f"🌐 Web server started on port {PORT}")
        
        # Start bot polling
        await dp.start_polling(bot, skip_updates=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔄 Cleaning up...")
        await bot.session.close()
        print("👋 Goodbye!")

if __name__ == "__main__":
    # Setup logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress some verbose logs
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot terminated")
    except Exception as e:
        print(f"❌ Startup error: {e}")#!/usr/bin/env python3
"""
Enhanced Horeca AI Bot - Role-based & Multi-language
- Role-based access control
- Personal cabinet for employees
- Enhanced AI for coffee/barista topics
- Multi-language support (UZ/RU/EN)
"""

import asyncio
import sqlite3
import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8005801479:AAENfmXu1fCX7srHvBxLPhLaKNwydC_r23A")
DATABASE_PATH = os.getenv("DATABASE_PATH", "horeca_bot.db")
PORT = int(os.getenv("PORT", 8000))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# AI availability check
AI_ENABLED = bool(OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'))

if AI_ENABLED:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        print("🤖 Real AI enabled with OpenAI")
    except ImportError:
        AI_ENABLED = False
        print("⚠️ OpenAI not installed, using demo mode")
else:
    print("🎭 Demo AI mode - add OPENAI_API_KEY for real AI")

# Initialize bot
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Create directories
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

# Language translations
TRANSLATIONS = {
    'uz': {
        'welcome_employee': "🎉 Salom {name}!\n\n🏢 Horeca AI Bot'ga xush kelibsiz!\n🎯 Lavozim: {position}\n⭐ Status: Hodim\n\n📱 Quyidagi menyudan kerakli bo'limni tanlang:",
        'welcome_admin': "🎉 Salom {name}!\n\n🏢 Horeca AI Bot'ga xush kelibsiz!\n🎯 Lavozim: {position}\n⭐ Status: Admin\n\n📱 Quyidagi menyudan kerakli bo'limni tanlang:",
        'welcome_guest': "👋 Salom {username}!\n\n🤖 **Horeca AI Bot**ga xush kelibsiz!\n\n📱 Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:\n\n📝 **Namuna:** +998901234567",
        'menu_personal': "🏠 Shaxsiy Kabinet",
        'menu_employees': "👥 Hodimlar",
        'menu_cleaning': "🧹 Tozalik",
        'menu_reports': "📊 Hisobotlar",
        'menu_ai_help': "🤖 AI Yordam",
        'menu_restaurant': "🏢 Restoran",
        'menu_settings': "⚙️ Sozlamalar",
        'menu_admin': "🛠️ Admin Panel",
        'main_menu': "🏠 Bosh Menyu",
        'language_uzbek': "🇺🇿 O'zbek tili",
        'language_russian': "🇷🇺 Rus tili",
        'language_english': "🇬🇧 English Language",
        'phone_not_found': "❌ **Telefon raqam topilmadi!**\n\n🔍 Quyidagilarni tekshiring:\n• To'g'ri formatda yozdingizmi? (+998xxxxxxxxx)\n• Raqam ro'yxatda bormi?\n\n🆘 Yordam kerak bo'lsa admin bilan bog'laning.",
        'ai_coffee_context': "Siz qahvaxona/kafe uchun professional barista yordamchisiz. Faqat qahva, kofe, ichimliklar, barista skills va qahvaxona operatsiyalari haqida javob bering.",
        'personal_stats': "📈 **{name} - Shaxsiy Statistika**\n\n🧹 **Tozalik Tekshiruvlari:**\n• Jami: {total_checks} ta\n• Qabul qilingan: {approved_checks} ta\n• Muvaffaqiyat: {success_rate:.1f}%\n\n🤖 **AI So'rovlari:** {ai_requests} ta\n\n🎯 **Lavozim:** {position}\n📅 **Faollik:** {current_month}"
    },
    'ru': {
        'welcome_employee': "🎉 Привет {name}!\n\n🏢 Добро пожаловать в Horeca AI Bot!\n🎯 Должность: {position}\n⭐ Статус: Сотрудник\n\n📱 Выберите нужный раздел из меню:",
        'welcome_admin': "🎉 Привет {name}!\n\n🏢 Добро пожаловать в Horeca AI Bot!\n🎯 Должность: {position}\n⭐ Статус: Админ\n\n📱 Выберите нужный раздел из меню:",
        'welcome_guest': "👋 Привет {username}!\n\n🤖 **Добро пожаловать в Horeca AI Bot**!\n\n📱 Для регистрации отправьте ваш номер телефона:\n\n📝 **Пример:** +998901234567",
        'menu_personal': "🏠 Личный Кабинет",
        'menu_employees': "👥 Сотрудники",
        'menu_cleaning': "🧹 Уборка",
        'menu_reports': "📊 Отчеты",
        'menu_ai_help': "🤖 AI Помощь",
        'menu_restaurant': "🏢 Ресторан",
        'menu_settings': "⚙️ Настройки",
        'menu_admin': "🛠️ Админ Панель",
        'main_menu': "🏠 Главное Меню",
        'language_uzbek': "🇺🇿 Узбекский язык",
        'language_russian': "🇷🇺 Русский язык",
        'language_english': "🇬🇧 English Language",
        'phone_not_found': "❌ **Номер телефона не найден!**\n\n🔍 Проверьте:\n• Правильный ли формат? (+998xxxxxxxxx)\n• Есть ли номер в списке?\n\n🆘 Если нужна помощь, свяжитесь с админом.",
        'ai_coffee_context': "Вы профессиональный помощник бариста для кофейни/кафе. Отвечайте только на вопросы о кофе, напитках, навыках бариста и операциях кофейни.",
        'personal_stats': "📈 **{name} - Личная Статистика**\n\n🧹 **Проверки Уборки:**\n• Всего: {total_checks} шт\n• Принято: {approved_checks} шт\n• Успешность: {success_rate:.1f}%\n\n🤖 **AI Запросы:** {ai_requests} шт\n\n🎯 **Должность:** {position}\n📅 **Активность:** {current_month}"
    },
    'en': {
        'welcome_employee': "🎉 Hello {name}!\n\n🏢 Welcome to Horeca AI Bot!\n🎯 Position: {position}\n⭐ Status: Employee\n\n📱 Please select the required section from the menu:",
        'welcome_admin': "🎉 Hello {name}!\n\n🏢 Welcome to Horeca AI Bot!\n🎯 Position: {position}\n⭐ Status: Admin\n\n📱 Please select the required section from the menu:",
        'welcome_guest': "👋 Hello {username}!\n\n🤖 **Welcome to Horeca AI Bot**!\n\n📱 To register, please send your phone number:\n\n📝 **Example:** +998901234567",
        'menu_personal': "🏠 Personal Cabinet",
        'menu_employees': "👥 Employees",
        'menu_cleaning': "🧹 Cleaning",
        'menu_reports': "📊 Reports",
        'menu_ai_help': "🤖 AI Help",
        'menu_restaurant': "🏢 Restaurant",
        'menu_settings': "⚙️ Settings",
        'menu_admin': "🛠️ Admin Panel",
        'main_menu': "🏠 Main Menu",
        'language_uzbek': "🇺🇿 Uzbek Language",
        'language_russian': "🇷🇺 Russian Language",
        'language_english': "🇬🇧 English Language",
        'phone_not_found': "❌ **Phone number not found!**\n\n🔍 Please check:\n• Correct format? (+998xxxxxxxxx)\n• Is the number registered?\n\n🆘 If you need help, contact admin.",
        'ai_coffee_context': "You are a professional barista assistant for coffee shops/cafes. Only answer questions about coffee, drinks, barista skills, and coffee shop operations.",
        'personal_stats': "📈 **{name} - Personal Statistics**\n\n🧹 **Cleaning Checks:**\n• Total: {total_checks} items\n• Approved: {approved_checks} items\n• Success Rate: {success_rate:.1f}%\n\n🤖 **AI Requests:** {ai_requests} items\n\n🎯 **Position:** {position}\n📅 **Activity:** {current_month}"
    }
}

# User language storage (in real app, store in database)
user_languages = {}

def get_user_language(user_id):
    """Get user's preferred language"""
    return user_languages.get(user_id, 'uz')  # Default to Uzbek

def set_user_language(user_id, language):
    """Set user's preferred language"""
    user_languages[user_id] = language

def _(user_id, key, **kwargs):
    """Get translated text"""
    lang = get_user_language(user_id)
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

# Coffee keywords for AI response filtering
coffee_keywords = [
    'latte', 'cappuccino', 'espresso', 'kofe', 'coffee', 'sut', 'milk',
    'bean', 'don', 'steam', 'bug', 'art', 'foam', 'barista', 'grind',
    'extraction', 'shot', 'crema', 'roast', 'arabica', 'robusta',
    'origin', 'blend', 'pour', 'tamping', 'dosing'
]

def get_coffee_response(question_lower, responses):
    """Get coffee-related response"""
    is_coffee_related = any(keyword in question_lower for keyword in coffee_keywords)
    if not is_coffee_related:
        return responses['not_coffee']

    for keyword, response in responses.items():
        if keyword in question_lower and keyword != 'not_coffee':
            return response

    return responses.get('espresso', responses['not_coffee'])

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
                language TEXT DEFAULT 'uz',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Personal tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                task_title TEXT NOT NULL,
                task_description TEXT,
                is_completed BOOLEAN DEFAULT 0,
                due_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        # Work schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                work_date DATE,
                start_time TIME,
                end_time TIME,
                break_start TIME DEFAULT '13:00',
                break_end TIME DEFAULT '14:00',
                is_day_off BOOLEAN DEFAULT 0,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
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
        
        # Insert sample personal tasks for barista
        barista_tasks = [
            ("Espresso mashinasini tozalash", "Har kuni oxirida espresso mashinasini to'liq tozalash", False),
            ("Kofe don inventarizatsiyasi", "Kofe donlari zaxirasini tekshirish va hisobot", False),
            ("Latte art o'rganish", "Yangi latte art texnikalarini o'rganish", False),
        ]
        
        for task_title, task_desc, is_completed in barista_tasks:
            cursor.execute("""
                INSERT OR IGNORE INTO personal_tasks (employee_id, task_title, task_description, is_completed, due_date)
                SELECT id, ?, ?, ?, datetime('now', '+7 days')
                FROM employees WHERE position = 'Barista' AND name = 'Akmal Karimov'
            """, (task_title, task_desc, is_completed))
        
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
            SELECT id, name, phone, position, telegram_id, is_active, language
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

def get_personal_stats(employee_id):
    """Get personal statistics for employee"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get cleaning checks stats
        cursor.execute("""
            SELECT COUNT(*) FROM cleaning_checks 
            WHERE employee_id = ?
        """, (employee_id,))
        total_checks = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM cleaning_checks 
            WHERE employee_id = ? AND is_approved = 1
        """, (employee_id,))
        approved_checks = cursor.fetchone()[0]
        
        # Get AI requests stats
        cursor.execute("""
            SELECT COUNT(*) FROM ai_requests 
            WHERE employee_id = ?
        """, (employee_id,))
        ai_requests = cursor.fetchone()[0]
        
        # Get pending tasks
        cursor.execute("""
            SELECT COUNT(*) FROM personal_tasks 
            WHERE employee_id = ? AND is_completed = 0
        """, (employee_id,))
        pending_tasks = cursor.fetchone()[0]
        
        conn.close()
        
        success_rate = (approved_checks / total_checks * 100) if total_checks > 0 else 0
        
        return {
            'total_checks': total_checks,
            'approved_checks': approved_checks,
            'ai_requests': ai_requests,
            'pending_tasks': pending_tasks,
            'success_rate': success_rate
        }
        
    except Exception as e:
        print(f"Get personal stats error: {e}")
        return None

def get_personal_tasks(employee_id):
    """Get personal tasks for employee"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT task_title, task_description, is_completed, due_date
            FROM personal_tasks 
            WHERE employee_id = ?
            ORDER BY is_completed ASC, due_date ASC
            LIMIT 10
        """, (employee_id,))
        
        tasks = cursor.fetchall()
        conn.close()
        return tasks
        
    except Exception as e:
        print(f"Get personal tasks error: {e}")
        return []

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

# Update all menu text functions to be language-aware
def get_menu_text(user_id, key, **kwargs):
    """Get menu text in user's language"""
    return _(user_id, key, **kwargs)

# Enhanced AI system for coffee/barista topics - IMPROVED
async def get_enhanced_coffee_ai_response(question, employee_context=None, user_id=None):
    """Enhanced AI response focused on coffee/barista topics - ALWAYS tries real AI first"""
    
    # ALWAYS try real AI first, even if API key might be missing
    try:
        if OPENAI_API_KEY:  # Check if key exists, even if not properly formatted
            print("🤖 Attempting real AI response...")
            
            lang = get_user_language(user_id) if user_id else 'uz'
            context_lang = {
                'uz': "O'zbek tilida",
                'ru': "на русском языке", 
                'en': "in English"
            }.get(lang, "O'zbek tilinda")
            
            # Enhanced context for more dynamic responses
            context = f"""Siz professional qahvaxona/kafe uchun barista yordamchisiz. {context_lang} javob bering.

Hodim ma'lumotlari:
- Ism: {employee_context.get('name', 'Noma\'lum') if employee_context else 'Noma\'lum'}
- Lavozim: {employee_context.get('position', 'Noma\'lum') if employee_context else 'Noma\'lum'}

Savol: "{question}"

MUHIM QOIDALAR:
1. Har bir savolga INDIVIDUAL va UNIQUE javob bering
2. Savolning mohiyatini tushunib, to'g'ridan-to'g'ri javob bering
3. Shablon javoblardan qoching, har safar yangi yondashuv ishlating
4. Agar savol umumiy bo'lsa (masalan "kofe haqida gapirib be"), keng qamrovli ma'lumot bering
5. Agar savol aniq bo'lsa, aniq javob bering

FAQAT quyidagi mavzularda yordam bering:
- ☕ Kofe turlari va tayyorlash usullari 
- 🥛 Sut ishlash texnikalari
- 🎨 Latte art va bezatish usullari
- ⚙️ Espresso mashinasi va jihozlar
- 📏 Kofe nisbatlari va retseptlar
- 🌡️ Harorat va vaqt parametrlari
- 🫘 Kofe donlari haqida ma'lumot
- 🧹 Qahvaxona jihozlarini tozalash
- 👥 Mijozlar bilan muloqot
- 📊 Qahvaxona operatsiyalari

Javoblaringiz:
- Savolga mos va individual bo'lsin
- Professional va amaliy bo'lsin  
- Emoji ishlatib do'stona bo'ling
- 2-4 paragraf uzunlikda bo'lsin
- Har gal BOSHQACHA yondashuv ishlating"""
            
            # Try to import and use OpenAI
            import openai
            openai.api_key = OPENAI_API_KEY
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": question}
                ],
                max_tokens=700,
                temperature=0.8,  # Higher temperature for more varied responses
                presence_penalty=0.3,  # Encourage new topics
                frequency_penalty=0.3   # Reduce repetition
            )
            
            result = response.choices[0].message.content
            print("✅ Real AI response generated successfully!")
            return result
            
    except Exception as e:
        print(f"❌ Real AI failed: {e}")
        print("🔄 Using enhanced static responses...")
    
    # Enhanced fallback with better logic
    return get_enhanced_static_coffee_response(question, user_id)

def get_enhanced_static_coffee_response(question, user_id=None):
    """Enhanced static responses for coffee topics with dynamic matching"""
    question_lower = question.lower()
    lang = get_user_language(user_id) if user_id else 'uz'
    
    coffee_responses = {
        'uz': {
            'latte': """🥛 **LATTE PROFESSIONAL RETSEPTI**

☕ **Tarkibi:**
• 1-2 shot espresso (30-60ml)
• 150-180ml buglangan sut
• 1cm sut ko'pigi

📋 **Professional tayyorlash:**
1. **Espresso:** 18-20g kofe, 25-30 soniya ekstraktsiya
2. **Sut:** 60-65°C gacha bug'lang (thermometer ishlatamiz)
3. **Microfoam:** Glossy, paint-like texture
4. **Quyish:** Steady stream, 3-4cm balandlikdan
5. **Latte Art:** Heart yoki tulip pattern

💡 **Pro tips:**
• Fresh sut ishlatamiz (2-3 kun ichida)
• Steam wand har safar tozalanadi
• Sut ikki marta bug'lanmaydi
• Perfect microfoam uchun: swirl + tap technique""",

            'cappuccino': """☕ **CAPPUCCINO MASTERCLASS**

🎯 **Classic nisbat:**
• 1 shot espresso (30ml)
• 60ml buglangan sut
• 60ml sut ko'pigi (dense foam)

⚡ **Tayyorlash texnikasi:**
1. **Espresso:** Double shot, 25-30 sek
2. **Foam creation:** Dense, velvety microfoam
3. **Temperature:** 65-70°C (lip-burning hot)
4. **Texture:** Thick, creamy consistency
5. **Presentation:** Ko'pik ustiga cocoa powder

🎨 **Italian style vs Modern:**
• **Traditional:** Ko'proq foam, kam sut
• **Modern:** Latte art bilan, microfoam focus
• **Wet vs Dry:** Mijoz preferensiyasiga qarab""",

            'espresso': """⚡ **PERFECT ESPRESSO GUIDE**

📊 **Golden parameters:**
• **Kofe:** 18-20g (double shot)
• **Vaqt:** 25-30 soniya
• **Hajm:** 36-40ml output
• **Bosim:** 9 bar
• **Harorat:** 92-96°C

🔧 **Texnika:**
1. **Grind:** Fine, hali powder emas
2. **Dose:** Scales bilan aniq o'lchang
3. **Distribution:** WDT yoki finger leveling
4. **Tamping:** 15-20kg bosim, level surface
5. **Timing:** Extraction vaqtini kuzating

❌ **Xatolar va yechimlar:**
• **Sour/Under:** Grind finer, vaqt uzaytiring
• **Bitter/Over:** Grind coarser, vaqt qisqartiring
• **Channeling:** Distribution yaxshilang""",

            'milk_steaming': """🥛 **PROFESSIONAL MILK STEAMING**

🌡️ **Temperature zones:**
• **Start:** Room temperature (4-6°C)
• **Finish:** 60-65°C (hand test: 3 soniya ushlab turolasiz)
• **Limit:** 70°C dan oshmang (protein buziladi)

🎯 **Steaming technique:**
1. **Position:** Steam wand surface yaqinida
2. **Stretching phase:** 0-5 soniya, havo qo'shamiz
3. **Heating phase:** 5-30 soniya, chuqurroq tiqish
4. **Texture:** Glossy, paint-like consistency

💡 **Pro secrets:**
• **Wand angle:** 15-30 daraja
• **Jug size:** Sut hajmidan 2 barobar katta
• **Swirling:** Steam tugagach darhol aylantiring
• **Tap technique:** Bubbles integration uchun""",

            'coffee_beans': """🫘 **KOFE DONLARI HAQIDA**

🌍 **Origin characteristics:**
• **Ethiopia:** Floral, fruity notes
• **Colombia:** Balanced, nutty-chocolate
• **Brazil:** Nutty, low acidity
• **Guatemala:** Full body, spicy notes

🔥 **Roast levels:**
• **Light:** Bright, acidic, origin flavors
• **Medium:** Balanced, caramelized notes
• **Dark:** Bold, bitter, less origin character

📅 **Freshness rules:**
• **Optimal:** 7-21 kun roast qilinganidan keyin
• **Grind:** Ishlatishdan 30 daqiqa oldin
• **Storage:** Cool, dry place, airtight container
• **Avoid:** Freezer, direct sunlight, moisture""",

            'general_coffee': """☕ **KOFE TAYYORLASH ASOSLARI**

🎯 **Eng muhim faktorlar:**
1. **Sifatli don:** Fresh roasted (2-4 hafta ichida)
2. **To'g'ri tortish:** Har ichimlik uchun o'z usuli
3. **Suv sifati:** Toza, mineral balansli suv
4. **Harorat nazorati:** Har bosqichda aniq harorat
5. **Vaqt nazorati:** Ekstraktsiya vaqtini kuzatish

💡 **Professional maslahatlar:**
• Kofe donlarini sovuq, quruq joyda saqlang
• Har kuni dozani aniq o'lchang (scales ishlatamiz)
• Jihozlarni muntazam tozalang
• Har xil kofe turlari bilan tajriba o'tkazing
• Mijozlar ta'mini o'rganing va eslab qoling

🏆 **Muvaffaqiyat kaliti:** Izchillik va amaliyot!""",

            'coffee_quality': """🌟 **SIFATLI KOFE TAYYORLASH**

🔍 **Sifat mezonlari:**
• **Ta'm balansi:** Achchiq, nordon, shirin uyg'unlik
• **Aroma:** Boy va jozibali hid
• **Tuzilish:** Smooth, creamy texture
• **Aftertas te:** Yoqimli ta'm qoldiq

⚙️ **Sifatni ta'minlash:**
1. **Toza jihozlar:** Har kuni tozalash
2. **Fresh ingredients:** Yangi kofe va sut
3. **Consistent technique:** Bir xil usul
4. **Tasting notes:** Ta'mini tahlil qilish
5. **Customer feedback:** Mijoz fikri

📈 **Sifatni oshirish yo'llari:**
• Turli kofe navlarini sinash
• Barista kurslarga borish  
• Yangi texnikalarni o'rganish
• Hamkasblar bilan tajriba almashish""",

            'not_coffee': "❌ Kechirasiz, men faqat qahvaxona va kofe mavzularida yordam bera olaman. ☕\n\nQuyidagi mavzularda savol bering:\n• Kofe tayyorlash usullari\n• Latte art texnikalari\n• Espresso sozlamalari\n• Sut ishlash\n• Qahvaxona jihozlari\n\nQahva bilan bog'liq savolingiz bormi? 😊"
        },
        'ru': {
            'latte': """🥛 **ПРОФЕССИОНАЛЬНЫЙ РЕЦЕПТ ЛАТТЕ**

☕ **Состав:**
• 1-2 шота эспрессо (30-60мл)
• 150-180мл взбитое молоко
• 1см молочная пена

📋 **Профессиональное приготовление:**
1. **Эспрессо:** 18-20г кофе, 25-30 сек экстракция
2. **Молоко:** Взбиваем до 60-65°C (используем термометр)
3. **Микропена:** Глянцевая, краскообразная текстура
4. **Вливание:** Равномерная струя, с высоты 3-4см
5. **Латте-арт:** Сердце или тюльпан

💡 **Профессиональные советы:**
• Используем свежее молоко (2-3 дня)
• Очищаем паровую трубку после каждого использования
• Молоко не взбиваем дважды
• Для идеальной микропены: техника swirl + tap""",

            'cappuccino': """☕ **МАСТЕР-КЛАСС КАПУЧИНО**

🎯 **Классические пропорции:**
• 1 шот эспрессо (30мл)
• 60мл взбитое молоко
• 60мл молочная пена (плотная)

⚡ **Техника приготовления:**
1. **Эспрессо:** Двойной шот, 25-30 сек
2. **Создание пены:** Плотная, бархатистая микропена
3. **Температура:** 65-70°C (горячая для губ)
4. **Текстура:** Густая, кремовая консистенция
5. **Подача:** Какао-порошок на пену

🎨 **Итальянский vs Современный стиль:**
• **Традиционный:** Больше пены, меньше молока
• **Современный:** С латте-артом, фокус на микропену
• **Wet vs Dry:** По предпочтениям клиента""",

            'espresso': """⚡ **РУКОВОДСТВО ПО ИДЕАЛЬНОМУ ЭСПРЕССО**

📊 **Золотые параметры:**
• **Кофе:** 18-20г (двойной шот)
• **Время:** 25-30 секунд
• **Объем:** 36-40мл на выходе
• **Давление:** 9 бар
• **Температура:** 92-96°C

🔧 **Техника:**
1. **Помол:** Мелкий, но не порошок
2. **Дозировка:** Точно взвешиваем на весах
3. **Распределение:** WDT или finger leveling
4. **Темпинг:** Давление 15-20кг, ровная поверхность
5. **Тайминг:** Следим за временем экстракции

❌ **Ошибки и решения:**
• **Кислый/Недо:** Мельче помол, увеличить время
• **Горький/Пере:** Крупнее помол, уменьшить время
• **Каналинг:** Улучшить распределение""",

            'not_coffee': "❌ Извините, я могу помочь только по темам кофейни и кофе. ☕\n\nЗадавайте вопросы по темам:\n• Способы приготовления кофе\n• Техники латте-арт\n• Настройки эспрессо\n• Работа с молоком\n• Оборудование кофейни\n\nЕсть вопросы по кофе? 😊"
        },
        'en': {
            'latte': """🥛 **PROFESSIONAL LATTE RECIPE**

☕ **Components:**
• 1-2 shots espresso (30-60ml)
• 150-180ml steamed milk
• 1cm milk foam

📋 **Professional preparation:**
1. **Espresso:** 18-20g coffee, 25-30 sec extraction
2. **Milk:** Steam to 60-65°C (use thermometer)
3. **Microfoam:** Glossy, paint-like texture
4. **Pouring:** Steady stream, 3-4cm height
5. **Latte Art:** Heart or tulip pattern

💡 **Pro tips:**
• Use fresh milk (2-3 days old)
• Clean steam wand after each use
• Never steam milk twice
• Perfect microfoam technique: swirl + tap""",

            'not_coffee': "❌ Sorry, I can only help with coffee shop and coffee topics. ☕\n\nAsk questions about:\n• Coffee brewing methods\n• Latte art techniques\n• Espresso settings\n• Milk steaming\n• Coffee shop equipment\n\nAny coffee-related questions? 😊"
        }
    }
    
    responses = coffee_responses.get(lang, coffee_responses['uz'])
    
    # DYNAMIC QUESTION MATCHING - more intelligent than before
    # Check for specific keywords and topics
    if any(word in question_lower for word in ['latte', 'латте']):
        return responses.get('latte', responses['general_coffee'])
    elif any(word in question_lower for word in ['cappuccino', 'капучино']):
        return responses.get('cappuccino', responses['general_coffee'])
    elif any(word in question_lower for word in ['espresso', 'эспрессо']):
        return responses.get('espresso', responses['general_coffee'])
    elif any(word in question_lower for word in ['sut', 'milk', 'молоко', 'steam', 'bug']):
        return responses.get('milk_steaming', responses['general_coffee'])
    elif any(word in question_lower for word in ['don', 'bean', 'зерно', 'beans']):
        return responses.get('coffee_beans', responses['general_coffee'])
    elif any(word in question_lower for word in ['art', 'арт', 'bezash', 'украшение']):
        return responses.get('milk_steaming', responses['general_coffee'])
    
    # General coffee questions
    elif any(word in question_lower for word in ['kofe', 'coffee', 'кофе', 'tayyorlash', 'приготовление', 'brewing', 'qanday', 'как', 'how']):
        return responses.get('general_coffee', responses['espresso'])
    elif any(word in question_lower for word in ['sifat', 'quality', 'качество', 'yaxshi', 'хороший', 'good', 'mazali', 'вкусный', 'tasty']):
        return responses.get('coffee_quality', responses['general_coffee'])
    
    # If no coffee keywords found
    elif not any(keyword in question_lower for keyword in coffee_keywords):
        return responses['not_coffee']
    
    # Default fallback
    return responses.get('general_coffee', responses['espresso'])

# Keyboard builders with role-based access - REGULAR KEYBOARDS
def main_menu_keyboard(user_id, is_admin_user=False):
    """Main menu keyboard with role-based access"""
    builder = ReplyKeyboardBuilder()
    
    if is_admin_user:
        # Admin sees all employees data
        builder.row(
            KeyboardButton(text=_(user_id, 'menu_employees')),
            KeyboardButton(text=_(user_id, 'menu_cleaning'))
        )
    else:
        # Regular employees see personal cabinet
        builder.row(
            KeyboardButton(text=_(user_id, 'menu_personal')),
            KeyboardButton(text=_(user_id, 'menu_cleaning'))
        )
    
    builder.row(
        KeyboardButton(text=_(user_id, 'menu_reports')),
        KeyboardButton(text=_(user_id, 'menu_ai_help'))
    )
    builder.row(
        KeyboardButton(text=_(user_id, 'menu_restaurant')),
        KeyboardButton(text=_(user_id, 'menu_settings'))
    )
    
    if is_admin_user:
        builder.row(
            KeyboardButton(text=_(user_id, 'menu_admin'))
        )
    
    return builder.as_markup(resize_keyboard=True)

def back_to_menu_keyboard(user_id):
    """Back to main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=_(user_id, 'main_menu')))
    return builder.as_markup(resize_keyboard=True)

def language_selection_keyboard():
    """Language selection keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🇺🇿 O'zbek tili"))
    builder.row(KeyboardButton(text="🇷🇺 Русский язык"))
    builder.row(KeyboardButton(text="🇬🇧 English Language"))
    builder.row(KeyboardButton(text="🔙 Orqaga / Назад / Back"))
    return builder.as_markup(resize_keyboard=True)

def personal_cabinet_keyboard(user_id):
    """Personal cabinet menu keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📊 Mening Statistikam"),
        KeyboardButton(text="📋 Mening Vazifalarim")
    )
    builder.row(
        KeyboardButton(text="📅 Ish Jadvali"),
        KeyboardButton(text="⏰ Ish Vaqti")
    )
    builder.row(
        KeyboardButton(text="🏆 Reyting"),
        KeyboardButton(text="🎯 Maqsadlar")
    )
    builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    return builder.as_markup(resize_keyboard=True)

def ai_help_keyboard(user_id):
    """AI help menu keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="☕ Espresso"),
        KeyboardButton(text="🥛 Latte")
    )
    builder.row(
        KeyboardButton(text="☕ Cappuccino"),
        KeyboardButton(text="🫘 Kofe Donlari")
    )
    builder.row(
        KeyboardButton(text="🥛 Sut Ishlash"),
        KeyboardButton(text="🎨 Latte Art")
    )
    builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    return builder.as_markup(resize_keyboard=True)

def cleaning_keyboard(user_id, is_cleaner=False):
    """Cleaning menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    if is_cleaner:
        builder.row(KeyboardButton(text="📸 Hojatxona Tekshiruvi"))
    
    builder.row(
        KeyboardButton(text="📊 Bugungi Tekshiruvlar"),
        KeyboardButton(text="📈 Statistika")
    )
    builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    return builder.as_markup(resize_keyboard=True)

def reports_keyboard(user_id, is_admin_user=False):
    """Reports menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    if is_admin_user:
        builder.row(
            KeyboardButton(text="📈 Kunlik"),
            KeyboardButton(text="📊 Haftalik")
        )
        builder.row(
            KeyboardButton(text="📅 Oylik"),
            KeyboardButton(text="👥 Hodimlar")
        )
    else:
        builder.row(
            KeyboardButton(text="📈 Mening Hisobotim"),
            KeyboardButton(text="📊 Jamoaviy Ko'rsatkichlar")
        )
    
    builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    return builder.as_markup(resize_keyboard=True)

def employees_keyboard(user_id):
    """Employees menu keyboard (Admin only)"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="👥 Barcha Hodimlar"),
        KeyboardButton(text="📊 Umumiy Statistika")
    )
    builder.row(
        KeyboardButton(text="📋 Ish Jadvallari"),
        KeyboardButton(text="🎯 Performance")
    )
    builder.row(KeyboardButton(text="🏠 Bosh Menyu"))
    return builder.as_markup(resize_keyboard=True)

# Message handlers
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Foydalanuvchi"
    
    employee = get_employee_by_telegram(user_id)
    
    if employee:
        # Set user language from database
        if employee[6]:  # language field
            set_user_language(user_id, employee[6])
        
        is_admin_user = is_admin(user_id)
        
        if is_admin_user:
            welcome_text = _(user_id, 'welcome_admin', name=employee[1], position=employee[3])
        else:
            welcome_text = _(user_id, 'welcome_employee', name=employee[1], position=employee[3])
        
        await message.answer(
            welcome_text,
            reply_markup=main_menu_keyboard(user_id, is_admin_user)
        )
    else:
        welcome_text = _(user_id, 'welcome_guest', username=username)
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
            reply_markup=main_menu_keyboard(user_id, is_admin_user)
        )
    else:
        await message.answer(_(user_id, 'phone_not_found'))

# Enhanced AI text handler - UPDATED for multilingual support
@dp.message(F.text)
async def handle_text_message(message: types.Message):
    """Handle text messages with enhanced coffee AI and menu navigation"""
    user_id = message.from_user.id
    employee = get_employee_by_telegram(user_id)
    text = message.text.strip()
    
    if not employee:
        await message.answer("❌ Avval ro'yxatdan o'ting! /start buyrug'ini bosing.")
        return
    
    # Skip phone registration
    if text.startswith('+998'):
        return
    
    is_admin_user = is_admin(user_id)
    lang = get_user_language(user_id)
    
    # Handle menu navigation with multilingual support
    menu_handlers = {
        # Personal Cabinet - all languages
        **{key: personal_cabinet_handler for key in [
            get_menu_text(user_id, 'menu_personal'), "🏠 Shaxsiy Kabinet", 
            "🏠 Личный Кабинет", "🏠 Personal Cabinet"
        ]},
        
        # Employees - Admin only, all languages  
        **{key: employees_handler for key in [
            get_menu_text(user_id, 'menu_employees'), "👥 Hodimlar",
            "👥 Сотрудники", "👥 Employees"
        ] if is_admin_user},
        
        # Cleaning - all languages
        **{key: cleaning_handler for key in [
            get_menu_text(user_id, 'menu_cleaning'), "🧹 Tozalik",
            "🧹 Уборка", "🧹 Cleaning"
        ]},
        
        # Reports - all languages
        **{key: reports_handler for key in [
            get_menu_text(user_id, 'menu_reports'), "📊 Hisobotlar",
            "📊 Отчеты", "📊 Reports"
        ]},
        
        # AI Help - all languages
        **{key: ai_help_handler for key in [
            get_menu_text(user_id, 'menu_ai_help'), "🤖 AI Yordam",
            "🤖 AI Помощь", "🤖 AI Help"
        ]},
        
        # Restaurant - all languages
        **{key: restaurant_handler for key in [
            get_menu_text(user_id, 'menu_restaurant'), "🏢 Restoran",
            "🏢 Ресторан", "🏢 Restaurant"
        ]},
        
        # Settings - all languages
        **{key: settings_handler for key in [
            get_menu_text(user_id, 'menu_settings'), "⚙️ Sozlamalar",
            "⚙️ Настройки", "⚙️ Settings"
        ]},
        
        # Main Menu - all languages
        **{key: main_menu_handler for key in [
            get_menu_text(user_id, 'main_menu'), "🏠 Bosh Menyu",
            "🏠 Главное Меню", "🏠 Main Menu"
        ]}
    }
    
    # Check menu handlers
    for menu_text, handler in menu_handlers.items():
        if text == menu_text:
            await handler(message)
            return
    
    # Handle language selection
    if text == "🇺🇿 O'zbek tili":
        await language_change_handler(message, 'uz')
        return
    elif text == "🇷🇺 Русский язык":
        await language_change_handler(message, 'ru')
        return
    elif text == "🇬🇧 English Language":
        await language_change_handler(message, 'en')
        return
    
    # Handle personal cabinet submenu - multilingual
    personal_submenu_handlers = {
        # Statistics
        **{key: my_detailed_stats_handler for key in [
            "📊 Mening Statistikam", "📊 Моя Статистика", "📊 My Statistics"
        ]},
        # Tasks
        **{key: my_tasks_handler for key in [
            "📋 Mening Vazifalarim", "📋 Мои Задачи", "📋 My Tasks"
        ]}
    }
    
    for menu_text, handler in personal_submenu_handlers.items():
        if text == menu_text:
            await handler(message)
            return
    
    # Handle AI help topics - multilingual
    ai_topic_handlers = {
        "☕ Espresso": ("☕ Espresso", 'espresso tayyorlash'),
        "🥛 Latte": ("🥛 Latte", 'latte retsepti'),
        "☕ Cappuccino": ("☕ Cappuccino", 'cappuccino qanday tayyorlanadi'),
        "🫘 Kofe Donlari": ("🫘 Kofe Donlari", 'kofe donlari haqida'),
        "🫘 Кофейные Зерна": ("🫘 Кофейные Зерна", 'kofe donlari haqida'),
        "🫘 Coffee Beans": ("🫘 Coffee Beans", 'kofe donlari haqida'),
        "🥛 Sut Ishlash": ("🥛 Sut Ishlash", 'sut steaming texnikasi'),
        "🥛 Взбивание Молока": ("🥛 Взбивание Молока", 'sut steaming texnikasi'),
        "🥛 Milk Steaming": ("🥛 Milk Steaming", 'sut steaming texnikasi'),
        "🎨 Latte Art": ("🎨 Latte Art", 'latte art qanday qilinadi'),
        "☕ Эспрессо": ("☕ Эспрессо", 'espresso tayyorlash'),
        "🥛 Латте": ("🥛 Латте", 'latte retsepti'),
        "☕ Капучино": ("☕ Капучино", 'cappuccino qanday tayyorlanadi')
    }
    
    if text in ai_topic_handlers:
        topic_text, question = ai_topic_handlers[text]
        await ai_topic_handler(message, question)
        return
    
    # Handle cleaning submenu - multilingual  
    if text in ["📸 Hojatxona Tekshiruvi", "📸 Проверка Туалета", "📸 Bathroom Check"]:
        await bathroom_check_handler(message)
        return
    
    # If not a menu item, treat as AI question
    else:
        # Show typing indicator
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Get enhanced coffee AI response
        employee_context = {
            "name": employee[1],
            "position": employee[3],
            "id": employee[0]
        }
        
        ai_response = await get_enhanced_coffee_ai_response(text, employee_context, user_id)
        
        # Save AI request
        save_ai_request(employee[0], text, ai_response)
        
        await message.answer(ai_response, reply_markup=back_to_menu_keyboard(user_id))

# Updated handlers for regular keyboards
async def main_menu_handler(message: types.Message):
    """Main menu handler"""
    user_id = message.from_user.id
    is_admin_user = is_admin(user_id)
    
    await message.answer(
        _(user_id, 'main_menu') + "\n\nKerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(user_id, is_admin_user)
    )

async def personal_cabinet_handler(message: types.Message):
    """Personal cabinet handler"""
    user_id = message.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await message.answer("❌ Xatolik!")
        return
    
    # Get personal statistics
    stats = get_personal_stats(employee[0])
    if not stats:
        await message.answer(
            "❌ Statistika ma'lumotlarini olishda xatolik!",
            reply_markup=back_to_menu_keyboard(user_id)
        )
        return
    
    # Format personal cabinet info
    success_rate = stats['success_rate']
    rating_emoji = "🏆" if success_rate >= 95 else "🥇" if success_rate >= 85 else "🥈" if success_rate >= 70 else "📈"
    
    cabinet_text = f"""🏠 **Shaxsiy Kabinet - {employee[1]}**

{rating_emoji} **Umumiy Ko'rsatkichlar:**
• Muvaffaqiyat darajasi: {success_rate:.1f}%
• Bajarilgan tekshiruvlar: {stats['approved_checks']}/{stats['total_checks']}
• AI so'rovlari: {stats['ai_requests']} ta
• Tugallanmagan vazifalar: {stats['pending_tasks']} ta

🎯 **Lavozim:** {employee[3]}
📅 **Faollik:** {datetime.now().strftime('%B %Y')}

Quyidagi bo'limlar orqali batafsil ma'lumot olishingiz mumkin:"""
    
    await message.answer(
        cabinet_text,
        reply_markup=personal_cabinet_keyboard(user_id)
    )

async def my_tasks_handler(message: types.Message):
    """My tasks handler"""
    user_id = message.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await message.answer("❌ Xatolik!")
        return
    
    tasks = get_personal_tasks(employee[0])
    
    if not tasks:
        tasks_text = f"""📋 **{employee[1]} - Shaxsiy Vazifalar**

✅ **Barcha vazifalar bajarilgan!**

Yangi vazifalar tez orada qo'shiladi."""
    else:
        tasks_text = f"""📋 **{employee[1]} - Shaxsiy Vazifalar**

"""
        
        for i, (title, description, is_completed, due_date) in enumerate(tasks, 1):
            status_emoji = "✅" if is_completed else "⏳"
            due_str = ""
            if due_date:
                due_parsed = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                if due_parsed.date() == datetime.now().date():
                    due_str = " (Bugun)"
                elif due_parsed.date() < datetime.now().date():
                    due_str = " (Muddati o'tgan)"
                else:
                    due_str = f" ({due_parsed.strftime('%d.%m')})"
            
            tasks_text += f"""{status_emoji} **{i}. {title}**{due_str}
{description}

"""
    
    await message.answer(tasks_text, reply_markup=back_to_menu_keyboard(user_id))

async def my_detailed_stats_handler(message: types.Message):
    """Detailed stats handler"""
    user_id = message.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await message.answer("❌ Xatolik!")
        return
    
    stats = get_personal_stats(employee[0])
    if not stats:
        await message.answer(
            "❌ Statistika ma'lumotlarini olishda xatolik!",
            reply_markup=back_to_menu_keyboard(user_id)
        )
        return
    
    current_month = datetime.now().strftime('%B %Y')
    
    stats_text = _(user_id, 'personal_stats',
                   name=employee[1],
                   total_checks=stats['total_checks'],
                   approved_checks=stats['approved_checks'],
                   success_rate=stats['success_rate'],
                   ai_requests=stats['ai_requests'],
                   position=employee[3],
                   current_month=current_month)
    
    # Add performance evaluation
    success_rate = stats['success_rate']
    if success_rate >= 95:
        stats_text += "\n\n🏆 **A'LO NATIJA!** Siz eng yaxshi hodimlardan birisiz!"
    elif success_rate >= 85:
        stats_text += "\n\n👍 **YAXSHI NATIJA!** Davom etishda!"
    elif success_rate >= 70:
        stats_text += "\n\n📈 **O'RTACHA NATIJA.** Yaxshilash mumkin."
    else:
        stats_text += "\n\n📝 **DIQQAT TALAB.** Ko'proq e'tibor qarating."
    
    await message.answer(stats_text, reply_markup=back_to_menu_keyboard(user_id))

async def settings_handler(message: types.Message):
    """Settings handler"""
    user_id = message.from_user.id
    current_lang = get_user_language(user_id)
    
    lang_names = {
        'uz': "O'zbek tili 🇺🇿",
        'ru': "Русский язык 🇷🇺",
        'en': "English Language 🇬🇧"
    }
    
    settings_text = f"""⚙️ **Sozlamalar**

🌐 **Joriy til:** {lang_names.get(current_lang, 'O\'zbek tili 🇺🇿')}

Tilni o'zgartirish uchun quyidagi tugmalardan birini tanlang:"""
    
    await message.answer(
        settings_text,
        reply_markup=language_selection_keyboard()
    )

async def language_change_handler(message: types.Message, new_lang: str):
    """Language change handler"""
    user_id = message.from_user.id
    
    # Update user language
    set_user_language(user_id, new_lang)
    
    # Update in database
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees 
            SET language = ? 
            WHERE telegram_id = ?
        """, (new_lang, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Language update error: {e}")
    
    success_messages = {
        'uz': "✅ Til muvaffaqiyatli o'zgartirildi - O'zbek tili",
        'ru': "✅ Язык успешно изменен - Русский язык",
        'en': "✅ Language successfully changed - English"
    }
    
    await message.answer(
        success_messages.get(new_lang, success_messages['uz']),
        reply_markup=back_to_menu_keyboard(user_id)
    )

async def ai_help_handler(message: types.Message):
    """AI help handler"""
    user_id = message.from_user.id
    
    help_text = {
        'uz': """🤖 **Qahvaxona AI Yordamchi**

Men sizga qahvaxona va kofe tayyorlash bo'yicha professional yordam bera olaman!

💡 **Misol savollar:**
• "Latteni yanada mazali qanday qilish mumkin?"
• "Espresso chiqarish vaqti nima uchun muhim?"
• "Sut mikrofoam qanday yaratiladi?"
• "Qaysi kofe donlari cappuccino uchun yaxshi?"

✨ Savolingizni yozing yoki quyidagi mavzulardan birini tanlang:""",
        'ru': """🤖 **Помощник AI для кофейни**

Я могу предоставить профессиональную помощь по кофейне и приготовлению кофе!

💡 **Примеры вопросов:**
• "Как сделать латте еще вкуснее?"
• "Почему важно время экстракции эспрессо?"
• "Как создать микропену молока?"
• "Какие зерна лучше для капучино?"

✨ Напишите ваш вопрос или выберите тему ниже:""",
        'en': """🤖 **Coffee Shop AI Assistant**

I can provide professional help with coffee shop operations and coffee preparation!

💡 **Example questions:**
• "How to make latte even more delicious?"
• "Why is espresso extraction time important?"
• "How to create milk microfoam?"
• "Which beans are best for cappuccino?"

✨ Write your question or choose a topic below:"""
    }
    
    lang = get_user_language(user_id)
    text = help_text.get(lang, help_text['uz'])
    
    await message.answer(text, reply_markup=ai_help_keyboard(user_id))

async def ai_topic_handler(message: types.Message, question: str):
    """AI topic handler - updated to use question directly"""
    user_id = message.from_user.id
    
    # Show typing indicator
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Get employee context
    employee = get_employee_by_telegram(user_id)
    employee_context = {
        "name": employee[1] if employee else "Unknown",
        "position": employee[3] if employee else "Unknown",
        "id": employee[0] if employee else 0
    }
    
    # Get AI response using the question
    content = await get_enhanced_coffee_ai_response(question, employee_context, user_id)
    
    # Save AI request if employee exists
    if employee:
        save_ai_request(employee[0], question, content)
    
    await message.answer(content, reply_markup=back_to_menu_keyboard(user_id))

async def employees_handler(message: types.Message):
    """Employees handler (Admin only)"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ Faqat adminlar uchun!")
        return
    
    await message.answer(
        "👥 **Hodimlar Boshqaruvi** (Admin)\n\nBarcha hodimlar ma'lumotlari va statistikasi:",
        reply_markup=employees_keyboard(user_id)
    )

async def cleaning_handler(message: types.Message):
    """Cleaning handler"""
    user_id = message.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    is_cleaner = employee and 'tozalovchi' in employee[3].lower()
    
    await message.answer(
        "🧹 **Tozalik Nazorati**\n\nTozalik tekshiruvlari va statistikalar:",
        reply_markup=cleaning_keyboard(user_id, is_cleaner)
    )

async def bathroom_check_handler(message: types.Message):
    """Bathroom check handler"""
    user_id = message.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee or 'tozalovchi' not in employee[3].lower():
        await message.answer(
            "❌ **Ruxsat yo'q!**\n\nFaqat tozalovchilar hojatxona tekshiruvi qila oladi.",
            reply_markup=back_to_menu_keyboard(user_id)
        )
        return
    
    await message.answer(
        """📸 **Hojatxona Tekshiruvi**

Hojatxonaning umumiy holatini ko'rsatadigan **aniq rasm** yuboring.

🔍 **Tekshiriladigan narsalar:**
• ✅ Tualet qogozi mavjudligi
• 🧴 Suyuq sovun holati
• 🚽 Unitaz tozaligi
• 🪣 Pollar holati (quruq/nam)
• 🧽 Lavabo va peshtaxtalar

⏰ **Vaqt:** 40 daqiqa (10 daqiqa bonus)

📱 Rasmni yuborganingizdan so'ng AI tahlil qiladi.""",
        reply_markup=back_to_menu_keyboard(user_id)
    )
    
    waiting_for_photo[user_id] = "bathroom_check"

async def reports_handler(message: types.Message):
    """Reports handler"""
    user_id = message.from_user.id
    is_admin_user = is_admin(user_id)
    
    report_text = "📊 **Hisobotlar Bo'limi**\n\n" + (
        "Admin sifatida barcha hisobotlarni ko'rishingiz mumkin:" if is_admin_user
        else "Shaxsiy va jamoaviy ko'rsatkichlaringizni ko'ring:"
    )
    
    await message.answer(report_text, reply_markup=reports_keyboard(user_id, is_admin_user))

async def restaurant_handler(message: types.Message):
    """Restaurant handler"""
    user_id = message.from_user.id
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'name'")
        name = cursor.fetchone()
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'description'")
        description = cursor.fetchone()
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'working_hours'")
        hours = cursor.fetchone()
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'contact'")
        contact = cursor.fetchone()
        
        conn.close()
        
        restaurant_text = f"""🏢 **{name[0] if name else 'Demo Restoran'}**

📝 **Tavsif:**
{description[0] if description else 'Ma\'lumot kiritilmagan'}

🕐 **Ish vaqti:**
{hours[0] if hours else '09:00 - 23:00'}

📞 **Aloqa:**
{contact[0] if contact else '+998900007747'}

🎯 **Bizning maqsad:**
Mijozlarimizga eng yaxshi xizmat va sifatli taom taqdim etish

✨ **Qadriyatlarimiz:**
• Sifat
• Xizmat
• Jamoavilik
• Rivojlanish"""
        
    except Exception as e:
        restaurant_text = f"🏢 **Restoran Haqida**\n\n❌ Ma'lumotlarni olishda xatolik: {str(e)}"
    
    await message.answer(restaurant_text, reply_markup=back_to_menu_keyboard(user_id))

# Callback query handlers
@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_admin_user = is_admin(user_id)
    
    await callback.message.edit_text(
        _(user_id, 'main_menu') + "\n\nKerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(user_id, is_admin_user)
    )

@dp.callback_query(F.data == "personal_cabinet")
async def personal_cabinet_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await callback.answer("❌ Xatolik!")
        return
    
    # Get personal statistics
    stats = get_personal_stats(employee[0])
    if not stats:
        await callback.message.edit_text(
            "❌ Statistika ma'lumotlarini olishda xatolik!",
            reply_markup=back_to_menu_keyboard(user_id)
        )
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Mening Statistikam", callback_data="my_detailed_stats"),
        InlineKeyboardButton(text="📋 Mening Vazifalarim", callback_data="my_tasks")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Ish Jadvali", callback_data="my_schedule"),
        InlineKeyboardButton(text="⏰ Ish Vaqti", callback_data="work_time")
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting", callback_data="my_rating"),
        InlineKeyboardButton(text="🎯 Maqsadlar", callback_data="my_goals")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    )
    
    # Format personal cabinet info
    success_rate = stats['success_rate']
    rating_emoji = "🏆" if success_rate >= 95 else "🥇" if success_rate >= 85 else "🥈" if success_rate >= 70 else "📈"
    
    cabinet_text = f"""🏠 **Shaxsiy Kabinet - {employee[1]}**

{rating_emoji} **Umumiy Ko'rsatkichlar:**
• Muvaffaqiyat darajasi: {success_rate:.1f}%
• Bajarilgan tekshiruvlar: {stats['approved_checks']}/{stats['total_checks']}
• AI so'rovlari: {stats['ai_requests']} ta
• Tugallanmagan vazifalar: {stats['pending_tasks']} ta

🎯 **Lavozim:** {employee[3]}
📅 **Faollik:** {datetime.now().strftime('%B %Y')}

Quyidagi bo'limlar orqali batafsil ma'lumot olishingiz mumkin:"""
    
    await callback.message.edit_text(
        cabinet_text,
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "my_tasks")
async def my_tasks_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await callback.answer("❌ Xatolik!")
        return
    
    tasks = get_personal_tasks(employee[0])
    
    if not tasks:
        tasks_text = f"""📋 **{employee[1]} - Shaxsiy Vazifalar**

✅ **Barcha vazifalar bajarilgan!**

Yangi vazifalar tez orada qo'shiladi."""
    else:
        tasks_text = f"""📋 **{employee[1]} - Shaxsiy Vazifalar**

"""
        
        for i, (title, description, is_completed, due_date) in enumerate(tasks, 1):
            status_emoji = "✅" if is_completed else "⏳"
            due_str = ""
            if due_date:
                due_parsed = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                if due_parsed.date() == datetime.now().date():
                    due_str = " (Bugun)"
                elif due_parsed.date() < datetime.now().date():
                    due_str = " (Muddati o'tgan)"
                else:
                    due_str = f" ({due_parsed.strftime('%d.%m')})"
            
            tasks_text += f"""{status_emoji} **{i}. {title}**{due_str}
{description}

"""
    
    await callback.message.edit_text(
        tasks_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Shaxsiy Kabinet", callback_data="personal_cabinet")
        ]])
    )

@dp.callback_query(F.data == "my_detailed_stats")
async def my_detailed_stats_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee:
        await callback.answer("❌ Xatolik!")
        return
    
    stats = get_personal_stats(employee[0])
    if not stats:
        await callback.message.edit_text(
            "❌ Statistika ma'lumotlarini olishda xatolik!",
            reply_markup=back_to_menu_keyboard(user_id)
        )
        return
    
    current_month = datetime.now().strftime('%B %Y')
    
    stats_text = _(user_id, 'personal_stats',
                   name=employee[1],
                   total_checks=stats['total_checks'],
                   approved_checks=stats['approved_checks'],
                   success_rate=stats['success_rate'],
                   ai_requests=stats['ai_requests'],
                   position=employee[3],
                   current_month=current_month)
    
    # Add performance evaluation
    success_rate = stats['success_rate']
    if success_rate >= 95:
        stats_text += "\n\n🏆 **A'LO NATIJA!** Siz eng yaxshi hodimlardan birisiz!"
    elif success_rate >= 85:
        stats_text += "\n\n👍 **YAXSHI NATIJA!** Davom etishda!"
    elif success_rate >= 70:
        stats_text += "\n\n📈 **O'RTACHA NATIJA.** Yaxshilash mumkin."
    else:
        stats_text += "\n\n📝 **DIQQAT TALAB.** Ko'proq e'tibor qarating."
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Shaxsiy Kabinet", callback_data="personal_cabinet")
        ]])
    )

@dp.callback_query(F.data == "settings")
async def settings_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_lang = get_user_language(user_id)
    
    lang_names = {
        'uz': "O'zbek tili 🇺🇿",
        'ru': "Русский язык 🇷🇺",
        'en': "English Language 🇬🇧"
    }
    
    settings_text = f"""⚙️ **Sozlamalar**

🌐 **Joriy til:** {lang_names.get(current_lang, 'O\'zbek tili 🇺🇿')}

Tilni o'zgartirish uchun quyidagi tugmalardan birini tanlang:"""
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=language_selection_keyboard()
    )

@dp.callback_query(F.data.startswith("lang_"))
async def language_change_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    new_lang = callback.data.split("_")[1]
    
    # Update user language
    set_user_language(user_id, new_lang)
    
    # Update in database
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees 
            SET language = ? 
            WHERE telegram_id = ?
        """, (new_lang, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Language update error: {e}")
    
    success_messages = {
        'uz': "✅ Til muvaffaqiyatli o'zgartirildi - O'zbek tili",
        'ru': "✅ Язык успешно изменен - Русский язык",
        'en': "✅ Language successfully changed - English"
    }
    
    await callback.message.edit_text(
        success_messages.get(new_lang, success_messages['uz']),
        reply_markup=back_to_menu_keyboard(user_id)
    )

@dp.callback_query(F.data == "ai_help")
async def ai_help_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="☕ Espresso", callback_data="help_espresso"),
        InlineKeyboardButton(text="🥛 Latte", callback_data="help_latte")
    )
    builder.row(
        InlineKeyboardButton(text="☕ Cappuccino", callback_data="help_cappuccino"),
        InlineKeyboardButton(text="🫘 Kofe Donlari", callback_data="help_beans")
    )
    builder.row(
        InlineKeyboardButton(text="🥛 Sut Ishlash", callback_data="help_milk"),
        InlineKeyboardButton(text="🎨 Latte Art", callback_data="help_art")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    )
    
    help_text = {
        'uz': """🤖 **Qahvaxona AI Yordamchi**

Men sizga qahvaxona va kofe tayyorlash bo'yicha professional yordam bera olaman!

💡 **Misol savollar:**
• "Latteni yanada mazali qanday qilish mumkin?"
• "Espresso chiqarish vaqti nima uchun muhim?"
• "Sut mikrofoam qanday yaratiladi?"
• "Qaysi kofe donlari cappuccino uchun yaxshi?"

✨ Savolingizni yozing yoki quyidagi mavzulardan birini tanlang:""",
        'ru': """🤖 **Помощник AI для кофейни**

Я могу предоставить профессиональную помощь по кофейне и приготовлению кофе!

💡 **Примеры вопросов:**
• "Как сделать латте еще вкуснее?"
• "Почему важно время экстракции эспрессо?"
• "Как создать микропену молока?"
• "Какие зерна лучше для капучино?"

✨ Напишите ваш вопрос или выберите тему ниже:""",
        'en': """🤖 **Coffee Shop AI Assistant**

I can provide professional help with coffee shop operations and coffee preparation!

💡 **Example questions:**
• "How to make latte even more delicious?"
• "Why is espresso extraction time important?"
• "How to create milk microfoam?"
• "Which beans are best for cappuccino?"

✨ Write your question or choose a topic below:"""
    }
    
    lang = get_user_language(user_id)
    text = help_text.get(lang, help_text['uz'])
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("help_"))
async def help_topics_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    topic = callback.data.split("_")[1]
    
    # Get enhanced response for specific topic
    topic_questions = {
        'espresso': 'espresso tayyorlash',
        'latte': 'latte retsepti',
        'cappuccino': 'cappuccino qanday tayyorlanadi',
        'beans': 'kofe donlari haqida',
        'milk': 'sut steaming texnikasi',
        'art': 'latte art qanday qilinadi'
    }
    
    question = topic_questions.get(topic, 'kofe tayyorlash')
    content = get_enhanced_static_coffee_response(question, user_id)
    
    await callback.message.edit_text(
        content,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 AI Yordam", callback_data="ai_help")
        ]])
    )

# Keep existing handlers for admin, cleaning, etc.
@dp.callback_query(F.data == "employees")
async def employees_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Faqat adminlar uchun!")
        return
        
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Barcha Hodimlar", callback_data="all_employees"),
        InlineKeyboardButton(text="📊 Umumiy Statistika", callback_data="employees_stats")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Ish Jadvallari", callback_data="all_schedules"),
        InlineKeyboardButton(text="🎯 Performance", callback_data="performance_overview")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        "👥 **Hodimlar Boshqaruvi** (Admin)\n\nBarcha hodimlar ma'lumotlari va statistikasi:",
        reply_markup=builder.as_markup()
    )

# Continue with existing cleaning, photo handlers, etc...
waiting_for_photo = {}

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

# Photo analysis remains the same
async def analyze_bathroom_photo(photo_data):
    """AI photo analysis with real/demo modes"""
    
    if AI_ENABLED:
        try:
            print("🔍 Using real OpenAI Vision analysis...")
            
            # Convert to base64
            import base64
            base64_image = base64.b64encode(photo_data).decode('utf-8')
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Hojatxona rasmini batafsil tahlil qiling va JSON formatda javob bering:

{
    "toilet_paper": true/false,
    "soap": "full"/"half"/"empty", 
    "toilet": "clean"/"dirty"/"very_dirty",
    "floor": "dry"/"wet"/"flooded",
    "sink": "clean"/"dirty",
    "overall": "approved"/"rejected",
    "score": 0-100,
    "notes": "batafsil tushuntirish o'zbek tilida"
}

Faqat JSON javob bering, boshqa matn yo'q."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=600,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                result = json.loads(json_str)
                print(f"✅ Real AI analysis complete: {result['score']}/100")
                return result
                
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            print("🔄 Falling back to demo mode...")
    
    # Demo/Fallback analysis
    print("🎭 Using demo AI analysis...")
    await asyncio.sleep(2)  # Simulate processing time
    
    # Improved demo logic
    toilet_paper = random.choice([True, True, True, False])  # 75% success
    soap_level = random.choice(['full', 'half', 'empty'])
    toilet_state = random.choice(['clean', 'clean', 'dirty'])  # 66% clean
    floor_state = random.choice(['dry', 'wet'])
    sink_state = random.choice(['clean', 'dirty'])
    
    # Calculate score
    score = 100
    issues = []
    
    if not toilet_paper:
        score -= 25
        issues.append("tualet qogozi tugagan")
    if soap_level == 'empty':
        score -= 20
        issues.append("sovun tugagan")
    elif soap_level == 'half':
        score -= 5
    if toilet_state == 'dirty':
        score -= 30
        issues.append("unitaz tozalanmagan")
    elif toilet_state == 'very_dirty':
        score -= 40
        issues.append("unitaz juda iflos")
    if floor_state == 'wet':
        score -= 15
        issues.append("pol nam, artish kerak")
    if sink_state == 'dirty':
        score -= 10
        issues.append("lavabo tozalanmagan")
    
    overall = 'approved' if score >= 70 else 'rejected'
    
    if overall == 'approved':
        notes = "Hojatxona umumiy holda tartibda. Yaxshi ish!" + (" (Demo AI)" if not AI_ENABLED else "")
    else:
        notes = f"Quyidagi muammolar aniqlandi: {', '.join(issues)}. Iltimos, tuzating." + (" (Demo AI)" if not AI_ENABLED else "")
    
    return {
        'toilet_paper': toilet_paper,
        'soap': soap_level,
        'toilet': toilet_state,
        'floor': floor_state,
        'sink': sink_state,
        'overall': overall,
        'score': max(0, score),
        'notes': notes
    }

# Continue with photo handlers and other existing functionality...
@dp.callback_query(F.data == "bathroom_check")
async def bathroom_check_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    employee = get_employee_by_telegram(user_id)
    
    if not employee or 'tozalovchi' not in employee[3].lower():
        await callback.message.edit_text(
            "❌ **Ruxsat yo'q!**\n\nFaqat tozalovchilar hojatxona tekshiruvi qila oladi.",
            reply_markup=back_to_menu_keyboard(user_id)
        )
        return
    
    await callback.message.edit_text(
        """📸 **Hojatxona Tekshiruvi**

Hojatxonaning umumiy holatini ko'rsatadigan **aniq rasm** yuboring.

🔍 **Tekshiriladigan narsalar:**
• ✅ Tualet qogozi mavjudligi
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
    """Handle photo uploads with real AI"""
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
    
    # Check API status and show appropriate message
    if AI_ENABLED:
        processing_msg = await message.answer("🤖 **Haqiqiy AI tahlil qilmoqda...**\n\n⏳ Iltimos, kuting...")
    else:
        processing_msg = await message.answer("🤖 **Demo AI tahlil qilmoqda...**\n\n⏳ (Haqiqiy AI uchun OPENAI_API_KEY sozlang)")
    
    try:
        # Download photo
        file_info = await bot.get_file(photo.file_id)
        file_data = await bot.download_file(file_info.file_path)
        photo_bytes = file_data.read()
        
        # AI Analysis
        analysis_result = await analyze_bathroom_photo(photo_bytes)
        
        if not analysis_result:
            await processing_msg.edit_text("❌ Tahlil xatosi! Qayta urinib ko'ring.")
            return
        
        # Save results
        photo_path = f"photos/{photo.file_id}.jpg"
        is_approved = analysis_result['overall'] == 'approved'
        save_cleaning_check(employee[0], photo_path, analysis_result, is_approved)
        
        # Format results
        score = analysis_result.get('score', 0)
        result_text = f"🤖 **AI Tahlil Natijasi:** {score}/100\n\n"
        
        # Details
        result_text += f"{'✅' if analysis_result['toilet_paper'] else '❌'} **Tualet qogozi:** {'Bor' if analysis_result['toilet_paper'] else 'Yo\'q'}\n"
        result_text += f"🧴 **Sovun:** {analysis_result['soap']}\n"
        result_text += f"🚽 **Unitaz:** {analysis_result['toilet']}\n"
        result_text += f"🪣 **Pollar:** {analysis_result['floor']}\n"
        result_text += f"🧽 **Lavabo:** {analysis_result['sink']}\n\n"
        
        if is_approved:
            result_text += f"✅ **QABUL QILINDI!** ({score}/100)\n\n"
            result_text += f"💬 {analysis_result['notes']}\n\n🎉 Ajoyib ish!"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")],
                [InlineKeyboardButton(text="🧹 Tozalik", callback_data="cleaning")]
            ])
        else:
            result_text += f"❌ **RAD ETILDI!** ({score}/100)\n\n"
            result_text += f"💬 {analysis_result['notes']}\n\n"
            result_text += "🔄 **Iltimos, tozalab qayta rasm yuboring.**"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Qayta", callback_data="bathroom_check")],
                [InlineKeyboardButton(text="🧹 Tozalik", callback_data="cleaning")]
            ])
        
        await processing_msg.edit_text(result_text, reply_markup=keyboard)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Xatolik: {str(e)}")
    
    finally:
        if user_id in waiting_for_photo:
            del waiting_for_photo[user_id]

# Additional callback handlers for remaining features
@dp.callback_query(F.data == "reports")
async def reports_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    builder = InlineKeyboardBuilder()
    
    if is_admin(user_id):
        builder.row(
            InlineKeyboardButton(text="📈 Kunlik", callback_data="daily_report"),
            InlineKeyboardButton(text="📊 Haftalik", callback_data="weekly_report")
        )
        builder.row(
            InlineKeyboardButton(text="📅 Oylik", callback_data="monthly_report"),
            InlineKeyboardButton(text="👥 Hodimlar", callback_data="employees_report")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="📈 Mening Hisobotim", callback_data="my_personal_report"),
            InlineKeyboardButton(text="📊 Jamoaviy Ko'rsatkichlar", callback_data="team_overview")
        )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")
    )
    
    report_text = "📊 **Hisobotlar Bo'limi**\n\n" + (
        "Admin sifatida barcha hisobotlarni ko'rishingiz mumkin:" if is_admin(user_id)
        else "Shaxsiy va jamoaviy ko'rsatkichlaringizni ko'ring:"
    )
    
    await callback.message.edit_text(report_text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "restaurant")
async def restaurant_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'name'")
        name = cursor.fetchone()
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'description'")
        description = cursor.fetchone()
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'working_hours'")
        hours = cursor.fetchone()
        cursor.execute("SELECT info_value FROM restaurant_info WHERE info_key = 'contact'")
        contact = cursor.fetchone()
        
        conn.close()
        
        restaurant_text = f"""🏢 **{name[0] if name else 'Demo Restoran'}**

📝 **Tavsif:**
{description[0] if description else 'Ma\'lumot kiritilmagan'}

🕐 **Ish vaqti:**
{hours[0] if hours else '09:00 - 23:00'}

📞 **Aloqa:**
{contact[0] if contact else '+998900007747'}

🎯 **Bizning maqsad:**
Mijozlarimizga eng yaxshi xizmat va sifatli taom taqdim etish

✨ **Qadriyatlarimiz:**
• Sifat
• Xizmat
• Jamoavilik
• Rivojlanish"""
        
    except Exception as e:
        restaurant_text = f"🏢 **Restoran Haqida**\n\n❌ Ma'lumotlarni olishda xatolik: {str(e)}"
    
    await callback.message.edit_text(
        restaurant_text,
        reply_markup=back_to_menu_keyboard(user_id)
    )

# Catch-all for unknown callbacks
@dp.callback_query()
async def handle_unknown_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer("🚧 Bu funksiya hali ishlab chiqilmoqda!")

# Error handler
@dp.error()
async def error_handler(event, exception):
    """Global error handler"""
    print(f"Error occurred: {exception}")
    return True

# Health check endpoint (for Render)
from aiohttp import web
from aiohttp.web import Request, Response

async def health_check(request: Request) -> Response:
    return web.json_response({"status": "healthy", "bot": "running"})

async def setup_webapp():
    """Setup web app for health checks"""
    app = web.Application()
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    return app

# Main function
async def main():
    """Main function to run the bot"""
    try:
        print("🚀 Starting Enhanced Horeca AI Bot...")
        print(f"📱 Python version: {__import__('sys').version}")
        print(f"💾 Database: {DATABASE_PATH}")
        print(f"🤖 AI Status: {'Real AI' if AI_ENABLED else 'Demo Mode'}")
        print(f"🌐 Multi-language: UZ/RU/EN support")
        print(f"👥 Role-based access: Admin vs Employee")
        
        # Initialize database
        print("📊 Initializing enhanced database...")
        if not init_database():
            print("❌ Database initialization failed!")
            return
        
        print("✅ Database ready!")
        print("🤖 Enhanced bot starting...")
        print("📱 Features:")
        print("  - Personal Cabinet for employees")
        print("  - Enhanced Coffee AI Assistant")
        print("  - Multi-language support (UZ/RU/EN)")
        print("  - Role-based permissions")
        print("  - Personal tasks and statistics")
        print("🎯 Admin: +998900007747")
        print("👥 Test users: +998901234567-70")
        print("🌐 Health check: /health")
        print("🛑 Stop with Ctrl+C")
        print("-" * 60)
        
        # Setup web app for health checks
        app = await setup_webapp()
        
        # Start web server for health checks (required by Render)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        print(f"🌐 Web server started on port {PORT}")
        
        # Start bot polling
        await dp.start_polling(bot, skip_updates=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔄 Cleaning up...")
        await bot.session.close()
        print("👋 Goodbye!")

if __name__ == "__main__":
    # Setup logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress some verbose logs
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot terminated")
    except Exception as e:
        print(f"❌ Startup error: {e}")
