# languages.py

STRINGS = {
    "uz": {
        # --- Roles / Welcome ---
        "role_manager": "MENEJER",
        "role_employee": "XODIM",
        "welcome_manager": "Assalomu alaykum! Bu menejer paneli. Vazifalarni bering, holatni kuzating, hisobotlarni oling.",
        "welcome_employee": "Assalomu alaykum! Bu sizning shaxsiy ish panelingiz.",
        "welcome_invite_required": "Hodimlar botdan foydalanishi uchun admin tomonidan INVITE havola beriladi.\nQuyidagi tugma orqali so‘rov yuborishingiz mumkin.",

        # --- Main buttons / Menus (matn sifatida ham kerak bo‘lishi mumkin) ---
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
        "btn_back": "◀️ Orqaga",

        # --- Language menu ---
        "btn_set_lang_uz": "🇺🇿 O‘zbekcha",
        "btn_set_lang_ru": "🇷🇺 Русский",
        "btn_set_lang_kk": "🇰🇿 Қазақша",
        "choose_language": "Tilni tanlang:",
        "lang_set_ok": "Til o‘rnatildi: {lang}",
        "language_set": "Til o‘rnatildi: {lang}",

        # --- Guards / help ---
        "only_private": "Iltimos, botdan faqat shaxsiy chatda foydalaning.",
        "not_authorized": "Kechirasiz, bu buyruq faqat menejerlar uchun.",
        "only_manager": "Kechirasiz, bu buyruq faqat menejerlar uchun.",
        "unknown_command": "Tushunarsiz buyruq. Tugmalardan foydalaning.",
        "help_text": "Asosiy buyruqlar: /start, /task, /status, /report, /mytasks, /done",

        # --- Employees (menu & actions) ---
        "btn_employees": "👤 Hodimlar",
        "employees_menu_title": "Hodimlar bo‘limi:",
        "employees_title": "Hodimlar bo‘limi:",
        "btn_employees_list": "📋 Ro‘yxat",
        "btn_employee_add": "➕ Hodim qo‘shish",
        "btn_employee_remove": "🗑️ Hodimni o‘chirish",
        "btn_employee_invite": "🔗 Taklif havolasi",
        "btn_emp_list": "📋 Ro‘yxat",
        "btn_emp_add": "➕ Qo‘shish",
        "btn_emp_remove": "🗑️ O‘chirish",
        "employees_list_header": "Faol hodimlar:",
        "employees_list_line": "• @{username} — {full_name}",
        "no_employees": "Hozircha faol hodimlar yo‘q.",
        "employees_empty": "Hozircha faol hodimlar yo‘q.",
        "prompt_employee_username": "@username yuboring (masalan, @ali).",
        "emp_add_hint": "Hodim qo‘shish uchun @username yuboring (masalan, @ali).",
        "emp_remove_hint": "O‘chirish uchun ham @username yuboring.",
        "employee_removed_ok": "✅ Hodim olib tashlandi: @{username}",
        "emp_removed": "✅ @{username} o‘chirildi.",
        "emp_remove_fail": "❌ @{username} topilmadi.",
        "invite_created": "Taklif havolasi @{username} uchun tayyor:\n{link}\nBu havolani hodimga yuboring.",
        "invite_used_success": "Xush kelibsiz! Taklif qabul qilindi. Sizning rolingiz — XODIM.",
        "invite_username_mismatch": "⚠️ Ogohlantirish: sizning username taklifdagidan farq qiladi.",
        "enter_username_error": "Username noto‘g‘ri. Iltimos, @ belgisidan foydalaning.",
        "emp_added": "✅ @{username} qo‘shildi.\nTaklif: {link}",
        "emp_add_fail": "❌ @{username} qo‘shib bo‘lmadi.",

        # --- Invites (admin panel) ---
        "btn_request_invite": "🔗 Invite so‘rash",
        "invite_ask_username_fullname": "Invite so‘rovi uchun @username va Ismingizni yuboring.\nMasalan: @whoop_uz Abduvohid",
        "invite_request_saved": "✅ So‘rovingiz qabul qilindi. Administrator tasdiqlashi bilan xabar olasiz.",
        "invite_request_exists": "ℹ️ Sizda faol invite so‘rovi bor. Administrator qarorini kuting.",
        "btn_admin_invites": "📨 Invites",
        "invites_title": "Invites so‘rovlari:",
        "pending_invites_title": "🧾 Pending invites:",
        "invites_empty": "Hozircha yangi invite so‘rovlari yo‘q.",
        "invite_row": "• #{id} @{username} — {full_name} — holat: {status}",
        "btn_invite_accept": "✅ Qabul qilish",
        "btn_invite_reject": "❌ Rad etish",
        "invite_accept_ok": "✅ Invite so‘rovi tasdiqlandi.",
        "invite_reject_ok": "❌ Invite so‘rovi rad etildi.",

        # --- Tasks (creation / lines / statuses) ---
        "task_assigned_to": "Yangi vazifa: {title}\nMuddat: {deadline}\nUstuvorlik: {priority}",
        "task_assigned": "Yangi vazifa: {title}\nMuddat: {deadline}\nUstuvorlik: {priority}",
        "task_assigned_manager_ok": "✅ Vazifa @{username} ga biriktirildi (ID: {task_id}).",
        "task_created": "✅ Vazifa yaratildi (ID: {task_id}).",
        "no_tasks": "Hozircha vazifalar yo‘q.",
        "your_tasks_header": "Sizning vazifalaringiz:",
        "task_line": "• #{id} [{priority}] {title} — holat: {status}, muddat: {deadline}",
        "task_controls": "Vazifa #{task_id}\n{title}\nMuddat: {deadline}\nUstuvorlik: {priority}",

        # --- Task inline buttons (employee side) ---
        "btn_task_accept": "👍 Qabul qilish",
        "btn_task_reject": "👎 Rad etish",
        "btn_task_done": "✔️ Bajarildi",
        "ask_reject_reason": "Rad etish sababini yozib yuboring (qisqacha).",
        "reject_saved_ok": "✅ Rad etish sababi saqlandi.",
        "task_accepted_ok": "✅ Vazifa qabul qilindi.",
        "task_rejected_ok": "❌ Vazifa rad etildi.",
        "task_already_decided": "ℹ️ Bu vazifa bo‘yicha qaror allaqachon qabul qilingan.",
        "task_done_ok": "✅ #{task_id} vazifasi bajarildi!",
        "task_done_notify_manager": "Xodim @{username} #{task_id} vazifasini tugatdi.",

        # --- Notifications to manager on changes ---
        "notify_task_accepted": "👤 @{username} #{task_id} vazifasini QABUL QILDI.",
        "notify_task_rejected": "👤 @{username} #{task_id} vazifasini RAD QILDI. Sabab: {reason}",
        "notify_task_done": "👤 @{username} #{task_id} vazifasini BAJARDI.",

        # --- Reminders / Deadlines ---
        "daily_morning": "⏰ 9:00 eslatma: vazifalaringizni ko‘rib chiqing.",
        "daily_evening": "⏰ 18:00 eslatma: bugungi hisobotni yuboring (/report).",
        "reminder_morning": "⏰ 9:00 eslatma: vazifalaringizni ko‘rib chiqing.",
        "reminder_evening": "⏰ 18:00 eslatma: bugungi hisobotni yuboring (/report).",
        "deadline_soon": "⏳ Eslatma: #{task_id} \"{title}\" vazifasining muddati yaqinlashmoqda ({deadline}).",
        "deadline_ping": "⏳ Eslatma: vazifa yaqinlashdi — {task}",

        # --- Reports / Status (manager) ---
        "report_prompt": "Bugungi hisobotni yuboring (qisqacha matn).",
        "report_saved": "✅ Hisobot saqlandi. Rahmat!",
        "manager_status_header": "Xodimlar holati:",
        "manager_status_item": "@{username}: jami {total}, bajarilgan {done}, bajarilmagan {open}",
        "manager_report_header": "Kunlik hisobot ({date}):",
        "manager_report_line": "@{username}: bajarilgan {done}, ochiq {open}",

        # --- Parsing / AI assist texts ---
        "assign_task_prompt": "Quyidagi formatda yuboring:\n/task @username \"vazifa matni\" 2025-08-25 18:00 [High]",
        "task_usage": "Quyidagi formatda yuboring:\n/task @username \"vazifa matni\" 2025-08-25 18:00 [High]",
        "voice_parsed": "Ovozni tahlil natijasi: @{username} — {title} — {deadline} — {priority}",
        "date_inferred_today": "📅 Sana ko‘rsatilmagan — bugungi sana qabul qilindi: {date}",
        "date_inferred_tomorrow": "📅 “Ertaga” deb tushunildi: {date}",
        "date_parsed_ok": "📅 Sana aniqlashtirildi: {date}",
        "priority_parsed_ok": "🔥 Ustuvorlik: {priority}",
        "parsed_from_voice": "🎙️ Ovozdan olindi: \"{title}\" — {deadline} — {priority}",

        # --- Done / usage prompts ---
        "done_usage": "Foydalanish: /done <task_id>",
        "done_ok": "✅ #{task_id} vazifasi bajarildi!",
        "done_fail": "❌ #{task_id} topilmadi yoki sizga tegishli emas.",
    },

    "ru": {
        "role_manager": "МЕНЕДЖЕР",
        "role_employee": "СОТРУДНИК",
        "welcome_manager": "Здравствуйте! Это панель менеджера. Назначайте задачи, следите за статусом и получайте отчёты.",
        "welcome_employee": "Здравствуйте! Это ваша личная панель задач.",
        "welcome_invite_required": "Чтобы пользоваться ботом, сотруднику нужна INVITE-ссылка от администратора.\nВы можете отправить запрос по кнопке ниже.",

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
        "btn_back": "◀️ Назад",

        "btn_set_lang_uz": "🇺🇿 O‘zbekcha",
        "btn_set_lang_ru": "🇷🇺 Русский",
        "btn_set_lang_kk": "🇰🇿 Қазақша",
        "choose_language": "Выберите язык:",
        "lang_set_ok": "Язык установлен: {lang}",
        "language_set": "Язык установлен: {lang}",

        "only_private": "Пожалуйста, используйте бота только в личном чате.",
        "not_authorized": "Извините, команда доступна только менеджерам.",
        "only_manager": "Извините, команда доступна только менеджерам.",
        "unknown_command": "Неизвестная команда. Используйте кнопки.",
        "help_text": "Команды: /start, /task, /status, /report, /mytasks, /done",

        "btn_employees": "👤 Сотрудники",
        "employees_menu_title": "Раздел сотрудников:",
        "employees_title": "Раздел сотрудников:",
        "btn_employees_list": "📋 Список",
        "btn_employee_add": "➕ Добавить",
        "btn_employee_remove": "🗑️ Удалить",
        "btn_employee_invite": "🔗 Инвайт-ссылка",
        "btn_emp_list": "📋 Список",
        "btn_emp_add": "➕ Добавить",
        "btn_emp_remove": "🗑️ Удалить",
        "employees_list_header": "Активные сотрудники:",
        "employees_list_line": "• @{username} — {full_name}",
        "no_employees": "Пока нет активных сотрудников.",
        "employees_empty": "Пока нет активных сотрудников.",
        "prompt_employee_username": "Отправьте @username (например, @ivan).",
        "emp_add_hint": "Чтобы добавить сотрудника, отправьте @username (например, @ivan).",
        "emp_remove_hint": "Для удаления также отправьте @username.",
        "employee_removed_ok": "✅ Сотрудник удалён: @{username}",
        "emp_removed": "✅ @{username} удалён.",
        "emp_remove_fail": "❌ @{username} не найден.",
        "invite_created": "Инвайт-ссылка для @{username}:\n{link}\nПерешлите её сотруднику.",
        "invite_used_success": "Добро пожаловать! Ваша роль — СОТРУДНИК.",
        "invite_username_mismatch": "⚠️ Внимание: ваш username отличается от указанного в инвайте.",
        "enter_username_error": "Неверный username. Пожалуйста, укажите с @.",
        "emp_added": "✅ @{username} добавлен.\nИнвайт: {link}",
        "emp_add_fail": "❌ Не удалось добавить @{username}.",

        "btn_request_invite": "🔗 Запросить инвайт",
        "invite_ask_username_fullname": "Для запроса инвайта отправьте @username и Имя.\nНапример: @whoop_uz Абдувахид",
        "invite_request_saved": "✅ Запрос принят. После решения администратора вы получите уведомление.",
        "invite_request_exists": "ℹ️ У вас уже есть активный запрос. Ожидайте решения.",
        "btn_admin_invites": "📨 Инвайты",
        "invites_title": "Запросы инвайтов:",
        "pending_invites_title": "🧾 Pending invites:",
        "invites_empty": "Новых запросов нет.",
        "invite_row": "• #{id} @{username} — {full_name} — статус: {status}",
        "btn_invite_accept": "✅ Принять",
        "btn_invite_reject": "❌ Отклонить",
        "invite_accept_ok": "✅ Запрос одобрен.",
        "invite_reject_ok": "❌ Запрос отклонён.",

        "task_assigned_to": "Новая задача: {title}\nДедлайн: {deadline}\nПриоритет: {priority}",
        "task_assigned": "Новая задача: {title}\nДедлайн: {deadline}\nПриоритет: {priority}",
        "task_assigned_manager_ok": "✅ Задача назначена @{username} (ID: {task_id}).",
        "task_created": "✅ Задача создана (ID: {task_id}).",
        "no_tasks": "Пока нет задач.",
        "your_tasks_header": "Ваши задачи:",
        "task_line": "• #{id} [{priority}] {title} — статус: {status}, дедлайн: {deadline}",
        "task_controls": "Задача #{task_id}\n{title}\nДедлайн: {deadline}\nПриоритет: {priority}",

        "btn_task_accept": "👍 Принять",
        "btn_task_reject": "👎 Отклонить",
        "btn_task_done": "✔️ Готово",
        "ask_reject_reason": "Отправьте причину отклонения (кратко).",
        "reject_saved_ok": "✅ Причина сохранена.",
        "task_accepted_ok": "✅ Задача принята.",
        "task_rejected_ok": "❌ Задача отклонена.",
        "task_already_decided": "ℹ️ По задаче уже принято решение.",
        "task_done_ok": "✅ Задача #{task_id} выполнена!",
        "task_done_notify_manager": "Сотрудник @{username} выполнил задачу #{task_id}.",

        "notify_task_accepted": "👤 @{username} ПРИНЯЛ(А) задачу #{task_id}.",
        "notify_task_rejected": "👤 @{username} ОТКЛОНИЛ(А) задачу #{task_id}. Причина: {reason}",
        "notify_task_done": "👤 @{username} ВЫПОЛНИЛ(А) задачу #{task_id}.",

        "daily_morning": "⏰ Напоминание 9:00: проверьте задачи.",
        "daily_evening": "⏰ Напоминание 18:00: отправьте отчёт за сегодня (/report).",
        "reminder_morning": "⏰ Напоминание 9:00: проверьте задачи.",
        "reminder_evening": "⏰ Напоминание 18:00: отправьте отчёт за сегодня (/report).",
        "deadline_soon": "⏳ Напоминание: дедлайн задачи #{task_id} «{title}» скоро ({deadline}).",
        "deadline_ping": "⏳ Напоминание: приближается срок — {task}",

        "report_prompt": "Отправьте краткий отчёт за сегодня.",
        "report_saved": "✅ Отчёт сохранён. Спасибо!",
        "manager_status_header": "Статус сотрудников:",
        "manager_status_item": "@{username}: всего {total}, выполнено {done}, открыто {open}",
        "manager_report_header": "Дневной отчёт ({date}):",
        "manager_report_line": "@{username}: выполнено {done}, открыто {open}",

        "assign_task_prompt": "Отправьте в формате:\n/task @username \"текст задачи\" 2025-08-25 18:00 [High]",
        "task_usage": "Отправьте в формате:\n/task @username \"текст задачи\" 2025-08-25 18:00 [High]",
        "voice_parsed": "Распознано из голоса: @{username} — {title} — {deadline} — {priority}",
        "date_inferred_today": "📅 Дата не указана — принята сегодняшняя: {date}",
        "date_inferred_tomorrow": "📅 Понято как «завтра»: {date}",
        "date_parsed_ok": "📅 Дата определена: {date}",
        "priority_parsed_ok": "🔥 Приоритет: {priority}",
        "parsed_from_voice": "🎙️ Из голоса: \"{title}\" — {deadline} — {priority}",

        "done_usage": "Использование: /done <task_id>",
        "done_ok": "✅ Задача #{task_id} выполнена!",
        "done_fail": "❌ #{task_id} не найдено или не принадлежит вам.",
    },

    "kk": {
        "role_manager": "МЕНЕДЖЕР",
        "role_employee": "ҚЫЗМЕТКЕР",
        "welcome_manager": "Сәлеметсіз бе! Бұл менеджер панелі. Тапсырма беріңіз, жағдайын қадағалаңыз, есеп алыңыз.",
        "welcome_employee": "Сәлеметсіз бе! Бұл сіздің жеке тақтаңыз.",
        "welcome_invite_required": "Ботты пайдалану үшін әкімші беретін INVITE сілтеме қажет.\nСұрауды төмендегі түймеден жіберіңіз.",

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
        "btn_back": "◀️ Артқа",

        "btn_set_lang_uz": "🇺🇿 O‘zbekcha",
        "btn_set_lang_ru": "🇷🇺 Русский",
        "btn_set_lang_kk": "🇰🇿 Қазақша",
        "choose_language": "Тілді таңдаңыз:",
        "lang_set_ok": "Тіл орнатылды: {lang}",
        "language_set": "Тіл орнатылды: {lang}",

        "only_private": "Ботты тек жеке чатта пайдаланыңыз.",
        "not_authorized": "Кешіріңіз, бұл бұйрық тек менеджерлерге арналған.",
        "only_manager": "Кешіріңіз, бұл бұйрық тек менеджерлерге арналған.",
        "unknown_command": "Белгісіз бұйрық. Түймелерді пайдаланыңыз.",
        "help_text": "Негізгі бұйрықтар: /start, /task, /status, /report, /mytasks, /done",

        "btn_employees": "👤 Қызметкерлер",
        "employees_menu_title": "Қызметкерлер бөлімі:",
        "employees_title": "Қызметкерлер бөлімі:",
        "btn_employees_list": "📋 Тізім",
        "btn_employee_add": "➕ Қосу",
        "btn_employee_remove": "🗑️ Жою",
        "btn_employee_invite": "🔗 Шақыру сілтемесі",
        "btn_emp_list": "📋 Тізім",
        "btn_emp_add": "➕ Қосу",
        "btn_emp_remove": "🗑️ Жою",
        "employees_list_header": "Белсенді қызметкерлер:",
        "employees_list_line": "• @{username} — {full_name}",
        "no_employees": "Әзірге белсенді қызметкерлер жоқ.",
        "employees_empty": "Әзірге белсенді қызметкерлер жоқ.",
        "prompt_employee_username": "@username жіберіңіз (мысалы, @aidos).",
        "emp_add_hint": "Қызметкер қосу үшін @username жіберіңіз (мысалы, @aidos).",
        "emp_remove_hint": "Жою үшін де @username жіберіңіз.",
        "employee_removed_ok": "✅ Қызметкер жойылды: @{username}",
        "emp_removed": "✅ @{username} жойылды.",
        "emp_remove_fail": "❌ @{username} табылмады.",
        "invite_created": "@{username} үшін шақыру сілтемесі:\n{link}\nБұл сілтемені қызметкерге жіберіңіз.",
        "invite_used_success": "Қош келдіңіз! Сіздің рөліңіз — ҚЫЗМЕТКЕР.",
        "invite_username_mismatch": "⚠️ Ескерту: сіздің username шақырудағыдан өзгеше.",
        "enter_username_error": "Дұрыс емес username. Өтінеміз, @ таңбасымен жазыңыз.",
        "emp_added": "✅ @{username} қосылды.\nШақыру: {link}",
        "emp_add_fail": "❌ @{username} қосу мүмкін болмады.",

        "btn_request_invite": "🔗 Шақыру сұрау",
        "invite_ask_username_fullname": "Шақыру сұрау үшін @username және Атыңызды жіберіңіз.\nМысалы: @whoop_uz Абдувахид",
        "invite_request_saved": "✅ Сұрауыңыз қабылданды. Әкімші шешімінен кейін хабар береміз.",
        "invite_request_exists": "ℹ️ Белсенді сұрауыңыз бар. Шешімді күтіңіз.",
        "btn_admin_invites": "📨 Шақырулар",
        "invites_title": "Шақыру сұраулары:",
        "pending_invites_title": "🧾 Pending invites:",
        "invites_empty": "Жаңа сұраулар жоқ.",
        "invite_row": "• #{id} @{username} — {full_name} — күйі: {status}",
        "btn_invite_accept": "✅ Қабылдау",
        "btn_invite_reject": "❌ Қайтару",
        "invite_accept_ok": "✅ Сұрау қабылданды.",
        "invite_reject_ok": "❌ Сұрау қайтарылды.",

        "task_assigned_to": "Жаңа тапсырма: {title}\nДедлайн: {deadline}\nБасымдылық: {priority}",
        "task_assigned": "Жаңа тапсырма: {title}\nДедлайн: {deadline}\nБасымдылық: {priority}",
        "task_assigned_manager_ok": "✅ Тапсырма @{username} қолданушысына тағайындалды (ID: {task_id}).",
        "task_created": "✅ Тапсырма құрылды (ID: {task_id}).",
        "no_tasks": "Әзірге тапсырмалар жоқ.",
        "your_tasks_header": "Сіздің тапсырмаларыңыз:",
        "task_line": "• #{id} [{priority}] {title} — күйі: {status}, дедлайн: {deadline}",
        "task_controls": "Тапсырма #{task_id}\n{title}\nДедлайн: {deadline}\nБасымдылық: {priority}",

        "btn_task_accept": "👍 Қабылдау",
        "btn_task_reject": "👎 Қайтару",
        "btn_task_done": "✔️ Орындалды",
        "ask_reject_reason": "Қайтару себебін қысқаша жазыңыз.",
        "reject_saved_ok": "✅ Себеп сақталды.",
        "task_accepted_ok": "✅ Тапсырма қабылданды.",
        "task_rejected_ok": "❌ Тапсырма қайтарылды.",
        "task_already_decided": "ℹ️ Бұл тапсырма бойынша шешім бұрын қабылданған.",
        "task_done_ok": "✅ #{task_id} тапсырмасы орындалды!",
        "task_done_notify_manager": "Қызметкер @{username} #{task_id} тапсырмасын аяқтады.",

        "notify_task_accepted": "👤 @{username} #{task_id} тапсырмасын ҚАБЫЛДАДЫ.",
        "notify_task_rejected": "👤 @{username} #{task_id} тапсырмасын ҚАЙТАРДЫ. Себеп: {reason}",
        "notify_task_done": "👤 @{username} #{task_id} тапсырмасын ОРЫНДАДЫ.",

        "daily_morning": "⏰ 9:00 еске салу: тапсырмаларыңызды тексеріңіз.",
        "daily_evening": "⏰ 18:00 еске салу: бүгінгі есепті жіберіңіз (/report).",
        "reminder_morning": "⏰ 9:00 еске салу: тапсырмаларыңызды тексеріңіз.",
        "reminder_evening": "⏰ 18:00 еске салу: бүгінгі есепті жіберіңіз (/report).",
        "deadline_soon": "⏳ Еске салу: #{task_id} «{title}» тапсырмасының дедлайны жақын ({deadline}).",
        "deadline_ping": "⏳ Еске салу: мерзімі жақындады — {task}",

        "report_prompt": "Бүгінгі есепті қысқаша жіберіңіз.",
        "report_saved": "✅ Есеп сақталды. Рақмет!",
        "manager_status_header": "Қызметкерлердің жағдайы:",
        "manager_status_item": "@{username}: барлығы {total}, орындалды {done}, ашық {open}",
        "manager_report_header": "Күндік есеп ({date}):",
        "manager_report_line": "@{username}: орындалды {done}, ашық {open}",

        "assign_task_prompt": "Формат:\n/task @username \"тапсырма мәтіні\" 2025-08-25 18:00 [High]",
        "task_usage": "Формат:\n/task @username \"тапсырма мәтіні\" 2025-08-25 18:00 [High]",
        "voice_parsed": "Дауыс тану нәтижесі: @{username} — {title} — {deadline} — {priority}",
        "date_inferred_today": "📅 Күн көрсетілмеген — бүгінгі күн қабылданды: {date}",
        "date_inferred_tomorrow": "📅 «Ертең» деп түсінілді: {date}",
        "date_parsed_ok": "📅 Күні анықталды: {date}",
        "priority_parsed_ok": "🔥 Басымдылық: {priority}",
        "parsed_from_voice": "🎙️ Дауыс бойынша: \"{title}\" — {deadline} — {priority}",

        "done_usage": "Пайдалану: /done <task_id>",
        "done_ok": "✅ #{task_id} тапсырмасы орындалды!",
        "done_fail": "❌ #{task_id} табылмады немесе сізге тиесілі емес.",
    }
}

DEFAULT_LANG = "uz"

def T(lang: str, key: str, **kwargs) -> str:
    """Matnni i18n lug‘atdan oladi. Noma’lum key bo‘lsa, default til yoki key qaytadi."""
    lang = lang if lang in STRINGS else DEFAULT_LANG
    s = STRINGS[lang].get(key) or STRINGS[DEFAULT_LANG].get(key) or key
    try:
        return s.format(**kwargs)
    except Exception:
        return s

# Kichik alias (compat)
t = T

# === ALIASES & PATCHES (backward compatibility) ===
def _alias(lang: str, src: str, dst: str):
    if lang in STRINGS and src in STRINGS[lang] and dst not in STRINGS[lang]:
        STRINGS[lang][dst] = STRINGS[lang][src]

def _ensure(lang: str, key: str, value: str):
    if lang in STRINGS and key not in STRINGS[lang]:
        STRINGS[lang][key] = value

for lg in ("uz", "ru", "kk"):
    _alias(lg, "btn_my_tasks", "btn_mytasks")
    _alias(lg, "btn_send_report", "btn_report_today")
    _alias(lg, "employees_menu_title", "employees_title")
    _alias(lg, "btn_employees_list", "btn_emp_list")
    _alias(lg, "btn_employee_add", "btn_emp_add")
    _alias(lg, "btn_employee_remove", "btn_emp_remove")
    _alias(lg, "no_employees", "employees_empty")
    _alias(lg, "lang_set_ok", "language_set")
    _alias(lg, "task_assigned_to", "task_assigned")
    _alias(lg, "assign_task_prompt", "task_usage")
    _alias(lg, "daily_morning", "reminder_morning")
    _alias(lg, "daily_evening", "reminder_evening")
    _alias(lg, "deadline_soon", "deadline_ping")

# Minimal fallbacks
_ensure("uz", "btn_back", "◀️ Orqaga")
_ensure("ru", "btn_back", "◀️ Назад")
_ensure("kk", "btn_back", "◀️ Артқа")
