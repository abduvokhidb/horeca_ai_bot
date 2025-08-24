# languages.py
STRINGS = {
    "uz": {
        "welcome_manager": "Assalomu alaykum! Bu menejer paneli. Vazifalarni bering, holatni kuzating, hisobotlarni oling.",
        "welcome_employee": "Assalomu alaykum! Bu sizning shaxsiy ish panelingiz.",
        "only_manager": "Kechirasiz, bu bo‘lim faqat menejerlar uchun.",
        "unknown_command": "Tushunarsiz buyruq. Tugmalardan foydalaning.",
        "help_text": "Buyruqlar: /start, /task, /status, /report, /mytasks, /done",
        "language_set": "Til o‘rnatildi: {lang}",

        # Hints / Podskazka
        "hint_pick_language": "Podskazka: quyida foydalanish tilini tanlang.",
        "hint_welcome_new": "Podskazka: ro‘yxatdan o‘tish uchun 'Ruyxatdan o‘tish' tugmasini bosing.",
        "hint_task_format": "Podskazka: sana/vaqt formati — HH:MM DD.MM.YYYY",
        "hint_attach": "Podskazka: /attach <task_id> yuboring, so‘ng faylni jo‘nating.",
        "hint_chat": "Podskazka: Chat bo‘limida xabar yuboring, admin javob beradi.",
        "hint_settings": "Podskazka: Sozlamalarda til, ism va telefonni yangilashingiz mumkin.",

        # Main labels (reply keyboard)
        "lbl_assign": "📝 Vazifa berish",
        "lbl_employees": "👤 Hodimlar",
        "lbl_dashboard": "📊 Dashboard",
        "lbl_reports": "🧾 Hisobotlar",
        "lbl_requests": "📨 So‘rovlar",
        "lbl_settings": "⚙️ Sozlamalar",
        "lbl_chat": "💬 Chat",
        "lbl_ai": "🤖 AI yordamchi",

        # Employee home
        "lbl_my_tasks": "✅ Mening vazifalarim",
        "lbl_send_report": "🧾 Hisobot",
        "lbl_back": "◀️ Orqaga",
        "lbl_change_lang": "🌐 Tilni o‘zgartirish",
        "lbl_change_name": "📝 Ismni o‘zgartirish",
        "lbl_change_phone": "📞 Telefonni o‘zgartirish",
        "lbl_register": "🆕 Ro‘yxatdan o‘tish",

        # Employees
        "employees_title": "Hodimlar bo‘limi:",
        "employees_list_header": "Faol hodimlar:",
        "employees_list_line": "• @{username} — {full_name}",
        "emp_add_hint": "Hodim qo‘shish uchun @username yuboring (masalan, @ali).",
        "emp_remove_hint": "O‘chirish uchun ham @username yuboring.",
        "invite_created": "Taklif havolasi @{username} uchun:\n{link}",

        # Invites / Requests
        "invites_title": "Invite so‘rovlari:",
        "invites_empty": "So‘rovlar yo‘q.",
        "btn_invite_accept": "✅ Qabul qilish",
        "btn_invite_reject": "❌ Rad etish",
        "invite_accept_ok": "✅ Tasdiqlandi.",
        "invite_reject_ok": "❌ Rad etildi.",

        # Tasks
        "task_assigned": "Yangi vazifa: {title}\nMuddat: {deadline}\nUstuvorlik: {priority}",
        "task_created": "✅ Vazifa yaratildi (ID: {task_id}).",
        "your_tasks_header": "Sizning vazifalaringiz:",
        "no_tasks": "Hozircha vazifalar yo‘q.",
        "done_usage": "Foydalanish: /done <task_id>",
        "done_ok": "✅ #{task_id} vazifasi bajarildi!",
        "done_fail": "❌ #{task_id} topilmadi yoki sizga tegishli emas.",
        "deadline_soon": "⏳ Eslatma: #{task_id} \"{title}\" vazifasining muddati yaqinlashmoqda ({deadline}).",

        # Reports / Dashboard
        "manager_status_header": "Xodimlar holati:",
        "report_prompt": "Bugungi hisobotni yuboring (qisqacha).",
        "reminder_morning": "⏰ 9:00 eslatma: vazifalaringizni ko‘rib chiqing.",
        "reminder_evening": "⏰ 18:00 eslatma: bugungi hisobotni yuboring.",

        # Settings
        "settings_title": "Sozlamalar:",
        "ask_new_name": "Yangi ismni kiriting:",
        "ask_new_phone": "Iltimos, kontaktingizni yuboring yoki raqamni kiriting:",
        "profile_saved": "✅ Profil yangilandi.",
        "choose_language": "Tilni tanlang:",
    },
    "ru": {
        "welcome_manager": "Здравствуйте! Панель менеджера: назначайте задачи, следите за статусом, получайте отчёты.",
        "welcome_employee": "Здравствуйте! Это ваша личная рабочая панель.",
        "only_manager": "Извините, этот раздел только для менеджеров.",
        "unknown_command": "Неизвестная команда. Используйте кнопки.",
        "help_text": "Команды: /start, /task, /status, /report, /mytasks, /done",
        "language_set": "Язык установлен: {lang}",

        "hint_pick_language": "Подсказка: выберите язык ниже.",
        "hint_welcome_new": "Подсказка: нажмите «Регистрация», чтобы продолжить.",
        "hint_task_format": "Подсказка: формат даты/времени — HH:MM DD.MM.YYYY",
        "hint_attach": "Подсказка: отправьте /attach <task_id>, затем файл.",
        "hint_chat": "Подсказка: в разделе «Чат» отправьте сообщение — менеджер ответит.",
        "hint_settings": "Подсказка: в настройках можно сменить язык, имя и телефон.",

        "lbl_assign": "📝 Назначить",
        "lbl_employees": "👤 Сотрудники",
        "lbl_dashboard": "📊 Дашборд",
        "lbl_reports": "🧾 Отчёты",
        "lbl_requests": "📨 Запросы",
        "lbl_settings": "⚙️ Настройки",
        "lbl_chat": "💬 Чат",
        "lbl_ai": "🤖 AI помощник",

        "lbl_my_tasks": "✅ Мои задачи",
        "lbl_send_report": "🧾 Отчёт",
        "lbl_back": "◀️ Назад",
        "lbl_change_lang": "🌐 Сменить язык",
        "lbl_change_name": "📝 Сменить имя",
        "lbl_change_phone": "📞 Сменить телефон",
        "lbl_register": "🆕 Регистрация",

        "employees_title": "Раздел сотрудников:",
        "employees_list_header": "Активные сотрудники:",
        "employees_list_line": "• @{username} — {full_name}",
        "emp_add_hint": "Чтобы добавить сотрудника, отправьте @username (например, @ivan).",
        "emp_remove_hint": "Для удаления также отправьте @username.",
        "invite_created": "Инвайт для @{username}:\n{link}",

        "invites_title": "Запросы инвайтов:",
        "invites_empty": "Запросов нет.",
        "btn_invite_accept": "✅ Принять",
        "btn_invite_reject": "❌ Отклонить",
        "invite_accept_ok": "✅ Одобрено.",
        "invite_reject_ok": "❌ Отклонено.",

        "task_assigned": "Новая задача: {title}\nДедлайн: {deadline}\nПриоритет: {priority}",
        "task_created": "✅ Задача создана (ID: {task_id}).",
        "your_tasks_header": "Ваши задачи:",
        "no_tasks": "Задач пока нет.",
        "done_usage": "Использование: /done <task_id>",
        "done_ok": "✅ Задача #{task_id} выполнена!",
        "done_fail": "❌ #{task_id} не найдена или не вам назначена.",
        "deadline_soon": "⏳ Напоминание: дедлайн задачи #{task_id} «{title}» скоро ({deadline}).",

        "manager_status_header": "Статус сотрудников:",
        "report_prompt": "Отправьте краткий отчёт за сегодня.",
        "reminder_morning": "⏰ Напоминание 9:00: проверьте задачи.",
        "reminder_evening": "⏰ Напоминание 18:00: отправьте отчёт.",

        "settings_title": "Настройки:",
        "ask_new_name": "Введите новое имя:",
        "ask_new_phone": "Пожалуйста, отправьте контакт или укажите номер:",
        "profile_saved": "✅ Профиль обновлён.",
        "choose_language": "Выберите язык:",
    },
    "kk": {
        "welcome_manager": "Сәлем! Менеджер панелі: тапсырма беріңіз, жағдайын бақылаңыз, есептер алыңыз.",
        "welcome_employee": "Сәлем! Бұл сіздің жеке жұмыс панеліңіз.",
        "only_manager": "Кешіріңіз, бұл бөлім тек менеджерлер үшін.",
        "unknown_command": "Белгісіз команда. Түймелерді қолданыңыз.",
        "help_text": "Бұйрықтар: /start, /task, /status, /report, /mytasks, /done",
        "language_set": "Тіл орнатылды: {lang}",

        "hint_pick_language": "Кеңес: төменнен тілді таңдаңыз.",
        "hint_welcome_new": "Кеңес: жалғастыру үшін «Тіркелу» түймесін басыңыз.",
        "hint_task_format": "Кеңес: күн/уақыт форматы — HH:MM DD.MM.YYYY",
        "hint_attach": "Кеңес: /attach <task_id> жіберіп, содан кейін файл жіберіңіз.",
        "hint_chat": "Кеңес: «Чат» бөлімінде хабарлама жіберіңіз — менеджер жауап береді.",
        "hint_settings": "Кеңес: Баптауларда тілді, атты және телефонды өзгерте аласыз.",

        "lbl_assign": "📝 Тапсырма беру",
        "lbl_employees": "👤 Қызметкерлер",
        "lbl_dashboard": "📊 Дашборд",
        "lbl_reports": "🧾 Есептер",
        "lbl_requests": "📨 Сұраулар",
        "lbl_settings": "⚙️ Баптаулар",
        "lbl_chat": "💬 Чат",
        "lbl_ai": "🤖 AI көмекші",

        "lbl_my_tasks": "✅ Менің тапсырмаларым",
        "lbl_send_report": "🧾 Есеп",
        "lbl_back": "◀️ Артқа",
        "lbl_change_lang": "🌐 Тілді өзгерту",
        "lbl_change_name": "📝 Атын өзгерту",
        "lbl_change_phone": "📞 Телефонды өзгерту",
        "lbl_register": "🆕 Тіркелу",

        "employees_title": "Қызметкерлер бөлімі:",
        "employees_list_header": "Белсенді қызметкерлер:",
        "employees_list_line": "• @{username} — {full_name}",
        "emp_add_hint": "@username жіберіп (мысалы, @aidos) қызметкер қосыңыз.",
        "emp_remove_hint": "Жою үшін де @username жіберіңіз.",
        "invite_created": "@{username} үшін шақыру:\n{link}",

        "invites_title": "Шақыру сұраулары:",
        "invites_empty": "Сұраулар жоқ.",
        "btn_invite_accept": "✅ Қабылдау",
        "btn_invite_reject": "❌ Қайтару",
        "invite_accept_ok": "✅ Мақұлданды.",
        "invite_reject_ok": "❌ Қайтарылды.",

        "task_assigned": "Жаңа тапсырма: {title}\nДедлайн: {deadline}\nБасымдылық: {priority}",
        "task_created": "✅ Тапсырма құрылды (ID: {task_id}).",
        "your_tasks_header": "Сіздің тапсырмаларыңыз:",
        "no_tasks": "Пока тапсырма жоқ.",
        "done_usage": "Пайдалану: /done <task_id>",
        "done_ok": "✅ #{task_id} тапсырмасы орындалды!",
        "done_fail": "❌ #{task_id} табылмады немесе сізге тиесілі емес.",
        "deadline_soon": "⏳ Еске салу: #{task_id} «{title}» дедлайны жақындап қалды ({deadline}).",

        "manager_status_header": "Қызметкерлер жағдайы:",
        "report_prompt": "Бүгінгі қысқа есепті жіберіңіз.",
        "reminder_morning": "⏰ 9:00 еске салу: тапсырмаларыңызды тексеріңіз.",
        "reminder_evening": "⏰ 18:00 еске салу: бүгінгі есепті жіберіңіз.",

        "settings_title": "Баптаулар:",
        "ask_new_name": "Жаңа атты енгізіңіз:",
        "ask_new_phone": "Контакт жіберіңіз немесе нөмірді енгізіңіз:",
        "profile_saved": "✅ Профиль жаңартылды.",
        "choose_language": "Тілді таңдаңыз:",
    },
}

DEFAULT_LANG = "uz"

def T(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in STRINGS else DEFAULT_LANG
    s = STRINGS[lang].get(key) or STRINGS[DEFAULT_LANG].get(key) or key
    try:
        return s.format(**kwargs)
    except Exception:
        return s
