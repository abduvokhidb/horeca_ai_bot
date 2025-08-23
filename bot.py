# bot.py
# PTB v21.6 + JobQueue (extras) uchun yangilangan asosiy bot fayli
# Muvofiqlik: Python 3.11+, python-telegram-bot[job-queue]==21.6
# Xususiylik: Render Background Worker (Start Command: python bot.py)

import asyncio
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Ichki modullar
from config import Config
from database import Database
from languages import T  # T(lang, key, **kwargs) -> matn

# ------------------ Loglash ------------------
LOG_LEVEL = getattr(logging, getattr(Config, "LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("taskbot")

# ------------------ Global holat ------------------
# ⚠️ Asl xato: Database() ga 'path' berilmagan edi → tuzatildi (Config.DATABASE_PATH)
db = Database(getattr(Config, "DATABASE_PATH", "taskbot.db"))  # SQLite wrapper (sizning database.py ichida)

# ⚠️ Asl xato: Config.TIMEZONE allaqachon ZoneInfo bo‘lishi mumkin — qayta o‘ramaymiz
TZ = Config.TIMEZONE if isinstance(Config.TIMEZONE, ZoneInfo) else ZoneInfo(str(Config.TIMEZONE))

# Kunlik vaqtlardan foydalanish (tzinfo = Application.timezone orqali o‘rnatiladi)
def parse_hhmm(s: str, default: str) -> time:
    try:
        hh, mm = map(int, (s or default).split(":"))
        return time(hh, mm)
    except Exception:
        return time(*map(int, default.split(":")))

MORNING_TIME = parse_hhmm(getattr(Config, "MORNING_REMINDER", "09:00"), "09:00")
EVENING_TIME = parse_hhmm(getattr(Config, "EVENING_REMINDER", "18:00"), "18:00")
REPORT_TIME  = parse_hhmm(getattr(Config, "DAILY_REPORT_TIME", "18:00"), "18:00")

# ------------------ Foydali yordamchilar ------------------
def is_manager(user) -> bool:
    """Config dagi MANAGER_IDS yoki MANAGER_USERNAMES orqali tekshirish."""
    if user is None:
        return False
    tid = user.id
    uname = (user.username or "").lower()

    ids = set()
    for raw in str(getattr(Config, "MANAGER_IDS", "") or "").split(","):
        raw = raw.strip()
        if raw.isdigit():
            ids.add(int(raw))
    unames = {u.strip().lstrip("@").lower() for u in str(getattr(Config, "MANAGER_USERNAMES", "") or "").split(",") if u.strip()}

    return tid in ids or (uname and uname in unames)

def kb(rows):
    return InlineKeyboardMarkup([[InlineKeyboardButton(txt, callback_data=data) for (txt, data) in row] for row in rows])

async def ensure_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
    """DB da user mavjudligini ta’minlaydi va qaytaradi."""
    tg = update.effective_user
    if not tg:
        return {}
    user = db.upsert_user(
        telegram_id=tg.id,
        username=tg.username,
        full_name=f"{tg.first_name or ''} {tg.last_name or ''}".strip()
    )
    return user

def fmt_task(task) -> str:
    dd = ""
    if task.get("deadline"):
        try:
            dd = datetime.fromisoformat(task["deadline"]).strftime("%Y-%m-%d %H:%M")
        except Exception:
            dd = task["deadline"]
    pr = task.get("priority", "Medium")
    return f"#{task['id']} • {task.get('title','(no title)')} — *{task.get('status','new').upper()}* • ⏰ {dd or '-'} • 🔥 {pr}"

# ------------------ Menyular ------------------
def manager_home_kb(lang: str):
    return kb([
        [(T(lang, "btn_assign_task"), "m:assign"), (T(lang, "btn_status"), "m:status")],
        [(T(lang, "btn_reports"), "m:reports"), (T(lang, "btn_employees"), "m:employees")],
        [(T(lang, "btn_language"), "u:language")]
    ])

def employee_home_kb(lang: str):
    return kb([
        [(T(lang, "btn_mytasks"), "e:mytasks"), (T(lang, "btn_report_today"), "e:report")],
        [(T(lang, "btn_language"), "u:language")]
    ])

def employees_menu_kb(lang: str):
    return kb([
        [(T(lang, "btn_emp_list"), "emp:list")],
        [(T(lang, "btn_emp_add"), "emp:add"), (T(lang, "btn_emp_remove"), "emp:remove")],
        [(T(lang, "btn_back"), "back:home")]
    ])

# ------------------ /start ------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tguser = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", getattr(Config, "DEFAULT_LANG", "uz"))
    role = u.get("role") or ("MANAGER" if is_manager(tguser) else "EMPLOYEE")
    if u.get("role") != role:
        db.set_user_role(tguser.id, role)

    text = T(lang, "welcome_manager") if role == "MANAGER" else T(lang, "welcome_employee")
    await update.effective_chat.send_message(
        text=text,
        reply_markup=manager_home_kb(lang) if role == "MANAGER" else employee_home_kb(lang),
        parse_mode=ParseMode.HTML
    )

# ------------------ Tilni almashtirish ------------------
async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    kb_lang = kb([
        [("🇺🇿 O‘zbek", "lang:uz"), ("🇷🇺 Русский", "lang:ru"), ("🇰🇿 Қазақ", "lang:kz")],
        [(T(lang, "btn_back"), "back:home")]
    ])
    await update.effective_chat.send_message(T(lang, "choose_language"), reply_markup=kb_lang)

async def on_cb_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str):
    tg = update.effective_user
    db.set_user_language(tg.id, lang_code)
    # Ko‘rinadigan menyu
    role = db.get_user_role(tg.id)
    text = T(lang_code, "language_set")
    await update.effective_chat.send_message(
        text, reply_markup=manager_home_kb(lang_code) if role == "MANAGER" else employee_home_kb(lang_code)
    )

# ------------------ Hodimlar bo‘limi ------------------
async def cb_employees_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    await update.effective_chat.send_message(T(lang, "employees_title"), reply_markup=employees_menu_kb(lang))

async def cb_emp_list(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    emps = db.list_employees()
    if not emps:
        await update.effective_chat.send_message(T(lang, "employees_empty"), reply_markup=employees_menu_kb(lang))
        return
    lines = []
    for e in emps:
        lines.append(f"• @{e.get('username') or '-'} — {e.get('full_name') or '-'} (ID: {e['telegram_id']})")
    # FIX: .ing -> .join
    await update.effective_chat.send_message("\n".join(lines), reply_markup=employees_menu_kb(lang))

async def ask_emp_add(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    context.user_data["awaiting_emp_add"] = True
    await update.effective_chat.send_message(T(lang, "emp_add_hint"), reply_markup=employees_menu_kb(lang))

async def ask_emp_remove(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    context.user_data["awaiting_emp_remove"] = True
    await update.effective_chat.send_message(T(lang, "emp_remove_hint"), reply_markup=employees_menu_kb(lang))

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnli xabarlar uchun holatga qarab yo‘naltirish (hodim qo‘shish/uchirish kutilsa)."""
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", "uz")

    text = (update.message.text or "").strip()
    if context.user_data.pop("awaiting_emp_add", False):
        username = text.lstrip("@")
        ok, link = db.add_employee_by_username(username)
        if ok:
            await update.effective_chat.send_message(T(lang, "emp_added", username=username, link=link), reply_markup=employees_menu_kb(lang))
        else:
            await update.effective_chat.send_message(T(lang, "emp_add_fail", username=username), reply_markup=employees_menu_kb(lang))
        return

    if context.user_data.pop("awaiting_emp_remove", False):
        username = text.lstrip("@")
        ok = db.remove_employee_by_username(username)
        if ok:
            await update.effective_chat.send_message(T(lang, "emp_removed", username=username), reply_markup=employees_menu_kb(lang))
        else:
            await update.effective_chat.send_message(T(lang, "emp_remove_fail", username=username), reply_markup=employees_menu_kb(lang))
        return

# ------------------ Vazifa berish (/task) ------------------
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        await update.effective_chat.send_message(T(lang, "only_manager"))
        return

    # Format: /task @username "task matn" 2025-08-25 18:00 [High]
    args = update.message.text.split(maxsplit=1)
    if len(args) == 1:
        await update.effective_chat.send_message(T(lang, "task_usage"))
        return

    payload = args[1].strip()
    assigned_to, title, deadline_str, priority = parse_task_command(payload)

    task_id = db.create_task(
        title=title,
        description=title,
        created_by=tg.id,
        assigned_to_username=assigned_to.lstrip("@"),
        deadline=deadline_str,
        priority=priority,
    )

    # Xodimga bildirishnoma
    emp = db.get_user_by_username(assigned_to.lstrip("@"))
    if emp:
        try:
            await context.bot.send_message(
                chat_id=emp["telegram_id"],
                text=T(emp.get("language", "uz"), "task_assigned", title=title, deadline=deadline_str, priority=priority),
                reply_markup=kb([[(T(emp.get("language","uz"), "btn_mytasks"), "e:mytasks")]])
            )
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(T(lang, "task_created", task_id=task_id), reply_markup=manager_home_kb(lang))

    # Deadline eslatmasini qo‘yish
    await schedule_task_deadline(context.application, task_id)

def parse_task_command(payload: str):
    # Juda oddiy parser; sizda AI bilan boyitilgan bo‘lishi mumkin
    # Kutiladigan ko‘rinish: @username "task matn" 2025-08-25 18:00 [High]
    assigned = ""
    title = ""
    deadline = ""
    priority = "Medium"

    # username
    if payload.startswith("@"):
        parts = payload.split(maxsplit=1)
        assigned = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
    else:
        rest = payload

    # title
    if '"' in rest:
        try:
            first = rest.index('"')
            second = rest.index('"', first+1)
            title = rest[first+1:second].strip()
            rest = (rest[:first] + rest[second+1:]).strip()
        except ValueError:
            title = rest
            rest = ""
    else:
        title = rest
        rest = ""

    # deadline + priority
    if "[" in rest and "]" in rest:
        pr = rest[rest.index("[")+1:rest.index("]")].strip()
        if pr:
            priority = pr.title()
        rest = (rest[:rest.index("[")] + rest[rest.index("]")+1:]).strip()

    # qolganini deadline sifatida qabul qilamiz
    deadline = rest.strip() or ""

    # ISO normalize (agar bo‘lsa)
    try:
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline)
            deadline = deadline_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    return assigned, title or "(no title)", deadline, priority

# ------------------ /status (manager) ------------------
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        await update.effective_chat.send_message(T(lang, "only_manager"))
        return

    items = db.get_status_overview()  # [(employee, [tasks])]
    lines = []
    for row in items:
        emp = row["employee"]
        tasks = row["tasks"]
        lines.append(f"👤 @{emp.get('username') or '-'} — {emp.get('full_name') or '-'}")
        if not tasks:
            lines.append("  • —")
        else:
            for t in tasks:
                lines.append("  • " + fmt_task(t))
    await update.effective_chat.send_message("\n".join(lines), reply_markup=manager_home_kb(lang), parse_mode=ParseMode.MARKDOWN)

# ------------------ /report (manager) ------------------
async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        await update.effective_chat.send_message(T(lang, "only_manager"))
        return
    text = await build_daily_report_text()
    await update.effective_chat.send_message(text, parse_mode=ParseMode.MARKDOWN, reply_markup=manager_home_kb(lang))

# ------------------ /mytasks (employee) ------------------
async def cmd_mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    tasks = db.list_tasks_for_user(tg.id)
    if not tasks:
        await update.effective_chat.send_message(T(lang, "no_tasks"), reply_markup=employee_home_kb(lang))
        return
    lines = [fmt_task(t) for t in tasks]
    await update.effective_chat.send_message("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=employee_home_kb(lang))

# ------------------ /done (employee) ------------------
async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    args = update.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await update.effective_chat.send_message(T(lang, "done_usage"))
        return
    task_id = int(args[1])
    ok = db.mark_task_done(task_id, tg.id)
    if ok:
        await update.effective_chat.send_message(T(lang, "done_ok", task_id=task_id), reply_markup=employee_home_kb(lang))
    else:
        await update.effective_chat.send_message(T(lang, "done_fail", task_id=task_id), reply_markup=employee_home_kb(lang))

# ------------------ Xodim kundalik hisobot (employee) ------------------
async def cb_employee_report(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    # Oddiy: bugun bajarilganlar soni
    cnt = db.count_completed_today(update.effective_user.id)
    db.save_report(update.effective_user.id, f"Completed today: {cnt}", cnt)
    await update.effective_chat.send_message(T(lang, "report_saved", count=cnt), reply_markup=employee_home_kb(lang))

# ------------------ Voice -> task (manager ovozi) ------------------
async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        return
    voice = update.message.voice
    if not voice:
        return
    # Ovoz faylini olish
    file = await context.bot.get_file(voice.file_id)
    path = await file.download_to_drive(custom_path=f"/tmp/{voice.file_unique_id}.oga")
    # Whisper (ixtiyoriy)
    title, assigned_to, deadline, priority = await ai_parse_voice(str(path))
    task_id = db.create_task(
        title=title,
        description=title,
        created_by=tg.id,
        assigned_to_username=assigned_to.lstrip("@") if assigned_to else "",
        deadline=deadline,
        priority=priority or "Medium",
    )
    await update.effective_chat.send_message(T(lang, "task_created", task_id=task_id), reply_markup=manager_home_kb(lang))
    await schedule_task_deadline(context.application, task_id)

async def ai_parse_voice(path: str):
    """OPENAI_API_KEY bo‘lsa: ovoz->matn, so‘ng soddalashtirilgan ajratish."""
    import os
    assigned_to = ""
    title = "Voice task"
    deadline = ""
    priority = "Medium"

    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            with open(path, "rb") as f:
                tr = client.audio.transcriptions.create(model="whisper-1", file=f)
            text = tr.text.strip()
            # juda soddalashtirilgan parse (AI majburiymas)
            assigned_to, title, deadline, priority = parse_task_command(text)
        except Exception as e:
            logger.warning("Whisper parse failed: %s", e)
    return title, assigned_to, deadline, priority

# ------------------ Rejalashtirish: eslatmalar & hisobot ------------------
async def schedule_user_jobs(app: Application):
    if app.job_queue is None:
        logger.warning("JobQueue yo‘q, schedule_user_jobs o‘tkazildi")
        return

    # Avval mavjud ishlarga dublikat qo‘ymaslik uchun tozalash
    for name in ("morning_reminder", "evening_reminder"):
        for j in app.job_queue.get_jobs_by_name(name):
            j.schedule_removal()

    # Har kuni 9:00 va 18:00 da barcha xodimlarga eslatma
    app.job_queue.run_daily(
        callback=lambda ctx: asyncio.create_task(send_daily_reminder(ctx.application, when="morning")),
        time=MORNING_TIME, days=(0,1,2,3,4,5,6), name="morning_reminder"
    )
    app.job_queue.run_daily(
        callback=lambda ctx: asyncio.create_task(send_daily_reminder(ctx.application, when="evening")),
        time=EVENING_TIME, days=(0,1,2,3,4,5,6), name="evening_reminder"
    )
    logger.info("Daily reminders scheduled at %s and %s", MORNING_TIME, EVENING_TIME)

async def schedule_daily_manager_report(app: Application):
    if app.job_queue is None:
        logger.warning("JobQueue yo‘q, schedule_daily_manager_report o‘tkazildi")
        return
    for j in app.job_queue.get_jobs_by_name("daily_manager_report"):
        j.schedule_removal()
    app.job_queue.run_daily(
        callback=lambda ctx: asyncio.create_task(daily_manager_report(ctx.application)),
        time=REPORT_TIME, days=(0,1,2,3,4,5,6), name="daily_manager_report"
    )
    logger.info("Daily manager report scheduled at %s", REPORT_TIME)

async def schedule_task_deadline(app: Application, task_id: int):
    if app.job_queue is None:
        return
    task = db.get_task(task_id)
    if not task or not task.get("deadline"):
        return
    try:
        dt = datetime.fromisoformat(task["deadline"])
    except Exception:
        return
    # Agar naive bo‘lsa, Application.timezone (TZ) default sifatida ishlatiladi.
    for j in app.job_queue.get_jobs_by_name(f"deadline_{task_id}"):
        j.schedule_removal()
    app.job_queue.run_once(
        callback=lambda ctx: asyncio.create_task(send_deadline_ping(ctx.application, task_id)),
        when=dt, name=f"deadline_{task_id}"
    )

# --- Callback implementatsiyalari ---
async def send_daily_reminder(app: Application, when: str):
    employees = db.list_employees()
    for e in employees:
        lang = e.get("language", "uz")
        text = T(lang, "reminder_morning") if when == "morning" else T(lang, "reminder_evening")
        try:
            await app.bot.send_message(chat_id=e["telegram_id"], text=text, reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.warning("Reminder failed to %s: %s", e.get("username"), ex)

async def send_deadline_ping(app: Application, task_id: int):
    t = db.get_task(task_id)
    if not t:
        return
    emp = db.get_user(t["assigned_to"])
    if not emp:
        return
    lang = emp.get("language", "uz")
    msg = T(lang, "deadline_ping", task=fmt_task(t))
    try:
        await app.bot.send_message(emp["telegram_id"], msg, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.warning("Deadline ping failed: %s", e)

async def build_daily_report_text() -> str:
    rows = db.build_daily_summary()
    if not rows:
        return "*Bugun faoliyat bo‘yicha ma’lumot yo‘q.*"
    lines = ["*Kunlik hisobot:*"]
    for r in rows:
        lines.append(f"• @{r['username'] or '-'} — {r['completed']} done / {r['total']} total")
    return "\n".join(lines)

async def daily_manager_report(app: Application):
    # Manager(lar)ga yuborish
    managers = db.list_managers()
    text = await build_daily_report_text()
    for m in managers:
        try:
            await app.bot.send_message(chat_id=m["telegram_id"], text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.warning("Manager report failed: %s", e)

# ------------------ Callbacks router ------------------
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", "uz")
    data = update.callback_query.data

    # Til
    if data.startswith("lang:"):
        code = data.split(":", 1)[1]
        return await on_cb_language(update, context, code)

    # Hodimlar bo‘limi
    if data == "m:employees":
        return await cb_employees_menu(update, context, lang)
    if data == "emp:list":
        return await cb_emp_list(update, context, lang)
    if data == "emp:add":
        return await ask_emp_add(update, context, lang)
    if data == "emp:remove":
        return await ask_emp_remove(update, context, lang)

    # Manager menyulari
    if data == "m:assign":
        await update.effective_chat.send_message(T(lang, "task_usage"))
        return
    if data == "m:status":
        return await cmd_status(update, context)
    if data == "m:reports":
        return await cmd_report(update, context)

    # Employee menyulari
    if data == "e:mytasks":
        return await cmd_mytasks(update, context)
    if data == "e:report":
        return await cb_employee_report(update, context, lang)

    # Orqaga
    if data == "back:home":
        role = db.get_user_role(tg.id)
        text = T(lang, "welcome_manager") if role == "MANAGER" else T(lang, "welcome_employee")
        await update.effective_chat.send_message(
            text, reply_markup=manager_home_kb(lang) if role == "MANAGER" else employee_home_kb(lang)
        )

# ------------------ Post-init: ishga tushganda rejalashtirish ------------------
async def on_start(app: Application):
    await schedule_user_jobs(app)
    await schedule_daily_manager_report(app)
    logger.info("Startup scheduling done")

# ------------------ Application builder ------------------
def build_application() -> Application:
    app = (
        Application
        .builder()
        .token(Config.TELEGRAM_BOT_TOKEN)
        .timezone(TZ)  # MUHIM: PTB v21 uchun default tz
        .post_init(on_start)
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("language", cmd_language))

    # Manager
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("report", cmd_report))

    # Employee
    app.add_handler(CommandHandler("mytasks", cmd_mytasks))
    app.add_handler(CommandHandler("done", cmd_done))

    # Callbacks
    app.add_handler(CallbackQueryHandler(on_callback))

    # Text router (hodim qo‘shish/uchirish uchun kutilgan holatlar)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    # Voice (manager uchun task yaratish)
    app.add_handler(MessageHandler(filters.VOICE, on_voice))

    return app

# ------------------ main ------------------
def main():
    app = build_application()
    logger.info("Starting bot …")
    # drop_pending_updates=True – eski navbatni tozalash
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        raise
