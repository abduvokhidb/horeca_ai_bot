# languages.py
DEFAULT_LANG = "uz"

STRINGS = {
    "uz": {
        # --- Core / Welcome ---
        "welcome_manager": "Assalomu alaykum! Menejer paneli: vazifa bering, holatni ko‘ring, hisobot oling.",
        "welcome_employee": "Assalomu alaykum! Bu sizning shaxsiy ish panelingiz.",
        "choose_language": "Tilni tanlang:",
        "language_set": "Til o‘rnatildi: {lang}",
        "only_manager": "Kechirasiz, bu bo‘lim faqat menejerlar uchun.",
        "unknown_command": "Tushunarsiz buyruq. Pastdagi tugmalardan foydalaning.",
        "help_text": "Buyruqlar: /start, /task, /status, /report, /mytasks, /done",

        # --- Hints / Podskazka ---
        "hint": "Podskazka",
        "hint_pick_language": "Podskazka: quyida foydalanish tilini tanlang.",
        "hint_task_format": "Podskazka: sana/vaqt formati — HH:MM DD.MM.YYYY",
        "hint_chat": "Podskazka: Chat bo‘limida xabar yuboring, admin javob beradi.",
        "hint_settings": "Podskazka: Sozlamalarda til, ism va telefonni yangilashingiz mumkin.",

        # --- Main labels (admin home) ---
        "lbl_assign": "📝 Vazifa berish",
        "lbl_employees": "👤 Hodimlar",
        "lbl_dashboard": "📊 Dashboard",
        "lbl_reports": "🧾 Hisobotlar",
        "lbl_requests": "📨 So‘rovlar",
        "lbl_settings": "⚙️ Sozlamalar",
        "lbl_chat": "💬 Chat",
        "lbl_ai": "🤖 AI yordamchi",

        # --- Employee home ---
        "lbl_my_tasks": "✅ Mening vazifalarim",
        "lbl_send_report": "🧾 Hisobot",
        "lbl_back": "◀️ Orqaga",
        "lbl_change_lang": "🌐 Tilni o‘zgartirish",
        "lbl_change_name": "📝 Ismni o‘zgartirish",
        "lbl_change_phone": "📞 Telefonni o‘zgartirish",
        "lbl_register": "🆕 Ro‘yxatdan o‘tish",

        # --- Employees ---
        "employees_title": "Hodimlar bo‘limi:",
        "employees_empty": "Hozircha faol hodimlar yo‘q.",
        "employees_list_header": "Faol hodimlar:",
        "employees_list_line": "• @{username} — {full_name}",
        "emp_add_hint": "Hodim qo‘shish uchun @username yuboring (masalan, @ali).",
        "emp_remove_hint": "O‘chirish uchun ham @username yuboring.",
        "enter_username_error": "Username noto‘g‘ri. Iltimos, @ bilan yuboring.",
        "emp_removed": "✅ @{username} o‘chirildi.",
        "emp_remove_fail": "❌ @{username} topilmadi.",
        "invite_created": "Taklif havolasi @{username} uchun tayyor:\n{link}",

        # --- Invites / Requests ---
        "invites_title": "🧾 Pending invites:",
        "invites_empty": "So‘rovlar yo‘q.",
        "btn_invite_accept": "✅ Qabul qilish",
        "btn_invite_reject": "❌ Rad etish",
        "invite_accept_ok": "✅ Invite tasdiqlandi.",
        "invite_reject_ok": "❌ Invite rad etildi.",

        # --- Tasks ---
        "assign_task_prompt": "Quyidagi formatda yuboring:\n/task @username \"vazifa\" 10:00 24.09.2025 [High]",
        "task_assigned": "Yangi vazifa: {title}\nMuddat: {deadline}\nUstuvorlik: {priority}",
        "task_created": "✅ Vazifa yaratildi (ID: {task_id}).",
        "no_tasks": "Hozircha vazifalar yo‘q.",
        "your_tasks_header": "Sizning vazifalaringiz:",
        "done_usage": "Foydalanish: /done <task_id>",
        "done_ok": "✅ #{task_id} vazifasi bajarildi!",
        "done_fail": "❌ #{task_id} topilmadi yoki sizga tegishli emas.",
        "task_done_notify_manager": "Xodim @{username} #{task_id} vazifasini tugatdi.",

        # --- Status/Report ---
        "manager_status_header": "Xodimlar holati:",
        "report_prompt": "Bugungi hisobotni yuboring (qisqacha).",

        # --- Reminders / Deadlines ---
        "reminder_morning": "⏰ 9:00 eslatma: vazifalaringizni ko‘rib chiqing.",
        "reminder_evening": "⏰ 18:00 eslatma: bugungi hisobotni yuboring.",
        "deadline_ping": "⏳ Eslatma: vazifa yaqinlashdi — {task}",
    },

    "ru": {
        "welcome_manager": "Здравствуйте! Панель менеджера: назначайте задачи, смотрите статус, получайте отчёты.",
        "welcome_employee": "Здравствуйте! Это ваша личная панель.",
        "choose_language": "Выберите язык:",
        "language_set": "Язык установлен: {lang}",
        "only_manager": "Извините, раздел доступен только менеджерам.",
        "unknown_command": "Неизвестная команда. Используйте кнопки ниже.",
        "help_text": "Команды: /start, /task, /status, /report, /mytasks, /done",

        "hint": "Подсказка",
        "hint_pick_language": "Подсказка: выберите язык ниже.",
        "hint_task_format": "Подсказка: формат даты/времени — HH:MM DD.MM.YYYY",
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
        "employees_empty": "Пока нет активных сотрудников.",
        "employees_list_header": "Активные сотрудники:",
        "employees_list_line": "• @{username} — {full_name}",
        "emp_add_hint": "Чтобы добавить сотрудника, отправьте @username (например, @ivan).",
        "emp_remove_hint": "Для удаления также отправьте @username.",
        "enter_username_error": "Неверный username. Пожалуйста, с @.",
        "emp_removed": "✅ @{username} удалён.",
        "emp_remove_fail": "❌ @{username} не найден.",
        "invite_created": "Инвайт-ссылка для @{username}:\n{link}",

        "invites_title": "🧾 Запросы инвайтов:",
        "invites_empty": "Запросов нет.",
        "btn_invite_accept": "✅ Принять",
        "btn_invite_reject": "❌ Отклонить",
        "invite_accept_ok": "✅ Запрос одобрен.",
        "invite_reject_ok": "❌ Запрос отклонён.",

        "assign_task_prompt": "Формат:\n/task @username \"задача\" 10:00 24.09.2025 [High]",
        "task_assigned": "Новая задача: {title}\nДедлайн: {deadline}\nПриоритет: {priority}",
        "task_created": "✅ Задача создана (ID: {task_id}).",
        "no_tasks": "Пока нет задач.",
        "your_tasks_header": "Ваши задачи:",
        "done_usage": "Использование: /done <task_id>",
        "done_ok": "✅ Задача #{task_id} выполнена!",
        "done_fail": "❌ #{task_id} не найдена или не принадлежит вам.",
        "task_done_notify_manager": "Сотрудник @{username} выполнил задачу #{task_id}.",

        "manager_status_header": "Статус сотрудников:",
        "report_prompt": "Отправьте краткий отчёт за сегодня.",

        "reminder_morning": "⏰ Напоминание 9:00: проверьте задачи.",
        "reminder_evening": "⏰ Напоминание 18:00: отправьте отчёт.",
        "deadline_ping": "⏳ Напоминание: приближается срок — {task}",
    },

    "kk": {
        "welcome_manager": "Сәлем! Менеджер панелі: тапсырма беріңіз, күйін қараңыз, есеп алыңыз.",
        "welcome_employee": "Сәлем! Бұл сіздің жеке панеліңіз.",
        "choose_language": "Тілді таңдаңыз:",
        "language_set": "Тіл орнатылды: {lang}",
        "only_manager": "Кешіріңіз, бұл бөлім тек менеджерлер үшін.",
        "unknown_command": "Белгісіз команда. Төмендегі түймелерді пайдаланыңыз.",
        "help_text": "Бұйрықтар: /start, /task, /status, /report, /mytasks, /done",

        "hint": "Кеңес",
        "hint_pick_language": "Кеңес: төменнен тілді таңдаңыз.",
        "hint_task_format": "Кеңес: күн/уақыт форматы — HH:MM DD.MM.YYYY",
        "hint_chat": "Кеңес: «Чат» бөлімінде хабар жіберіңіз — менеджер жауап береді.",
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
        "employees_empty": "Әзірге белсенді қызметкерлер жоқ.",
        "employees_list_header": "Белсенді қызметкерлер:",
        "employees_list_line": "• @{username} — {full_name}",
        "emp_add_hint": "@username жіберіп (мысалы, @aidos) қызметкер қосыңыз.",
        "emp_remove_hint": "Жою үшін де @username жіберіңіз.",
        "enter_username_error": "Дұрыс емес username. @ таңбасымен жіберіңіз.",
        "emp_removed": "✅ @{username} жойылды.",
        "emp_remove_fail": "❌ @{username} табылмады.",
        "invite_created": "@{username} үшін шақыру сілтемесі:\n{link}",

        "invites_title": "🧾 Шақыру сұраулары:",
        "invites_empty": "Сұраулар жоқ.",
        "btn_invite_accept": "✅ Қабылдау",
        "btn_invite_reject": "❌ Қайтару",
        "invite_accept_ok": "✅ Сұрау қабылданды.",
        "invite_reject_ok": "❌ Сұрау қайтарылды.",

        "assign_task_prompt": "Формат:\n/task @username \"тапсырма\" 10:00 24.09.2025 [High]",
        "task_assigned": "Жаңа тапсырма: {title}\nДедлайн: {deadline}\nБасымдылық: {priority}",
        "task_created": "✅ Тапсырма құрылды (ID: {task_id}).",
        "no_tasks": "Әзірге тапсырмалар жоқ.",
        "your_tasks_header": "Сіздің тапсырмаларыңыз:",
        "done_usage": "Пайдалану: /done <task_id>",
        "done_ok": "✅ #{task_id} тапсырмасы орындалды!",
        "done_fail": "❌ #{task_id} табылмады немесе сізге тиесілі емес.",
        "task_done_notify_manager": "Қызметкер @{username} #{task_id} тапсырмасын аяқтады.",

        "manager_status_header": "Қызметкерлердің жағдайы:",
        "report_prompt": "Бүгінгі қысқа есепті жіберіңіз.",

        "reminder_morning": "⏰ 9:00 еске салу: тапсырмаларыңызды тексеріңіз.",
        "reminder_evening": "⏰ 18:00 еске салу: бүгінгі есепті жіберіңіз.",
        "deadline_ping": "⏳ Еске салу: мерзім жақындады — {task}",
    },
}

def T(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in STRINGS else DEFAULT_LANG
    s = STRINGS[lang].get(key) or STRINGS[DEFAULT_LANG].get(key) or key
    try:
        return s.format(**kwargs)
    except Exception:
        return s
# languages.py oxiriga qo'shing

# --- Aliases (orqaga moslik) ---
def _alias(lang: str, src: str, dst: str):
    if lang in STRINGS and src in STRINGS[lang] and dst not in STRINGS[lang]:
        STRINGS[lang][dst] = STRINGS[lang][src]

for lg in ("uz", "ru", "kk"):
    # menu labels
    _alias(lg, "btn_back", "btn_back")  # agar allaqachon bor bo'lsa qoldiradi
    # lbl_* ni btn_* ga ko'chirish
    _alias(lg, "lbl_back", "btn_back")
    _alias(lg, "lbl_emp_list", "btn_emp_list")
    _alias(lg, "lbl_emp_add", "btn_emp_add")
    _alias(lg, "lbl_emp_remove", "btn_emp_remove")

    # Agar siz asosiy menyuda lbl_* ishlatsangiz, btn_* nomlari ham ishlasin:
    menu_pairs = {
        "lbl_assign": "btn_assign",
        "lbl_employees": "btn_employees",
        "lbl_dashboard": "btn_dashboard",
        "lbl_reports": "btn_reports",
        "lbl_requests": "btn_requests",
        "lbl_settings": "btn_settings",
        "lbl_chat": "btn_chat",
        "lbl_ai": "btn_ai",
        "lbl_my_tasks": "btn_my_tasks",
        "lbl_send_report": "btn_send_report",
        "lbl_change_lang": "btn_change_lang",
        "lbl_change_name": "btn_change_name",
        "lbl_change_phone": "btn_change_phone",
        "lbl_register": "btn_register",
    }
    for src, dst in menu_pairs.items():
        _alias(lg, src, dst)

# Minimal kalitlar ishonch uchun:
for lg in ("uz", "ru", "kk"):
    STRINGS[lg].setdefault("assign_task_prompt",
        STRINGS[lg].get("task_usage") or STRINGS["uz"]["assign_task_prompt"])
