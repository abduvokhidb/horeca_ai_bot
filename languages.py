# languages.py
DEFAULT_LANG = "uz"

STRINGS = {
    "uz": {
        "welcome_manager": "Assalomu alaykum! Menejer paneli: vazifa bering, holatni ko‘ring, hisobot oling.",
        "welcome_employee": "Assalomu alaykum! Bu sizning shaxsiy ish panelingiz.",
        "choose_language": "Tilni tanlang:",
        "language_set": "Til o‘rnatildi: {lang}",
        "only_manager": "Kechirasiz, bu bo‘lim faqat menejerlar uchun.",
        "unknown_command": "Tushunarsiz buyruq. Pastdagi tugmalardan foydalaning.",

        # Menyular
        "btn_back": "◀️ Orqaga",
        "btn_emp_list": "📋 Ro‘yxat",
        "btn_emp_add": "➕ Qo‘shish",
        "btn_emp_remove": "🗑️ O‘chirish",

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

        # Tasks
        "assign_task_prompt": "Quyidagi formatda yuboring:\n/task @username \"vazifa\" 10:00 24.09.2025 [High]",
        "task_assigned": "Yangi vazifa: {title}\nMuddat: {deadline}\nUstuvorlik: {priority}",
        "task_created": "✅ Vazifa yaratildi (ID: {task_id}).",
        "no_tasks": "Hozircha vazifalar yo‘q.",
        "your_tasks_header": "Sizning vazifalaringiz:",
        "done_usage": "Foydalanish: /done <task_id>",
        "done_ok": "✅ #{task_id} vazifasi bajarildi!",
        "done_fail": "❌ #{task_id} topilmadi yoki sizga tegishli emas.",
        "task_done_notify_manager": "Xodim @{username} #{task_id} vazifasini tugatdi.",

        # Status/Report
        "manager_status_header": "Xodimlar holati:",
        "reminder_morning": "⏰ 9:00 eslatma: vazifalaringizni ko‘rib chiqing.",
        "reminder_evening": "⏰ 18:00 eslatma: bugungi hisobotni yuboring.",
        "deadline_ping": "⏳ Eslatma: vazifa yaqinlashdi — {task}",

        # Invites / Requests (yangi)
        "invites_title": "🧾 Pending so‘rovlar:",
        "pending_info": "🕒 So‘rovingiz *admin tasdig‘ida*. Tasdiqlangach, panel ochiladi.",
        "new_request_text": "🆕 Yangi so‘rov: @{username} — {full_name}\nID: {uid}",
        "approved_user": "✅ Siz tasdiqlandingiz! Endi paneldan foydalanishingiz mumkin.",
        "rejected_user": "❌ So‘rov rad etildi.\nSabab: {reason}",
        "btn_approve": "✅ Qabul qilish",
        "btn_reject": "❌ Rad etish",
        "btn_refresh": "🔄 Statusni tekshirish",
        "pending_wait": "⏳ Sizning akkauntingiz tasdiqlanmoqda. Admin qabul qilgach, menyu ochiladi.",
    },
    "ru": {
        "welcome_manager": "Здравствуйте! Панель менеджера: назначайте задачи, смотрите статус, получайте отчёты.",
        "welcome_employee": "Здравствуйте! Это ваша личная панель.",
        "choose_language": "Выберите язык:",
        "language_set": "Язык установлен: {lang}",
        "only_manager": "Извините, раздел доступен только менеджерам.",
        "unknown_command": "Неизвестная команда. Используйте кнопки ниже.",

        "btn_back": "◀️ Назад",
        "btn_emp_list": "📋 Список",
        "btn_emp_add": "➕ Добавить",
        "btn_emp_remove": "🗑️ Удалить",

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
        "reminder_morning": "⏰ Напоминание 9:00: проверьте задачи.",
        "reminder_evening": "⏰ Напоминание 18:00: отправьте отчёт.",
        "deadline_ping": "⏳ Напоминание: приближается срок — {task}",

        "invites_title": "🧾 Запросы на одобрение:",
        "pending_info": "🕒 Ваша заявка *ожидает одобрения*. После одобрения панель откроется.",
        "new_request_text": "🆕 Новый запрос: @{username} — {full_name}\nID: {uid}",
        "approved_user": "✅ Вас одобрили! Теперь вы можете пользоваться панелью.",
        "rejected_user": "❌ Заявка отклонена.\nПричина: {reason}",
        "btn_approve": "✅ Принять",
        "btn_reject": "❌ Отклонить",
        "btn_refresh": "🔄 Проверить статус",
        "pending_wait": "⏳ Ваша учётная запись ожидает одобрения. После одобрения меню откроется.",
    },
    "kk": {
        "welcome_manager": "Сәлем! Менеджер панелі: тапсырма беріңіз, күйін қараңыз, есеп алыңыз.",
        "welcome_employee": "Сәлем! Бұл сіздің жеке панеліңіз.",
        "choose_language": "Тілді таңдаңыз:",
        "language_set": "Тіл орнатылды: {lang}",
        "only_manager": "Кешіріңіз, бұл бөлім тек менеджерлерге.",
        "unknown_command": "Белгісіз команда. Төмендегі түймелерді пайдаланыңыз.",

        "btn_back": "◀️ Артқа",
        "btn_emp_list": "📋 Тізім",
        "btn_emp_add": "➕ Қосу",
        "btn_emp_remove": "🗑️ Жою",

        "employees_title": "Қызметкерлер бөлімі:",
        "employees_empty": "Әзірге белсенді қызметкерлер жоқ.",
        "employees_list_header": "Белсенді қызметкерлер:",
        "employees_list_line": "• @{username} — {full_name}",
        "emp_add_hint": "Қызметкер қосу үшін @username жіберіңіз (мысалы, @aidos).",
        "emp_remove_hint": "Жою үшін де @username жіберіңіз.",
        "enter_username_error": "Дұрыс емес username. @ таңбасымен жіберіңіз.",
        "emp_removed": "✅ @{username} жойылды.",
        "emp_remove_fail": "❌ @{username} табылмады.",
        "invite_created": "@{username} үшін шақыру сілтемесі:\n{link}",

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
        "reminder_morning": "⏰ 9:00 еске салу: тапсырмаларыңызды тексеріңіз.",
        "reminder_evening": "⏰ 18:00 еске салу: бүгінгі есепті жіберіңіз.",
        "deadline_ping": "⏳ Еске салу: мерзім жақындады — {task}",

        "invites_title": "🧾 Мақұлдауға сұраулар:",
        "pending_info": "🕒 Сұрауыңыз *мақұлдауды күтуде*. Мақұлданған соң панель ашылады.",
        "new_request_text": "🆕 Жаңа сұрау: @{username} — {full_name}\nID: {uid}",
        "approved_user": "✅ Сіз мақұлдандыңыз! Енді панельді қолдана аласыз.",
        "rejected_user": "❌ Сұрау қайтарылды.\nСебебі: {reason}",
        "btn_approve": "✅ Қабылдау",
        "btn_reject": "❌ Қайтару",
        "btn_refresh": "🔄 Статусты тексеру",
        "pending_wait": "⏳ Есептік жазбаңыз мақұлдауды күтуде. Әкімші мақұлдаған соң мәзір ашылады.",
    },
}

def T(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in STRINGS else DEFAULT_LANG
    s = STRINGS[lang].get(key) or STRINGS[DEFAULT_LANG].get(key) or key
    try:
        return s.format(**kwargs)
    except Exception:
        return s
