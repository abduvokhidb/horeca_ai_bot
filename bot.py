import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    CallbackQuery
)
from telegram.ext import (
    Updater, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    Filters, 
    ConversationHandler, 
    CallbackContext
)

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token (O'zingizning tokeningizni qo'ying)
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Ma'lumotlar fayli
DATA_FILE = 'bot_data.json'

# Conversation states
(WAITING_TASK_TITLE, WAITING_TASK_DESC, WAITING_TASK_DEADLINE, 
 WAITING_TASK_ASSIGNEE, WAITING_PROJECT_NAME, WAITING_PROJECT_DESC,
 WAITING_TEAM_NAME, WAITING_TEAM_DESC, WAITING_FEEDBACK) = range(9)

# Task Status
class TaskStatus(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

# Task Priority
class TaskPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

# Ko'p tillilik - 3 ta til: O'zbek, Rus, Qozoq
LANGUAGES = {
    'uz': {
        'name': '🇺🇿 O\'zbek',
        'flag': '🇺🇿',
        'welcome': '👋 Xush kelibsiz!\n\nMen Task Management Bot - vazifalar va loyihalarni boshqarish uchun yordamchingiz.',
        'choose_action': '📋 Kerakli amalni tanlang:',
        'main_menu': '🏠 Asosiy menyu',
        'my_tasks': '📋 Mening vazifalarim',
        'new_task': '➕ Yangi vazifa',
        'projects': '📁 Loyihalar',
        'new_project': '➕ Yangi loyiha',
        'teams': '👥 Jamoalar',
        'new_team': '➕ Yangi jamoa',
        'calendar': '📅 Kalendar',
        'today_tasks': '📌 Bugungi vazifalar',
        'reports': '📊 Hisobotlar',
        'notifications': '🔔 Bildirishnomalar',
        'settings': '⚙️ Sozlamalar',
        'help': '❓ Yordam',
        'back': '◀️ Orqaga',
        'cancel': '❌ Bekor qilish',
        'done': '✅ Tayyor',
        'edit': '✏️ Tahrirlash',
        'delete': '🗑 O\'chirish',
        'language': '🌐 Til',
        'choose_language': '🌐 Tilni tanlang:',
        'language_changed': '✅ Til muvaffaqiyatli o\'zgartirildi!',
        'enter_task_title': '📝 Vazifa nomini kiriting:',
        'enter_task_desc': '📄 Vazifa tavsifini kiriting (yoki /skip):',
        'enter_deadline': '📅 Muddatni kiriting (kun.oy.yil formatida yoki /skip):',
        'task_created': '✅ Vazifa muvaffaqiyatli yaratildi!',
        'no_tasks': '📭 Hozircha vazifalar yo\'q',
        'select_task': '📋 Vazifani tanlang:',
        'task_details': '📋 Vazifa tafsilotlari',
        'status': '📊 Status',
        'priority': '⚡ Muhimlik',
        'deadline': '📅 Muddat',
        'description': '📝 Tavsif',
        'created_date': '🕐 Yaratilgan',
        'assigned_to': '👤 Mas\'ul',
        'change_status': '🔄 Statusni o\'zgartirish',
        'change_priority': '⚡ Muhimlikni o\'zgartirish',
        'assign_user': '👤 Mas\'ul tayinlash',
        'task_updated': '✅ Vazifa yangilandi!',
        'task_deleted': '✅ Vazifa o\'chirildi!',
        'confirm_delete': '❓ Vazifani o\'chirishni tasdiqlaysizmi?',
        'yes': '✅ Ha',
        'no': '❌ Yo\'q',
        'search': '🔍 Qidirish',
        'filter': '🎯 Filtr',
        'sort': '↕️ Saralash',
        'statistics': '📈 Statistika',
        'export': '📤 Export',
        'import': '📥 Import',
        'profile': '👤 Profil',
        'logout': '🚪 Chiqish',
        'about': 'ℹ️ Bot haqida',
        'contact_admin': '💬 Admin bilan bog\'lanish',
        'rate_bot': '⭐ Botni baholash',
        'share': '📢 Ulashish',
        'status_todo': '📝 Bajarilishi kerak',
        'status_in_progress': '🔄 Jarayonda',
        'status_review': '👀 Tekshirilmoqda',
        'status_done': '✅ Bajarildi',
        'status_cancelled': '❌ Bekor qilindi',
        'priority_low': '🟢 Past',
        'priority_medium': '🟡 O\'rta',
        'priority_high': '🔴 Yuqori',
        'priority_urgent': '🚨 Shoshilinch',
        'daily_report': '📊 Kunlik hisobot',
        'weekly_report': '📊 Haftalik hisobot',
        'monthly_report': '📊 Oylik hisobot',
        'no_projects': '📭 Loyihalar yo\'q',
        'project_created': '✅ Loyiha yaratildi!',
        'select_project': '📁 Loyihani tanlang:',
        'project_details': '📁 Loyiha tafsilotlari',
        'add_to_project': '📎 Loyihaga qo\'shish',
        'remove_from_project': '📎 Loyihadan chiqarish',
        'team_members': '👥 Jamoa a\'zolari',
        'add_member': '➕ A\'zo qo\'shish',
        'remove_member': '➖ A\'zoni chiqarish',
        'member_added': '✅ A\'zo qo\'shildi!',
        'member_removed': '✅ A\'zo chiqarildi!',
        'notifications_on': '🔔 Bildirishnomalar yoqilgan',
        'notifications_off': '🔕 Bildirishnomalar o\'chirilgan',
        'reminder_set': '⏰ Eslatma o\'rnatildi!',
        'search_results': '🔍 Qidiruv natijalari',
        'no_results': '❌ Hech narsa topilmadi',
        'loading': '⏳ Yuklanmoqda...',
        'error': '❌ Xatolik yuz berdi!',
        'success': '✅ Muvaffaqiyatli!',
        'warning': '⚠️ Diqqat!',
        'info': 'ℹ️ Ma\'lumot',
        'confirm': '❓ Tasdiqlaysizmi?',
        'enter_project_name': '📝 Loyiha nomini kiriting:',
        'enter_project_desc': '📄 Loyiha tavsifini kiriting (yoki /skip):',
        'enter_team_name': '📝 Jamoa nomini kiriting:',
        'enter_team_desc': '📄 Jamoa tavsifini kiriting (yoki /skip):',
        'team_created': '✅ Jamoa yaratildi!',
        'no_teams': '📭 Jamoalar yo\'q',
        'select_team': '👥 Jamoani tanlang:',
        'team_details': '👥 Jamoa tafsilotlari',
        'feedback': '💬 Fikr-mulohaza',
        'send_feedback': '📝 Fikringizni yuboring:',
        'feedback_sent': '✅ Fikr-mulohazangiz yuborildi!',
        'quick_actions': '⚡ Tezkor amallar',
        'mark_done': '✅ Bajarildi deb belgilash',
        'postpone': '⏰ Kechiktirish',
        'duplicate': '📑 Nusxalash',
        'archive': '📦 Arxivlash',
        'unarchive': '📤 Arxivdan chiqarish',
        'pin': '📌 Qadash',
        'unpin': '📌 Qadashdan olish',
        'all_tasks': '📋 Barcha vazifalar',
        'my_created': '✏️ Men yaratganlar',
        'assigned_to_me': '👤 Menga tayinlanganlar',
        'high_priority': '🔴 Muhim vazifalar',
        'overdue': '⏰ Muddati o\'tganlar',
        'completed': '✅ Bajarilganlar',
        'upcoming': '📅 Yaqinlashayotganlar',
        'today': '📌 Bugun',
        'tomorrow': '📅 Ertaga',
        'this_week': '📅 Bu hafta',
        'next_week': '📅 Keyingi hafta',
        'this_month': '📅 Bu oy',
        'custom_date': '📅 Boshqa sana'
    },
    'ru': {
        'name': '🇷🇺 Русский',
        'flag': '🇷🇺',
        'welcome': '👋 Добро пожаловать!\n\nЯ Task Management Bot - ваш помощник для управления задачами и проектами.',
        'choose_action': '📋 Выберите действие:',
        'main_menu': '🏠 Главное меню',
        'my_tasks': '📋 Мои задачи',
        'new_task': '➕ Новая задача',
        'projects': '📁 Проекты',
        'new_project': '➕ Новый проект',
        'teams': '👥 Команды',
        'new_team': '➕ Новая команда',
        'calendar': '📅 Календарь',
        'today_tasks': '📌 Задачи на сегодня',
        'reports': '📊 Отчеты',
        'notifications': '🔔 Уведомления',
        'settings': '⚙️ Настройки',
        'help': '❓ Помощь',
        'back': '◀️ Назад',
        'cancel': '❌ Отмена',
        'done': '✅ Готово',
        'edit': '✏️ Редактировать',
        'delete': '🗑 Удалить',
        'language': '🌐 Язык',
        'choose_language': '🌐 Выберите язык:',
        'language_changed': '✅ Язык успешно изменен!',
        'enter_task_title': '📝 Введите название задачи:',
        'enter_task_desc': '📄 Введите описание задачи (или /skip):',
        'enter_deadline': '📅 Введите срок (в формате день.месяц.год или /skip):',
        'task_created': '✅ Задача успешно создана!',
        'no_tasks': '📭 Пока нет задач',
        'select_task': '📋 Выберите задачу:',
        'task_details': '📋 Детали задачи',
        'status': '📊 Статус',
        'priority': '⚡ Приоритет',
        'deadline': '📅 Срок',
        'description': '📝 Описание',
        'created_date': '🕐 Создано',
        'assigned_to': '👤 Ответственный',
        'change_status': '🔄 Изменить статус',
        'change_priority': '⚡ Изменить приоритет',
        'assign_user': '👤 Назначить ответственного',
        'task_updated': '✅ Задача обновлена!',
        'task_deleted': '✅ Задача удалена!',
        'confirm_delete': '❓ Подтвердите удаление задачи?',
        'yes': '✅ Да',
        'no': '❌ Нет',
        'search': '🔍 Поиск',
        'filter': '🎯 Фильтр',
        'sort': '↕️ Сортировка',
        'statistics': '📈 Статистика',
        'export': '📤 Экспорт',
        'import': '📥 Импорт',
        'profile': '👤 Профиль',
        'logout': '🚪 Выход',
        'about': 'ℹ️ О боте',
        'contact_admin': '💬 Связь с админом',
        'rate_bot': '⭐ Оценить бота',
        'share': '📢 Поделиться',
        'status_todo': '📝 Нужно выполнить',
        'status_in_progress': '🔄 В процессе',
        'status_review': '👀 На проверке',
        'status_done': '✅ Выполнено',
        'status_cancelled': '❌ Отменено',
        'priority_low': '🟢 Низкий',
        'priority_medium': '🟡 Средний',
        'priority_high': '🔴 Высокий',
        'priority_urgent': '🚨 Срочный',
        'daily_report': '📊 Ежедневный отчет',
        'weekly_report': '📊 Еженедельный отчет',
        'monthly_report': '📊 Ежемесячный отчет',
        'no_projects': '📭 Нет проектов',
        'project_created': '✅ Проект создан!',
        'select_project': '📁 Выберите проект:',
        'project_details': '📁 Детали проекта',
        'add_to_project': '📎 Добавить в проект',
        'remove_from_project': '📎 Удалить из проекта',
        'team_members': '👥 Члены команды',
        'add_member': '➕ Добавить участника',
        'remove_member': '➖ Удалить участника',
        'member_added': '✅ Участник добавлен!',
        'member_removed': '✅ Участник удален!',
        'notifications_on': '🔔 Уведомления включены',
        'notifications_off': '🔕 Уведомления выключены',
        'reminder_set': '⏰ Напоминание установлено!',
        'search_results': '🔍 Результаты поиска',
        'no_results': '❌ Ничего не найдено',
        'loading': '⏳ Загрузка...',
        'error': '❌ Произошла ошибка!',
        'success': '✅ Успешно!',
        'warning': '⚠️ Внимание!',
        'info': 'ℹ️ Информация',
        'confirm': '❓ Подтвердить?',
        'enter_project_name': '📝 Введите название проекта:',
        'enter_project_desc': '📄 Введите описание проекта (или /skip):',
        'enter_team_name': '📝 Введите название команды:',
        'enter_team_desc': '📄 Введите описание команды (или /skip):',
        'team_created': '✅ Команда создана!',
        'no_teams': '📭 Нет команд',
        'select_team': '👥 Выберите команду:',
        'team_details': '👥 Детали команды',
        'feedback': '💬 Обратная связь',
        'send_feedback': '📝 Отправьте ваш отзыв:',
        'feedback_sent': '✅ Ваш отзыв отправлен!',
        'quick_actions': '⚡ Быстрые действия',
        'mark_done': '✅ Отметить выполненным',
        'postpone': '⏰ Отложить',
        'duplicate': '📑 Дублировать',
        'archive': '📦 Архивировать',
        'unarchive': '📤 Разархивировать',
        'pin': '📌 Закрепить',
        'unpin': '📌 Открепить',
        'all_tasks': '📋 Все задачи',
        'my_created': '✏️ Созданные мной',
        'assigned_to_me': '👤 Назначенные мне',
        'high_priority': '🔴 Важные задачи',
        'overdue': '⏰ Просроченные',
        'completed': '✅ Выполненные',
        'upcoming': '📅 Предстоящие',
        'today': '📌 Сегодня',
        'tomorrow': '📅 Завтра',
        'this_week': '📅 Эта неделя',
        'next_week': '📅 Следующая неделя',
        'this_month': '📅 Этот месяц',
        'custom_date': '📅 Другая дата'
    },
    'kk': {
        'name': '🇰🇿 Қазақша',
        'flag': '🇰🇿',
        'welcome': '👋 Қош келдіңіз!\n\nМен Task Management Bot - тапсырмалар мен жобаларды басқару үшін көмекшіңізбін.',
        'choose_action': '📋 Әрекетті таңдаңыз:',
        'main_menu': '🏠 Басты мәзір',
        'my_tasks': '📋 Менің тапсырмаларым',
        'new_task': '➕ Жаңа тапсырма',
        'projects': '📁 Жобалар',
        'new_project': '➕ Жаңа жоба',
        'teams': '👥 Топтар',
        'new_team': '➕ Жаңа топ',
        'calendar': '📅 Күнтізбе',
        'today_tasks': '📌 Бүгінгі тапсырмалар',
        'reports': '📊 Есептер',
        'notifications': '🔔 Хабарландырулар',
        'settings': '⚙️ Баптаулар',
        'help': '❓ Көмек',
        'back': '◀️ Артқа',
        'cancel': '❌ Болдырмау',
        'done': '✅ Дайын',
        'edit': '✏️ Өңдеу',
        'delete': '🗑 Жою',
        'language': '🌐 Тіл',
        'choose_language': '🌐 Тілді таңдаңыз:',
        'language_changed': '✅ Тіл сәтті өзгертілді!',
        'enter_task_title': '📝 Тапсырма атауын енгізіңіз:',
        'enter_task_desc': '📄 Тапсырма сипаттамасын енгізіңіз (немесе /skip):',
        'enter_deadline': '📅 Мерзімді енгізіңіз (күн.ай.жыл форматында немесе /skip):',
        'task_created': '✅ Тапсырма сәтті жасалды!',
        'no_tasks': '📭 Әзірше тапсырмалар жоқ',
        'select_task': '📋 Тапсырманы таңдаңыз:',
        'task_details': '📋 Тапсырма мәліметтері',
        'status': '📊 Мәртебесі',
        'priority': '⚡ Басымдық',
        'deadline': '📅 Мерзімі',
        'description': '📝 Сипаттама',
        'created_date': '🕐 Жасалған',
        'assigned_to': '👤 Жауапты',
        'change_status': '🔄 Мәртебені өзгерту',
        'change_priority': '⚡ Басымдықты өзгерту',
        'assign_user': '👤 Жауапты тағайындау',
        'task_updated': '✅ Тапсырма жаңартылды!',
        'task_deleted': '✅ Тапсырма жойылды!',
        'confirm_delete': '❓ Тапсырманы жоюды растайсыз ба?',
        'yes': '✅ Иә',
        'no': '❌ Жоқ',
        'search': '🔍 Іздеу',
        'filter': '🎯 Сүзгі',
        'sort': '↕️ Сұрыптау',
        'statistics': '📈 Статистика',
        'export': '📤 Экспорт',
        'import': '📥 Импорт',
        'profile': '👤 Профиль',
        'logout': '🚪 Шығу',
        'about': 'ℹ️ Бот туралы',
        'contact_admin': '💬 Әкімшімен байланыс',
        'rate_bot': '⭐ Ботты бағалау',
        'share': '📢 Бөлісу',
        'status_todo': '📝 Орындау керек',
        'status_in_progress': '🔄 Орындалуда',
        'status_review': '👀 Тексерілуде',
        'status_done': '✅ Орындалды',
        'status_cancelled': '❌ Болдырылмады',
        'priority_low': '🟢 Төмен',
        'priority_medium': '🟡 Орташа',
        'priority_high': '🔴 Жоғары',
        'priority_urgent': '🚨 Шұғыл',
        'daily_report': '📊 Күндік есеп',
        'weekly_report': '📊 Апталық есеп',
        'monthly_report': '📊 Айлық есеп',
        'no_projects': '📭 Жобалар жоқ',
        'project_created': '✅ Жоба жасалды!',
        'select_project': '📁 Жобаны таңдаңыз:',
        'project_details': '📁 Жоба мәліметтері',
        'add_to_project': '📎 Жобаға қосу',
        'remove_from_project': '📎 Жобадан шығару',
        'team_members': '👥 Топ мүшелері',
        'add_member': '➕ Мүше қосу',
        'remove_member': '➖ Мүшені шығару',
        'member_added': '✅ Мүше қосылды!',
        'member_removed': '✅ Мүше шығарылды!',
        'notifications_on': '🔔 Хабарландырулар қосулы',
        'notifications_off': '🔕 Хабарландырулар өшірулі',
        'reminder_set': '⏰ Еске салғыш орнатылды!',
        'search_results': '🔍 Іздеу нәтижелері',
        'no_results': '❌ Ештеңе табылмады',
        'loading': '⏳ Жүктелуде...',
        'error': '❌ Қате пайда болды!',
        'success': '✅ Сәтті!',
        'warning': '⚠️ Назар аударыңыз!',
        'info': 'ℹ️ Ақпарат',
        'confirm': '❓ Растайсыз ба?',
        'enter_project_name': '📝 Жоба атауын енгізіңіз:',
        'enter_project_desc': '📄 Жоба сипаттамасын енгізіңіз (немесе /skip):',
        'enter_team_name': '📝 Топ атауын енгізіңіз:',
        'enter_team_desc': '📄 Топ сипаттамасын енгізіңіз (немесе /skip):',
        'team_created': '✅ Топ жасалды!',
        'no_teams': '📭 Топтар жоқ',
        'select_team': '👥 Топты таңдаңыз:',
        'team_details': '👥 Топ мәліметтері',
        'feedback': '💬 Кері байланыс',
        'send_feedback': '📝 Пікіріңізді жіберіңіз:',
        'feedback_sent': '✅ Пікіріңіз жіберілді!',
        'quick_actions': '⚡ Жылдам әрекеттер',
        'mark_done': '✅ Орындалды деп белгілеу',
        'postpone': '⏰ Кейінге қалдыру',
        'duplicate': '📑 Көшіру',
        'archive': '📦 Мұрағаттау',
        'unarchive': '📤 Мұрағаттан шығару',
        'pin': '📌 Бекіту',
        'unpin': '📌 Бекітуден алу',
        'all_tasks': '📋 Барлық тапсырмалар',
        'my_created': '✏️ Мен жасағандар',
        'assigned_to_me': '👤 Маған тағайындалғандар',
        'high_priority': '🔴 Маңызды тапсырмалар',
        'overdue': '⏰ Мерзімі өткендер',
        'completed': '✅ Орындалғандар',
        'upcoming': '📅 Алдағылар',
        'today': '📌 Бүгін',
        'tomorrow': '📅 Ертең',
        'this_week': '📅 Осы апта',
        'next_week': '📅 Келесі апта',
        'this_month': '📅 Осы ай',
        'custom_date': '📅 Басқа күн'
    }
}

class DataManager:
    """Ma'lumotlar bazasi bilan ishlash"""
    
    def __init__(self):
        self.data = self.load_data()
    
    def load_data(self) -> dict:
        """Ma'lumotlarni yuklash"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'users': {},
            'tasks': {},
            'projects': {},
            'teams': {},
            'task_counter': 0,
            'project_counter': 0,
            'team_counter': 0
        }
    
    def save_data(self):
        """Ma'lumotlarni saqlash"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_user(self, user_id: int) -> dict:
        """Foydalanuvchi ma'lumotlarini olish"""
        user_id = str(user_id)
        if user_id not in self.data['users']:
            self.data['users'][user_id] = {
                'id': user_id,
                'tasks': [],
                'projects': [],
                'teams': [],
                'settings': {
                    'notifications': True,
                    'language': 'uz'  # Default til
                }
            }
            self.save_data()
        return self.data['users'][user_id]
    
    def get_user_language(self, user_id: int) -> str:
        """Foydalanuvchi tilini olish"""
        user = self.get_user(user_id)
        return user['settings'].get('language', 'uz')
    
    def set_user_language(self, user_id: int, language: str):
        """Foydalanuvchi tilini o'zgartirish"""
        user = self.get_user(user_id)
        user['settings']['language'] = language
        self.save_data()
    
    def create_task(self, user_id: int, title: str, description: str = None, 
                   deadline: str = None) -> str:
        """Yangi vazifa yaratish"""
        self.data['task_counter'] += 1
        task_id = f"TASK_{self.data['task_counter']:04d}"
        
        task = {
            'id': task_id,
            'title': title,
            'description': description,
            'status': TaskStatus.TODO.value,
            'priority': TaskPriority.MEDIUM.value,
            'created_by': str(user_id),
            'assigned_to': str(user_id),
            'created_date': datetime.now().isoformat(),
            'deadline': deadline,
            'project_id': None,
            'team_id': None,
            'completed': False,
            'archived': False,
            'pinned': False
        }
        
        self.data['tasks'][task_id] = task
        user = self.get_user(user_id)
        user['tasks'].append(task_id)
        self.save_data()
        
        return task_id
    
    def get_user_tasks(self, user_id: int, filter_type: str = 'all') -> List[dict]:
        """Foydalanuvchi vazifalarini olish"""
        user = self.get_user(user_id)
        tasks = []
        
        for task_id in user['tasks']:
            if task_id in self.data['tasks']:
                task = self.data['tasks'][task_id]
                
                # Filtrlash
                if filter_type == 'active' and task['status'] in [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]:
                    continue
                elif filter_type == 'completed' and task['status'] != TaskStatus.DONE.value:
                    continue
                elif filter_type == 'today':
                    if task['deadline']:
                        deadline_date = datetime.fromisoformat(task['deadline']).date()
                        if deadline_date != datetime.now().date():
                            continue
                    else:
                        continue
                elif filter_type == 'overdue':
                    if task['deadline'] and task['status'] != TaskStatus.DONE.value:
                        deadline_date = datetime.fromisoformat(task['deadline'])
                        if deadline_date >= datetime.now():
                            continue
                    else:
                        continue
                elif filter_type == 'high_priority' and task['priority'] not in [TaskPriority.HIGH.value, TaskPriority.URGENT.value]:
                    continue
                
                tasks.append(task)
        
        # Saralash: pinned > priority > deadline
        tasks.sort(key=lambda x: (
            not x.get('pinned', False),
            x['priority'] != TaskPriority.URGENT.value,
            x['priority'] != TaskPriority.HIGH.value,
            x['deadline'] or '9999-12-31'
        ))
        
        return tasks
    
    def update_task(self, task_id: str, **kwargs):
        """Vazifani yangilash"""
        if task_id in self.data['tasks']:
            self.data['tasks'][task_id].update(kwargs)
            self.save_data()
            return True
        return False
    
    def delete_task(self, task_id: str, user_id: int):
        """Vazifani o'chirish"""
        if task_id in self.data['tasks']:
            del self.data['tasks'][task_id]
            user = self.get_user(user_id)
            if task_id in user['tasks']:
                user['tasks'].remove(task_id)
            self.save_data()
            return True
        return False
    
    def create_project(self, user_id: int, name: str, description: str = None) -> str:
        """Yangi loyiha yaratish"""
        self.data['project_counter'] += 1
        project_id = f"PROJ_{self.data['project_counter']:04d}"
        
        project = {
            'id': project_id,
            'name': name,
            'description': description,
            'created_by': str(user_id),
            'created_date': datetime.now().isoformat(),
            'tasks': [],
            'members': [str(user_id)],
            'archived': False
        }
        
        self.data['projects'][project_id] = project
        user = self.get_user(user_id)
        user['projects'].append(project_id)
        self.save_data()
        
        return project_id
    
    def get_user_projects(self, user_id: int) -> List[dict]:
        """Foydalanuvchi loyihalarini olish"""
        user = self.get_user(user_id)
        projects = []
        
        for project_id in user['projects']:
            if project_id in self.data['projects']:
                projects.append(self.data['projects'][project_id])
        
        return projects
    
    def create_team(self, user_id: int, name: str, description: str = None) -> str:
        """Yangi jamoa yaratish"""
        self.data['team_counter'] += 1
        team_id = f"TEAM_{self.data['team_counter']:04d}"
        
        team = {
            'id': team_id,
            'name': name,
            'description': description,
            'created_by': str(user_id),
            'created_date': datetime.now().isoformat(),
            'members': [str(user_id)],
            'projects': [],
            'archived': False
        }
        
        self.data['teams'][team_id] = team
        user = self.get_user(user_id)
        user['teams'].append(team_id)
        self.save_data()
        
        return team_id
    
    def get_user_teams(self, user_id: int) -> List[dict]:
        """Foydalanuvchi jamoalarini olish"""
        user = self.get_user(user_id)
        teams = []
        
        for team_id in user['teams']:
            if team_id in self.data['teams']:
                teams.append(self.data['teams'][team_id])
        
        return teams

# Bot klassi
class TaskBot:
    def __init__(self, token: str):
        self.token = token
        self.db = DataManager()
        self.updater = Updater(token, use_context=True)
        self.dp = self.updater.dispatcher
        self.setup_handlers()
    
    def get_text(self, user_id: int, key: str) -> str:
        """Foydalanuvchi tiliga mos matnni olish"""
        lang = self.db.get_user_language(user_id)
        return LANGUAGES[lang].get(key, key)
    
    def get_main_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Asosiy klaviatura"""
        t = lambda key: self.get_text(user_id, key)
        
        keyboard = [
            [t('my_tasks'), t('new_task')],
            [t('projects'), t('teams')],
            [t('today_tasks'), t('calendar')],
            [t('reports'), t('settings')]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_task_filter_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Vazifalar filtri uchun inline klaviatura"""
        t = lambda key: self.get_text(user_id, key)
        
        keyboard = [
            [
                InlineKeyboardButton(t('all_tasks'), callback_data='filter_all'),
                InlineKeyboardButton(t('today'), callback_data='filter_today')
            ],
            [
                InlineKeyboardButton(t('high_priority'), callback_data='filter_high'),
                InlineKeyboardButton(t('overdue'), callback_data='filter_overdue')
            ],
            [
                InlineKeyboardButton(t('completed'), callback_data='filter_completed'),
                InlineKeyboardButton(t('upcoming'), callback_data='filter_upcoming')
            ],
            [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_task_actions_keyboard(self, user_id: int, task_id: str) -> InlineKeyboardMarkup:
        """Vazifa amallari uchun inline klaviatura"""
        t = lambda key: self.get_text(user_id, key)
        task = self.db.data['tasks'].get(task_id, {})
        
        keyboard = []
        
        # Status o'zgartirish
        status_buttons = []
        if task.get('status') != TaskStatus.DONE.value:
            status_buttons.append(InlineKeyboardButton(t('mark_done'), callback_data=f'task_done_{task_id}'))
        status_buttons.append(InlineKeyboardButton(t('change_status'), callback_data=f'task_status_{task_id}'))
        keyboard.append(status_buttons)
        
        # Priority va boshqa amallar
        keyboard.append([
            InlineKeyboardButton(t('change_priority'), callback_data=f'task_priority_{task_id}'),
            InlineKeyboardButton(t('edit'), callback_data=f'task_edit_{task_id}')
        ])
        
        # Pin/Unpin va Archive
        pin_archive = []
        if task.get('pinned'):
            pin_archive.append(InlineKeyboardButton(t('unpin'), callback_data=f'task_unpin_{task_id}'))
        else:
            pin_archive.append(InlineKeyboardButton(t('pin'), callback_data=f'task_pin_{task_id}'))
        
        if task.get('archived'):
            pin_archive.append(InlineKeyboardButton(t('unarchive'), callback_data=f'task_unarchive_{task_id}'))
        else:
            pin_archive.append(InlineKeyboardButton(t('archive'), callback_data=f'task_archive_{task_id}'))
        keyboard.append(pin_archive)
        
        # Duplicate va Delete
        keyboard.append([
            InlineKeyboardButton(t('duplicate'), callback_data=f'task_duplicate_{task_id}'),
            InlineKeyboardButton(t('delete'), callback_data=f'task_delete_{task_id}')
        ])
        
        # Orqaga
        keyboard.append([InlineKeyboardButton(t('back'), callback_data='my_tasks')])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_status_keyboard(self, user_id: int, task_id: str) -> InlineKeyboardMarkup:
        """Status tanlash uchun klaviatura"""
        t = lambda key: self.get_text(user_id, key)
        
        keyboard = [
            [InlineKeyboardButton(t('status_todo'), callback_data=f'set_status_{task_id}_{TaskStatus.TODO.value}')],
            [InlineKeyboardButton(t('status_in_progress'), callback_data=f'set_status_{task_id}_{TaskStatus.IN_PROGRESS.value}')],
            [InlineKeyboardButton(t('status_review'), callback_data=f'set_status_{task_id}_{TaskStatus.REVIEW.value}')],
            [InlineKeyboardButton(t('status_done'), callback_data=f'set_status_{task_id}_{TaskStatus.DONE.value}')],
            [InlineKeyboardButton(t('status_cancelled'), callback_data=f'set_status_{task_id}_{TaskStatus.CANCELLED.value}')],
            [InlineKeyboardButton(t('back'), callback_data=f'task_view_{task_id}')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_priority_keyboard(self, user_id: int, task_id: str) -> InlineKeyboardMarkup:
        """Priority tanlash uchun klaviatura"""
        t = lambda key: self.get_text(user_id, key)
        
        keyboard = [
            [InlineKeyboardButton(t('priority_low'), callback_data=f'set_priority_{task_id}_{TaskPriority.LOW.value}')],
            [InlineKeyboardButton(t('priority_medium'), callback_data=f'set_priority_{task_id}_{TaskPriority.MEDIUM.value}')],
            [InlineKeyboardButton(t('priority_high'), callback_data=f'set_priority_{task_id}_{TaskPriority.HIGH.value}')],
            [InlineKeyboardButton(t('priority_urgent'), callback_data=f'set_priority_{task_id}_{TaskPriority.URGENT.value}')],
            [InlineKeyboardButton(t('back'), callback_data=f'task_view_{task_id}')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_settings_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Sozlamalar uchun klaviatura"""
        t = lambda key: self.get_text(user_id, key)
        user = self.db.get_user(user_id)
        notif_status = t('notifications_on') if user['settings']['notifications'] else t('notifications_off')
        
        keyboard = [
            [InlineKeyboardButton(f"{t('language')}: {LANGUAGES[user['settings']['language']]['flag']}", 
                                 callback_data='change_language')],
            [InlineKeyboardButton(notif_status, callback_data='toggle_notifications')],
            [InlineKeyboardButton(t('profile'), callback_data='view_profile')],
            [InlineKeyboardButton(t('feedback'), callback_data='send_feedback')],
            [InlineKeyboardButton(t('about'), callback_data='about_bot')],
            [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_language_keyboard(self) -> InlineKeyboardMarkup:
        """Til tanlash uchun klaviatura"""
        keyboard = [
            [InlineKeyboardButton(lang_data['name'], callback_data=f'set_lang_{lang_code}')]
            for lang_code, lang_data in LANGUAGES.items()
        ]
        keyboard.append([InlineKeyboardButton('◀️', callback_data='settings')])
        
        return InlineKeyboardMarkup(keyboard)
    
    def format_task(self, task: dict, user_id: int, detailed: bool = False) -> str:
        """Vazifani formatlash"""
        t = lambda key: self.get_text(user_id, key)
        
        # Status va priority iconkalari
        status_icons = {
            TaskStatus.TODO.value: t('status_todo'),
            TaskStatus.IN_PROGRESS.value: t('status_in_progress'),
            TaskStatus.REVIEW.value: t('status_review'),
            TaskStatus.DONE.value: t('status_done'),
            TaskStatus.CANCELLED.value: t('status_cancelled')
        }
        
        priority_icons = {
            TaskPriority.LOW.value: t('priority_low'),
            TaskPriority.MEDIUM.value: t('priority_medium'),
            TaskPriority.HIGH.value: t('priority_high'),
            TaskPriority.URGENT.value: t('priority_urgent')
        }
        
        # Asosiy ma'lumotlar
        text = f"📋 <b>{task['title']}</b>\n"
        
        if task.get('pinned'):
            text = "📌 " + text
        
        text += f"\n{t('status')}: {status_icons.get(task['status'], task['status'])}\n"
        text += f"{t('priority')}: {priority_icons.get(task['priority'], task['priority'])}\n"
        
        if task.get('deadline'):
            deadline = datetime.fromisoformat(task['deadline'])
            days_left = (deadline - datetime.now()).days
            
            if days_left < 0:
                text += f"{t('deadline')}: <b>⏰ {abs(days_left)} kun o'tib ketdi!</b>\n"
            elif days_left == 0:
                text += f"{t('deadline')}: <b>📅 Bugun!</b>\n"
            elif days_left == 1:
                text += f"{t('deadline')}: <b>📅 Ertaga</b>\n"
            else:
                text += f"{t('deadline')}: 📅 {deadline.strftime('%d.%m.%Y')} ({days_left} kun qoldi)\n"
        
        if detailed:
            if task.get('description'):
                text += f"\n{t('description')}:\n{task['description']}\n"
            
            created_date = datetime.fromisoformat(task['created_date'])
            text += f"\n{t('created_date')}: {created_date.strftime('%d.%m.%Y %H:%M')}\n"
            
            if task.get('project_id'):
                project = self.db.data['projects'].get(task['project_id'])
                if project:
                    text += f"📁 {t('projects')}: {project['name']}\n"
            
            if task.get('team_id'):
                team = self.db.data['teams'].get(task['team_id'])
                if team:
                    text += f"👥 {t('teams')}: {team['name']}\n"
        
        return text
    
    # Handler metodlari
    def start_handler(self, update: Update, context: CallbackContext):
        """Start komandasi"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        welcome_text = self.get_text(user_id, 'welcome')
        update.message.reply_text(
            welcome_text,
            reply_markup=self.get_main_keyboard(user_id),
            parse_mode=ParseMode.HTML
        )
    
    def help_handler(self, update: Update, context: CallbackContext):
        """Yordam komandasi"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        help_text = f"""
{t('help')} <b>Task Management Bot</b>

<b>Asosiy komandalar:</b>
/start - Botni ishga tushirish
/help - Yordam
/newtask - Yangi vazifa yaratish
/mytasks - Vazifalarim
/newproject - Yangi loyiha
/projects - Loyihalar
/newteam - Yangi jamoa
/teams - Jamoalar
/today - Bugungi vazifalar
/report - Hisobot
/settings - Sozlamalar
/feedback - Fikr bildirish

<b>Qo'shimcha:</b>
• Barcha funksiyalar tugmalar orqali ham mavjud
• Vazifalarni pinlash, arxivlash mumkin
• 3 tilda ishlaydi: O'zbek, Rus, Qozoq
• Deadline eslatmalari avtomatik yuboriladi
        """
        
        update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    def text_handler(self, update: Update, context: CallbackContext):
        """Matnli xabarlarni qayta ishlash"""
        user_id = update.effective_user.id
        text = update.message.text
        t = lambda key: self.get_text(user_id, key)
        
        # Tugma bosilganda
        if text == t('my_tasks'):
            self.show_tasks(update, context)
        elif text == t('new_task'):
            self.new_task_start(update, context)
        elif text == t('projects'):
            self.show_projects(update, context)
        elif text == t('teams'):
            self.show_teams(update, context)
        elif text == t('today_tasks'):
            self.show_today_tasks(update, context)
        elif text == t('calendar'):
            self.show_calendar(update, context)
        elif text == t('reports'):
            self.show_reports_menu(update, context)
        elif text == t('settings'):
            self.show_settings(update, context)
        else:
            update.message.reply_text(
                t('choose_action'),
                reply_markup=self.get_main_keyboard(user_id)
            )
    
    def show_tasks(self, update: Update, context: CallbackContext, filter_type: str = 'all'):
        """Vazifalarni ko'rsatish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        tasks = self.db.get_user_tasks(user_id, filter_type)
        
        if not tasks:
            text = t('no_tasks')
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(t('new_task'), callback_data='new_task')],
                [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
            ])
        else:
            text = f"<b>{t('my_tasks')}</b>\n\n"
            keyboard_buttons = []
            
            for task in tasks[:10]:  # Maksimum 10 ta vazifa
                task_text = task['title']
                if task.get('pinned'):
                    task_text = "📌 " + task_text
                if task['status'] == TaskStatus.DONE.value:
                    task_text = "✅ " + task_text
                elif task['priority'] == TaskPriority.URGENT.value:
                    task_text = "🚨 " + task_text
                elif task['priority'] == TaskPriority.HIGH.value:
                    task_text = "🔴 " + task_text
                
                keyboard_buttons.append([
                    InlineKeyboardButton(task_text, callback_data=f"task_view_{task['id']}")
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(t('filter'), callback_data='task_filter'),
                InlineKeyboardButton(t('new_task'), callback_data='new_task')
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(t('back'), callback_data='back_to_menu')
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            # Statistika
            total = len(tasks)
            completed = len([t for t in tasks if t['status'] == TaskStatus.DONE.value])
            in_progress = len([t for t in tasks if t['status'] == TaskStatus.IN_PROGRESS.value])
            
            text += f"📊 {t('statistics')}:\n"
            text += f"• Jami: {total}\n"
            text += f"• {t('completed')}: {completed}\n"
            text += f"• {t('status_in_progress')}: {in_progress}\n"
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    
    def new_task_start(self, update: Update, context: CallbackContext) -> int:
        """Yangi vazifa yaratishni boshlash"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        cancel_keyboard = ReplyKeyboardMarkup(
            [[t('cancel')]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        if update.callback_query:
            update.callback_query.answer()
            update.callback_query.message.reply_text(
                t('enter_task_title'),
                reply_markup=cancel_keyboard
            )
        else:
            update.message.reply_text(
                t('enter_task_title'),
                reply_markup=cancel_keyboard
            )
        
        return WAITING_TASK_TITLE
    
    def task_title_received(self, update: Update, context: CallbackContext) -> int:
        """Vazifa nomini qabul qilish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        if update.message.text == t('cancel'):
            update.message.reply_text(
                t('choose_action'),
                reply_markup=self.get_main_keyboard(user_id)
            )
            return ConversationHandler.END
        
        context.user_data['task_title'] = update.message.text
        
        skip_keyboard = ReplyKeyboardMarkup(
            [['/skip'], [t('cancel')]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        update.message.reply_text(
            t('enter_task_desc'),
            reply_markup=skip_keyboard
        )
        
        return WAITING_TASK_DESC
    
    def task_desc_received(self, update: Update, context: CallbackContext) -> int:
        """Vazifa tavsifini qabul qilish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        if update.message.text == t('cancel'):
            update.message.reply_text(
                t('choose_action'),
                reply_markup=self.get_main_keyboard(user_id)
            )
            return ConversationHandler.END
        
        if update.message.text != '/skip':
            context.user_data['task_desc'] = update.message.text
        else:
            context.user_data['task_desc'] = None
        
        skip_keyboard = ReplyKeyboardMarkup(
            [['/skip'], [t('cancel')]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        update.message.reply_text(
            t('enter_deadline') + "\n(Masalan: 25.12.2024)",
            reply_markup=skip_keyboard
        )
        
        return WAITING_TASK_DEADLINE
    
    def task_deadline_received(self, update: Update, context: CallbackContext) -> int:
        """Vazifa muddatini qabul qilish va yaratish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        if update.message.text == t('cancel'):
            update.message.reply_text(
                t('choose_action'),
                reply_markup=self.get_main_keyboard(user_id)
            )
            return ConversationHandler.END
        
        deadline = None
        if update.message.text != '/skip':
            try:
                # DD.MM.YYYY formatidan datetime'ga o'tkazish
                deadline_date = datetime.strptime(update.message.text, '%d.%m.%Y')
                deadline = deadline_date.isoformat()
            except ValueError:
                update.message.reply_text(
                    "❌ Noto'g'ri format! Iltimos, DD.MM.YYYY formatida kiriting.\nMasalan: 25.12.2024"
                )
                return WAITING_TASK_DEADLINE
        
        # Vazifani yaratish
        task_id = self.db.create_task(
            user_id=user_id,
            title=context.user_data['task_title'],
            description=context.user_data.get('task_desc'),
            deadline=deadline
        )
        
        task = self.db.data['tasks'][task_id]
        task_text = self.format_task(task, user_id, detailed=True)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t('change_priority'), callback_data=f'task_priority_{task_id}'),
                InlineKeyboardButton(t('assign_user'), callback_data=f'task_assign_{task_id}')
            ],
            [
                InlineKeyboardButton(t('add_to_project'), callback_data=f'task_to_project_{task_id}'),
                InlineKeyboardButton(t('my_tasks'), callback_data='my_tasks')
            ]
        ])
        
        update.message.reply_text(
            f"{t('task_created')}\n\n{task_text}",
            reply_markup=self.get_main_keyboard(user_id),
            parse_mode=ParseMode.HTML
        )
        
        update.message.reply_text(
            t('quick_actions'),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        
        # Context'ni tozalash
        context.user_data.clear()
        
        return ConversationHandler.END
    
    def callback_handler(self, update: Update, context: CallbackContext):
        """Callback query handler"""
        query = update.callback_query
        user_id = query.from_user.id
        t = lambda key: self.get_text(user_id, key)
        
        query.answer()
        
        # Til o'zgartirish
        if query.data.startswith('set_lang_'):
            lang = query.data.replace('set_lang_', '')
            self.db.set_user_language(user_id, lang)
            query.edit_message_text(
                self.get_text(user_id, 'language_changed'),
                reply_markup=self.get_settings_keyboard(user_id)
            )
        
        # Til menyusi
        elif query.data == 'change_language':
            query.edit_message_text(
                t('choose_language'),
                reply_markup=self.get_language_keyboard()
            )
        
        # Sozlamalar
        elif query.data == 'settings':
            self.show_settings_inline(query, user_id)
        
        # Vazifalar
        elif query.data == 'my_tasks':
            self.show_tasks(update, context)
        
        # Yangi vazifa
        elif query.data == 'new_task':
            self.new_task_start(update, context)
        
        # Vazifani ko'rish
        elif query.data.startswith('task_view_'):
            task_id = query.data.replace('task_view_', '')
            self.show_task_details(query, user_id, task_id)
        
        # Vazifa statusini o'zgartirish
        elif query.data.startswith('task_status_'):
            task_id = query.data.replace('task_status_', '')
            query.edit_message_reply_markup(
                reply_markup=self.get_status_keyboard(user_id, task_id)
            )
        
        # Statusni o'rnatish
        elif query.data.startswith('set_status_'):
            parts = query.data.split('_')
            task_id = parts[2]
            status = parts[3]
            self.db.update_task(task_id, status=status)
            query.answer(t('task_updated'))
            self.show_task_details(query, user_id, task_id)
        
        # Vazifa prioritetini o'zgartirish
        elif query.data.startswith('task_priority_'):
            task_id = query.data.replace('task_priority_', '')
            query.edit_message_reply_markup(
                reply_markup=self.get_priority_keyboard(user_id, task_id)
            )
        
        # Prioritetni o'rnatish
        elif query.data.startswith('set_priority_'):
            parts = query.data.split('_')
            task_id = parts[2]
            priority = parts[3]
            self.db.update_task(task_id, priority=priority)
            query.answer(t('task_updated'))
            self.show_task_details(query, user_id, task_id)
        
        # Vazifani bajarildi deb belgilash
        elif query.data.startswith('task_done_'):
            task_id = query.data.replace('task_done_', '')
            self.db.update_task(task_id, status=TaskStatus.DONE.value)
            query.answer(t('task_updated'))
            self.show_task_details(query, user_id, task_id)
        
        # Vazifani pinlash
        elif query.data.startswith('task_pin_'):
            task_id = query.data.replace('task_pin_', '')
            self.db.update_task(task_id, pinned=True)
            query.answer('📌 ' + t('success'))
            self.show_task_details(query, user_id, task_id)
        
        # Vazifani unpinlash
        elif query.data.startswith('task_unpin_'):
            task_id = query.data.replace('task_unpin_', '')
            self.db.update_task(task_id, pinned=False)
            query.answer(t('success'))
            self.show_task_details(query, user_id, task_id)
        
        # Vazifani arxivlash
        elif query.data.startswith('task_archive_'):
            task_id = query.data.replace('task_archive_', '')
            self.db.update_task(task_id, archived=True)
            query.answer('📦 ' + t('success'))
            self.show_tasks(update, context)
        
        # Vazifani arxivdan chiqarish
        elif query.data.startswith('task_unarchive_'):
            task_id = query.data.replace('task_unarchive_', '')
            self.db.update_task(task_id, archived=False)
            query.answer(t('success'))
            self.show_task_details(query, user_id, task_id)
        
        # Vazifani nusxalash
        elif query.data.startswith('task_duplicate_'):
            task_id = query.data.replace('task_duplicate_', '')
            original_task = self.db.data['tasks'].get(task_id)
            if original_task:
                new_task_id = self.db.create_task(
                    user_id=user_id,
                    title=original_task['title'] + " (nusxa)",
                    description=original_task.get('description'),
                    deadline=original_task.get('deadline')
                )
                query.answer(t('success'))
                self.show_task_details(query, user_id, new_task_id)
        
        # Vazifani o'chirish tasdiqlash
        elif query.data.startswith('task_delete_'):
            task_id = query.data.replace('task_delete_', '')
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(t('yes'), callback_data=f'confirm_delete_{task_id}'),
                    InlineKeyboardButton(t('no'), callback_data=f'task_view_{task_id}')
                ]
            ])
            query.edit_message_text(
                t('confirm_delete'),
                reply_markup=keyboard
            )
        
        # O'chirishni tasdiqlash
        elif query.data.startswith('confirm_delete_'):
            task_id = query.data.replace('confirm_delete_', '')
            self.db.delete_task(task_id, user_id)
            query.answer(t('task_deleted'))
            self.show_tasks(update, context)
        
        # Filtr
        elif query.data == 'task_filter':
            query.edit_message_reply_markup(
                reply_markup=self.get_task_filter_keyboard(user_id)
            )
        
        # Filtr turlari
        elif query.data.startswith('filter_'):
            filter_type = query.data.replace('filter_', '')
            self.show_tasks(update, context, filter_type)
        
        # Bildirishnomalarni yoqish/o'chirish
        elif query.data == 'toggle_notifications':
            user = self.db.get_user(user_id)
            user['settings']['notifications'] = not user['settings']['notifications']
            self.db.save_data()
            query.answer(t('success'))
            self.show_settings_inline(query, user_id)
        
        # Profil
        elif query.data == 'view_profile':
            self.show_profile(query, user_id)
        
        # Bot haqida
        elif query.data == 'about_bot':
            self.show_about(query, user_id)
        
        # Fikr bildirish
        elif query.data == 'send_feedback':
            query.message.reply_text(t('send_feedback'))
            return WAITING_FEEDBACK
        
        # Asosiy menyuga qaytish
        elif query.data == 'back_to_menu':
            query.edit_message_text(
                t('choose_action'),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(t('my_tasks'), callback_data='my_tasks'),
                        InlineKeyboardButton(t('new_task'), callback_data='new_task')
                    ],
                    [
                        InlineKeyboardButton(t('projects'), callback_data='projects'),
                        InlineKeyboardButton(t('teams'), callback_data='teams')
                    ],
                    [
                        InlineKeyboardButton(t('reports'), callback_data='reports'),
                        InlineKeyboardButton(t('settings'), callback_data='settings')
                    ]
                ])
            )
    
    def show_task_details(self, query: CallbackQuery, user_id: int, task_id: str):
        """Vazifa tafsilotlarini ko'rsatish"""
        t = lambda key: self.get_text(user_id, key)
        task = self.db.data['tasks'].get(task_id)
        
        if not task:
            query.answer(t('error'))
            return
        
        task_text = self.format_task(task, user_id, detailed=True)
        keyboard = self.get_task_actions_keyboard(user_id, task_id)
        
        query.edit_message_text(
            task_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    def show_settings(self, update: Update, context: CallbackContext):
        """Sozlamalar menyusi"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        text = f"⚙️ <b>{t('settings')}</b>"
        keyboard = self.get_settings_keyboard(user_id)
        
        update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    def show_settings_inline(self, query: CallbackQuery, user_id: int):
        """Inline sozlamalar menyusi"""
        t = lambda key: self.get_text(user_id, key)
        
        text = f"⚙️ <b>{t('settings')}</b>"
        keyboard = self.get_settings_keyboard(user_id)
        
        query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    def show_profile(self, query: CallbackQuery, user_id: int):
        """Foydalanuvchi profilini ko'rsatish"""
        t = lambda key: self.get_text(user_id, key)
        user = self.db.get_user(user_id)
        
        # Statistika
        all_tasks = self.db.get_user_tasks(user_id)
        completed_tasks = [t for t in all_tasks if t['status'] == TaskStatus.DONE.value]
        active_tasks = [t for t in all_tasks if t['status'] not in [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]]
        
        text = f"""
👤 <b>{t('profile')}</b>

🆔 User ID: <code>{user_id}</code>
🌐 {t('language')}: {LANGUAGES[user['settings']['language']]['name']}
🔔 {t('notifications')}: {'✅' if user['settings']['notifications'] else '❌'}

📊 <b>{t('statistics')}:</b>
• {t('all_tasks')}: {len(all_tasks)}
• {t('completed')}: {len(completed_tasks)}
• Faol vazifalar: {len(active_tasks)}
• {t('projects')}: {len(user['projects'])}
• {t('teams')}: {len(user['teams'])}
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t('back'), callback_data='settings')]
        ])
        
        query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    def show_about(self, query: CallbackQuery, user_id: int):
        """Bot haqida ma'lumot"""
        t = lambda key: self.get_text(user_id, key)
        
        text = f"""
ℹ️ <b>{t('about')}</b>

🤖 <b>Task Management Bot</b>
Version: 2.0

Bu bot sizga vazifalar, loyihalar va jamoalarni 
boshqarishda yordam beradi.

✨ <b>Imkoniyatlar:</b>
• Vazifalarni yaratish va boshqarish
• Loyihalar bilan ishlash
• Jamoa a'zolari bilan hamkorlik
• Deadline eslatmalari
• Hisobotlar va statistika
• 3 tilda interfeys

💬 Savollar bo'lsa: @your_support_bot
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t('rate_bot'), url='https://t.me/your_bot?start=rate'),
                InlineKeyboardButton(t('share'), switch_inline_query='Check out this awesome Task Bot!')
            ],
            [InlineKeyboardButton(t('back'), callback_data='settings')]
        ])
        
        query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    def show_projects(self, update: Update, context: CallbackContext):
        """Loyihalarni ko'rsatish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        projects = self.db.get_user_projects(user_id)
        
        if not projects:
            text = f"📁 <b>{t('projects')}</b>\n\n{t('no_projects')}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(t('new_project'), callback_data='new_project')],
                [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
            ])
        else:
            text = f"📁 <b>{t('projects')}</b>\n\n"
            keyboard_buttons = []
            
            for project in projects:
                task_count = len(project.get('tasks', []))
                member_count = len(project.get('members', []))
                button_text = f"{project['name']} ({task_count} vazifa, {member_count} a'zo)"
                keyboard_buttons.append([
                    InlineKeyboardButton(button_text, callback_data=f"project_view_{project['id']}")
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(t('new_project'), callback_data='new_project')
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(t('back'), callback_data='back_to_menu')
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    
    def show_teams(self, update: Update, context: CallbackContext):
        """Jamoalarni ko'rsatish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        teams = self.db.get_user_teams(user_id)
        
        if not teams:
            text = f"👥 <b>{t('teams')}</b>\n\n{t('no_teams')}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(t('new_team'), callback_data='new_team')],
                [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
            ])
        else:
            text = f"👥 <b>{t('teams')}</b>\n\n"
            keyboard_buttons = []
            
            for team in teams:
                member_count = len(team.get('members', []))
                project_count = len(team.get('projects', []))
                button_text = f"{team['name']} ({member_count} a'zo, {project_count} loyiha)"
                keyboard_buttons.append([
                    InlineKeyboardButton(button_text, callback_data=f"team_view_{team['id']}")
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(t('new_team'), callback_data='new_team')
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(t('back'), callback_data='back_to_menu')
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    
    def show_today_tasks(self, update: Update, context: CallbackContext):
        """Bugungi vazifalarni ko'rsatish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        tasks = self.db.get_user_tasks(user_id, 'today')
        
        if not tasks:
            text = f"📌 <b>{t('today_tasks')}</b>\n\n{t('no_tasks')}"
        else:
            text = f"📌 <b>{t('today_tasks')}</b>\n\n"
            for i, task in enumerate(tasks, 1):
                status_emoji = '✅' if task['status'] == TaskStatus.DONE.value else '⏳'
                text += f"{i}. {status_emoji} {task['title']}\n"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t('all_tasks'), callback_data='my_tasks'),
                InlineKeyboardButton(t('new_task'), callback_data='new_task')
            ],
            [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
        ])
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    
    def show_calendar(self, update: Update, context: CallbackContext):
        """Kalendar ko'rsatish"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        # Haftaning kunlari bo'yicha vazifalar
        today = datetime.now().date()
        week_tasks = {}
        
        for i in range(7):
            date = today + timedelta(days=i)
            week_tasks[date] = []
        
        all_tasks = self.db.get_user_tasks(user_id)
        for task in all_tasks:
            if task.get('deadline') and task['status'] != TaskStatus.DONE.value:
                deadline_date = datetime.fromisoformat(task['deadline']).date()
                if deadline_date in week_tasks:
                    week_tasks[deadline_date].append(task)
        
        text = f"📅 <b>{t('calendar')}</b>\n\n"
        
        for date, tasks in week_tasks.items():
            if date == today:
                day_name = t('today')
            elif date == today + timedelta(days=1):
                day_name = t('tomorrow')
            else:
                day_name = date.strftime('%A')
            
            text += f"<b>{day_name} ({date.strftime('%d.%m')})</b>\n"
            if tasks:
                for task in tasks:
                    priority_emoji = '🔴' if task['priority'] in [TaskPriority.HIGH.value, TaskPriority.URGENT.value] else '⚪'
                    text += f"  {priority_emoji} {task['title']}\n"
            else:
                text += f"  {t('no_tasks')}\n"
            text += "\n"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t('today_tasks'), callback_data='today_tasks'),
                InlineKeyboardButton(t('all_tasks'), callback_data='my_tasks')
            ],
            [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
        ])
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    
    def show_reports_menu(self, update: Update, context: CallbackContext):
        """Hisobotlar menyusi"""
        user_id = update.effective_user.id
        t = lambda key: self.get_text(user_id, key)
        
        text = f"📊 <b>{t('reports')}</b>\n\n{t('choose_action')}:"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t('daily_report'), callback_data='report_daily')],
            [InlineKeyboardButton(t('weekly_report'), callback_data='report_weekly')],
            [InlineKeyboardButton(t('monthly_report'), callback_data='report_monthly')],
            [
                InlineKeyboardButton(t('export'), callback_data='export_data'),
                InlineKeyboardButton(t('statistics'), callback_data='show_stats')
            ],
            [InlineKeyboardButton(t('back'), callback_data='back_to_menu')]
        ])
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    
    def setup_handlers(self):
        """Handlerlarni sozlash"""
        # Komandalar
        self.dp.add_handler(CommandHandler('start', self.start_handler))
        self.dp.add_handler(CommandHandler('help', self.help_handler))
        
        # Yangi vazifa conversation
        task_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('newtask', self.new_task_start),
                CallbackQueryHandler(self.new_task_start, pattern='^new_task$')
            ],
            states={
                WAITING_TASK_TITLE: [MessageHandler(Filters.text & ~Filters.command, self.task_title_received)],
                WAITING_TASK_DESC: [MessageHandler(Filters.text & ~Filters.command, self.task_desc_received)],
                WAITING_TASK_DEADLINE: [MessageHandler(Filters.text & ~Filters.command, self.task_deadline_received)]
            },
            fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
        )
        self.dp.add_handler(task_conv_handler)
        
        # Callback queries
        self.dp.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Matnli xabarlar
        self.dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.text_handler))
    
    def run(self):
        """Botni ishga tushirish"""
        logger.info("Bot ishga tushmoqda...")
        self.updater.start_polling()
        self.updater.idle()


# Asosiy qism
if __name__ == '__main__':
    # Bot tokenini o'rnating
    TOKEN = "YOUR_BOT_TOKEN_HERE"  # BotFather'dan olingan token
    
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ Iltimos, bot tokenini kiriting!")
        print("1. Telegram'da @BotFather'ga yozing")
        print("2. /newbot komandasi bilan yangi bot yarating")
        print("3. Olingan tokenni TOKEN o'zgaruvchisiga yozing")
    else:
        bot = TaskBot(TOKEN)
        bot.run()
