STRINGS = {
    "uz": {
        "role_manager": "MENEJER",
        "role_employee": "XODIM",
        "welcome_manager": "Assalomu alaykum! Bu menejer paneli. Vazifalarni bering, holatni kuzating, hisobotlarni oling.",
        "welcome_employee": "Assalomu alaykum! Bu sizning shaxsiy ish panelingiz.",
        "btn_assign_task": "📝 Vazifa berish",
        "btn_status": "📊 Holat",
        "btn_reports": "🧾 Hisobotlar",
        "btn_language": "🌐 Til",
        "btn_help": "❓ Yordam",
        "btn_my_tasks": "✅ Mening vazifalarim",
        "btn_send_report": "🧾 Hisobot yuborish",
        "btn_mark_done": "✔️ Bajarildi",
        "btn_open_tasks": "📋 Vazifalarni ochish",
        "btn_cancel": "✖️ Bekor qilish",
        "btn_set_lang_uz": "🇺🇿 O‘zbekcha",
        "btn_set_lang_ru": "🇷🇺 Русский",
        "btn_set_lang_kk": "🇰🇿 Қазақша",
        "choose_language": "Tilni tanlang:",
        "not_authorized": "Kechirasiz, bu buyruq faqat menejerlar uchun.",
        "unknown_command": "Tushunarsiz buyruq. Tugmalardan foydalaning.",
        "task_assigned_to": "Yangi vazifa: {title}\nMuddat: {deadline}\nUstuvorlik: {priority}",
        "task_assigned_manager_ok": "✅ Vazifa @{username} ga biriktirildi (ID: {task_id}).",
        "no_tasks": "Hozircha vazifalar yo‘q.",
        "your_tasks_header": "Sizning vazifalaringiz:",
        "task_line": "• #{id} [{priority}] {title} — holat: {status}, muddat: {deadline}",
        "task_done_ok": "✅ #{task_id} vazifasi bajarildi!",
        "task_done_notify_manager": "Xodim @{username} #{task_id} vazifasini tugatdi.",
        "daily_morning": "⏰ 9:00 eslatma: vazifalaringizni ko‘rib chiqing.",
        "daily_evening": "⏰ 18:00 eslatma: bugungi hisobotni yuboring (/report).",
        "report_prompt": "Bugungi hisobotni yuboring (qisqacha matn).",
        "report_saved": "✅ Hisobot saqlandi. Rahmat!",
        "manager_status_header": "Xodimlar holati:",
        "manager_status_item": "@{username}: jami {total}, bajarilgan {done}, bajarilmagan {open}",
        "manager_report_header": "Kunlik hisobot ({date}):",
        "manager_report_line": "@{username}: bajarilgan {done}, ochiq {open}",
        "set_role_manager_ok": "Foydalanuvchi endi menejer.",
        "set_role_employee_ok": "Foydalanuvchi endi xodim.",
        "select_employee": "Xodimni tanlang:",
        "assign_task_prompt": "Quyidagi formatda yuboring:\n/task @username \"vazifa matni\" 2025-08-25 18:00 [High]",
        "voice_parsed": "Ovozni tahlil natijasi: @{username} — {title} — {deadline} — {priority}",
        "deadline_soon": "⏳ Eslatma: #{task_id} \"{title}\" vazifasining muddati yaqinlashmoqda ({deadline}).",
        "lang_set_ok": "Til o‘rnatildi: {lang}",
        "only_private": "Iltimos, botdan faqat shaxsiy chatda foydalaning.",
        "help_text": "Asosiy buyruqlar: /start, /task, /status, /report, /mytasks, /done",

        "btn_employees": "👤 Hodimlar",
        "employees_menu_title": "Hodimlar bo‘limi:",
        "btn_employees_list": "📋 Ro‘yxat",
        "btn_employee_add": "➕ Hodim qo‘shish",
        "btn_employee_remove": "🗑️ Hodimni o‘chirish",
        "btn_employee_invite": "🔗 Taklif havolasi",
        "prompt_employee_username": "@username yuboring (masalan, @ali).",
        "invite_created": "Taklif havolasi @{username} uchun tayyor:\n{link}\nBu havolani hodimga yuboring.",
        "employees_list_header": "Faol hodimlar:",
        "employees_list_line": "• @{username} — {full_name}",
        "employee_removed_ok": "✅ Hodim olib tashlandi: @{username}",
        "invite_used_success": "Xush kelibsiz! Taklif qabul qilindi. Sizning rolingiz — XODIM.",
        "invite_username_mismatch": "⚠️ Ogohlantirish: sizning username taklifdagidan farq qiladi.",
        "no_employees": "Hozircha faol hodimlar yo‘q.",
        "enter_username_error": "Username noto‘g‘ri. Iltimos, @ belgisidan foydalaning.",
    },
    "ru": {
        "role_manager": "МЕНЕДЖЕР",
        "role_employee": "СОТРУДНИК",
        "welcome_manager": "Здравствуйте! Это панель менеджера. Назначайте задачи, следите за статусом и получайте отчёты.",
        "welcome_employee": "Здравствуйте! Это ваша личная панель задач.",
        "btn_assign_task": "📝 Назначить задачу",
        "btn_status": "📊 Статус",
        "btn_reports": "🧾 Отчёты",
        "btn_language": "🌐 Язык",
        "btn_help": "❓ Помощь",
        "btn_my_tasks": "✅ Мои задачи",
        "btn_send_report": "🧾 Отправить отчёт",
        "btn_mark_done": "✔️ Готово",
        "btn_open_tasks": "📋 Открыть задачи",
        "btn_cancel": "✖️ Отмена",
        "btn_set_lang_uz": "🇺🇿 O‘zbekcha",
        "btn_set_lang_ru": "🇷🇺 Русский",
        "btn_set_lang_kk": "🇰🇿 Қазақша",
        "choose_language": "Выберите язык:",
        "not_authorized": "Извините, команда доступна только менеджерам.",
        "unknown_command": "Неизвестная команда. Используйте кнопки.",
        "task_assigned_to": "Новая задача: {title}\nДедлайн: {deadline}\nПриоритет: {priority}",
        "task_assigned_manager_ok": "✅ Задача назначена @{username} (ID: {task_id}).",
        "no_tasks": "Пока нет задач.",
        "your_tasks_header": "Ваши задачи:",
        "task_line": "• #{id} [{priority}] {title} — статус: {status}, дедлайн: {deadline}",
        "task_done_ok": "✅ Задача #{task_id} выполнена!",
        "task_done_notify_manager": "Сотрудник @{username} выполнил задачу #{task_id}.",
        "daily_morning": "⏰ Напоминание 9:00: проверьте задачи.",
        "daily_evening": "⏰ Напоминание 18:00: отправьте отчёт за сегодня (/report).",
        "report_prompt": "Отправьте краткий отчёт за сегодня.",
        "report_saved": "✅ Отчёт сохранён. Спасибо!",
        "manager_status_header": "Статус сотрудников:",
        "manager_status_item": "@{username}: всего {total}, выполнено {done}, открыто {open}",
        "manager_report_header": "Дневной отчёт ({date}):",
        "manager_report_line": "@{username}: выполнено {done}, открыто {open}",
        "set_role_manager_ok": "Пользователь теперь менеджер.",
        "set_role_employee_ok": "Пользователь теперь сотрудник.",
        "select_employee": "Выберите сотрудника:",
        "assign_task_prompt": "Отправьте в формате:\n/task @username \"текст задачи\" 2025-08-25 18:00 [High]",
        "voice_parsed": "Распознано из голоса: @{username} — {title} — {deadline} — {priority}",
        "deadline_soon": "⏳ Напоминание: дедлайн задачи #{task_id} «{title}» скоро ({deadline}).",
        "lang_set_ok": "Язык установлен: {lang}",
        "only_private": "Пожалуйста, используйте бота только в личном чате.",
        "help_text": "Команды: /start, /task, /status, /report, /mytasks, /done",

        "btn_employees": "👤 Сотрудники",
        "employees_menu_title": "Раздел сотрудников:",
        "btn_employees_list": "📋 Список",
        "btn_employee_add": "➕ Добавить",
        "btn_employee_remove": "🗑️ Удалить",
        "btn_employee_invite": "🔗 Инвайт-ссылка",
        "prompt_employee_username": "Отправьте @username (например, @ivan).",
        "invite_created": "Инвайт-ссылка для @{username}:\n{link}\nПерешлите её сотруднику.",
        "employees_list_header": "Активные сотрудники:",
        "employees_list_line": "• @{username} — {full_name}",
        "employee_removed_ok": "✅ Сотрудник удалён: @{username}",
        "invite_used_success": "Добро пожаловать! Ваша роль — СОТРУДНИК.",
        "invite_username_mismatch": "⚠️ Внимание: ваш username отличается от указанного в инвайте.",
        "no_employees": "Пока нет активных сотрудников.",
        "enter_username_error": "Неверный username. Пожалуйста, укажите с @.",
    },
    "kk": {
        "role_manager": "МЕНЕДЖЕР",
        "role_employee": "ҚЫЗМЕТКЕР",
        "welcome_manager": "Сәлеметсіз бе! Бұл менеджер панелі. Тапсырма беріңіз, жағдайын қадағалаңыз, есеп алыңыз.",
        "welcome_employee": "Сәлеметсіз бе! Бұл сіздің жеке тақтаңыз.",
        "btn_assign_task": "📝 Тапсырма беру",
        "btn_status": "📊 Жағдай",
        "btn_reports": "🧾 Есептер",
        "btn_language": "🌐 Тіл",
        "btn_help": "❓ Көмек",
        "btn_my_tasks": "✅ Менің тапсырмаларым",
        "btn_send_report": "🧾 Есеп жіберу",
        "btn_mark_done": "✔️ Орындалды",
        "btn_open_tasks": "📋 Тапсырмаларды ашу",
        "btn_cancel": "✖️ Бас тарту",
        "btn_set_lang_uz": "🇺🇿 O‘zbekcha",
        "btn_set_lang_ru": "🇷🇺 Русский",
        "btn_set_lang_kk": "🇰🇿 Қазақша",
        "choose_language": "Тілді таңдаңыз:",
        "not_authorized": "Кешіріңіз, бұл бұйрық тек менеджерлерге арналған.",
        "unknown_command": "Белгісіз бұйрық. Түймелерді пайдаланыңыз.",
        "task_assigned_to": "Жаңа тапсырма: {title}\nДедлайн: {deadline}\nБасымдылық: {priority}",
        "task_assigned_manager_ok": "✅ Тапсырма @{username} қолданушысына тағайындалды (ID: {task_id}).",
        "no_tasks": "Әзірге тапсырмалар жоқ.",
        "your_tasks_header": "Сіздің тапсырмаларыңыз:",
        "task_line": "• #{id} [{priority}] {title} — күйі: {status}, дедлайн: {deadline}",
        "task_done_ok": "✅ #{task_id} тапсырмасы орындалды!",
        "task_done_notify_manager": "Қызметкер @{username} #{task_id} тапсырмасын аяқтады.",
        "daily_morning": "⏰ 9:00 еске салу: тапсырмаларыңызды тексеріңіз.",
        "daily_evening": "⏰ 18:00 еске салу: бүгінгі есепті жіберіңіз (/report).",
        "report_prompt": "Бүгінгі есепті қысқаша жіберіңіз.",
        "report_saved": "✅ Есеп сақталды. Рақмет!",
        "manager_status_header": "Қызметкерлердің жағдайы:",
        "manager_status_item": "@{username}: барлығы {total}, орындалды {done}, ашық {open}",
        "manager_report_header": "Күндік есеп ({date}):",
        "manager_report_line": "@{username}: орындалды {done}, ашық {open}",
        "set_role_manager_ok": "Пайдаланушы енді менеджер.",
        "set_role_employee_ok": "Пайдаланушы енді қызметкер.",
        "select_employee": "Қызметкерді таңдаңыз:",
        "assign_task_prompt": "Формат:\n/task @username \"тапсырма мәтіні\" 2025-08-25 18:00 [High]",
        "voice_parsed": "Дауыс тану нәтижесі: @{username} — {title} — {deadline} — {priority}",
        "deadline_soon": "⏳ Еске салу: #{task_id} «{title}» тапсырмасының дедлайны жақын ({deadline}).",
        "lang_set_ok": "Тіл орнатылды: {lang}",
        "only_private": "Ботты тек жеке чатта пайдаланыңыз.",
        "help_text": "Негізгі бұйрықтар: /start, /task, /status, /report, /mytasks, /done",

        "btn_employees": "👤 Қызметкерлер",
        "employees_menu_title": "Қызметкерлер бөлімі:",
        "btn_employees_list": "📋 Тізім",
        "btn_employee_add": "➕ Қосу",
        "btn_employee_remove": "🗑️ Жою",
        "btn_employee_invite": "🔗 Шақыру сілтемесі",
        "prompt_employee_username": "@username жіберіңіз (мысалы, @aidos).",
        "invite_created": "@{username} үшін шақыру сілтемесі:\n{link}\nБұл сілтемені қызметкерге жіберіңіз.",
        "employees_list_header": "Белсенді қызметкерлер:",
        "employees_list_line": "• @{username} — {full_name}",
        "employee_removed_ok": "✅ Қызметкер жойылды: @{username}",
        "invite_used_success": "Қош келдіңіз! Сіздің рөліңіз — ҚЫЗМЕТКЕР.",
        "invite_username_mismatch": "⚠️ Ескерту: сіздің username шақырудағыдан өзгеше.",
        "no_employees": "Әзірге белсенді қызметкерлер жоқ.",
        "enter_username_error": "Дұрыс емес username. Өтінеміз, @ таңбасымен жазыңыз.",
    }
}

DEFAULT_LANG = "uz"

def T(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in STRINGS else DEFAULT_LANG
    s = STRINGS[lang].get(key) or STRINGS[DEFAULT_LANG].get(key) or key
    try:
        return s.format(**kwargs)
    except Exception:
        return s

# Moslik uchun kichik harfni ham qoldiramiz
t = T


# === ALIASES & MISSING KEYS PATCH (bot.py bilan 1:1 moslash) ===
def _alias(lang: str, src: str, dst: str):
    if lang in STRINGS and src in STRINGS[lang] and dst not in STRINGS[lang]:
        STRINGS[lang][dst] = STRINGS[lang][src]

def _ensure(lang: str, key: str, value: str):
    if lang in STRINGS and key not in STRINGS[lang]:
        STRINGS[lang][key] = value

for lg in ("uz", "ru", "kk"):
    # btn_mytasks ← btn_my_tasks
    _alias(lg, "btn_my_tasks", "btn_mytasks")
    # btn_report_today ← btn_send_report
    _alias(lg, "btn_send_report", "btn_report_today")
    # employees_title ← employees_menu_title
    _alias(lg, "employees_menu_title", "employees_title")
    # btn_emp_* ← btn_employee_*
    _alias(lg, "btn_employees_list", "btn_emp_list")
    _alias(lg, "btn_employee_add", "btn_emp_add")
    _alias(lg, "btn_employee_remove", "btn_emp_remove")
    # employees_empty ← no_employees
    _alias(lg, "no_employees", "employees_empty")
    # language_set ← lang_set_ok
    _alias(lg, "lang_set_ok", "language_set")
    # task_assigned ← task_assigned_to
    _alias(lg, "task_assigned_to", "task_assigned")
    # task_usage ← assign_task_prompt
    _alias(lg, "assign_task_prompt", "task_usage")
    # reminder_* ← daily_*
    _alias(lg, "daily_morning", "reminder_morning")
    _alias(lg, "daily_evening", "reminder_evening")
    # deadline_ping ← deadline_soon
    _alias(lg, "deadline_soon", "deadline_ping")

# Yo‘q bo‘lsa — default qiymatlarni qo‘shamiz
_ensure("uz", "btn_back", "◀️ Orqaga")
_ensure("ru", "btn_back", "◀️ Назад")
_ensure("kk", "btn_back", "◀️ Артқа")

_ensure("uz", "emp_add_hint", "Hodim qo‘shish uchun @username yuboring (masalan, @ali).")
_ensure("ru", "emp_add_hint", "Чтобы добавить сотрудника, отправьте @username (например, @ivan).")
_ensure("kk", "emp_add_hint", "Қызметкер қосу үшін @username жіберіңіз (мысалы, @aidos).")

_ensure("uz", "emp_remove_hint", "O‘chirish uchun ham @username yuboring.")
_ensure("ru", "emp_remove_hint", "Для удаления также отправьте @username.")
_ensure("kk", "emp_remove_hint", "Жою үшін де @username жіберіңіз.")

_ensure("uz", "emp_added", "✅ @{username} qo‘shildi.\nTaklif: {link}")
_ensure("ru", "emp_added", "✅ @{username} добавлен.\nИнвайт: {link}")
_ensure("kk", "emp_added", "✅ @{username} қосылды.\nШақыру: {link}")

_ensure("uz", "emp_add_fail", "❌ @{username} qo‘shib bo‘lmadi.")
_ensure("ru", "emp_add_fail", "❌ Не удалось добавить @{username}.")
_ensure("kk", "emp_add_fail", "❌ @{username} қосу мүмкін болмады.")

_ensure("uz", "emp_removed", "✅ @{username} o‘chirildi.")
_ensure("ru", "emp_removed", "✅ @{username} удалён.")
_ensure("kk", "emp_removed", "✅ @{username} жойылды.")

_ensure("uz", "emp_remove_fail", "❌ @{username} topilmadi.")
_ensure("ru", "emp_remove_fail", "❌ @{username} не найден.")
_ensure("kk", "emp_remove_fail", "❌ @{username} табылмады.")

_ensure("uz", "only_manager", "Kechirasiz, bu buyruq faqat menejerlar uchun.")
_ensure("ru", "only_manager", "Извините, команда доступна только менеджерам.")
_ensure("kk", "only_manager", "Кешіріңіз, бұл бұйрық тек менеджерлерге арналған.")

_ensure("uz", "task_created", "✅ Vazifa yaratildi (ID: {task_id}).")
_ensure("ru", "task_created", "✅ Задача создана (ID: {task_id}).")
_ensure("kk", "task_created", "✅ Тапсырма құрылды (ID: {task_id}).")

_ensure("uz", "done_usage", "Foydalanish: /done <task_id>")
_ensure("ru", "done_usage", "Использование: /done <task_id>")
_ensure("kk", "done_usage", "Пайдалану: /done <task_id>")

_ensure("uz", "done_ok", "✅ #{task_id} vazifasi bajarildi!")
_ensure("ru", "done_ok", "✅ Задача #{task_id} выполнена!")
_ensure("kk", "done_ok", "✅ #{task_id} тапсырмасы орындалды!")

_ensure("uz", "done_fail", "❌ #{task_id} topilmadi yoki sizga tegishli emas.")
_ensure("ru", "done_fail", "❌ #{task_id} не найдено или не принадлежит вам.")
_ensure("kk", "done_fail", "❌ #{task_id} табылмады немесе сізге тиесілі емес.")
