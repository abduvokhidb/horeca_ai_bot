# bot.py
# PTB v21.6 + JobQueue (extras) uchun kengaytirilgan bot
# Muvofiqlik: Python 3.11+, python-telegram-bot[job-queue]==21.6
# Xususiylik: Render Background Worker (Start Command: python bot.py)

import asyncio
import logging
import re
from datetime import datetime, date, time, timedelta
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
db = Database(getattr(Config, "DATABASE_PATH", "taskbot.db"))  # SQLite wrapper

# Timezone: Config.TIMEZONE allaqachon ZoneInfo bo‘lishi mumkin — qayta o‘ramaymiz
TZ = Config.TIMEZONE if isinstance(Config.TIMEZONE, ZoneInfo) else ZoneInfo(str(Config.TIMEZONE))

# Kunlik vaqtlardan foydalanish (tzinfo = JobQueue.set_timezone orqali o‘rnatiladi)
def to_time(v, default_str: str) -> time:
    """Config dan keladigan 'HH:MM'/'HH:MM:SS' str yoki time obyektini time ga aylantiradi."""
    if isinstance(v, time):
        return v
    s = str(v or default_str)
    try:
        parts = s.split(":")
        if len(parts) >= 2:
            hh = int(parts[0])
            mm = int(parts[1])
            return time(hh, mm)
    except Exception:
        pass
    p = default_str.split(":")
    return time(int(p[0]), int(p[1]))

MORNING_TIME = to_time(getattr(Config, "MORNING_REMINDER", "09:00"), "09:00")
EVENING_TIME = to_time(getattr(Config, "EVENING_REMINDER", "18:00"), "18:00")
REPORT_TIME  = to_time(getattr(Config, "DAILY_REPORT_TIME", "18:00"), "18:00")

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

# ------- Aqlli sana/vaqt parserlari -------
DATE_RE_DMY = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b")   # 24.09.2025
DATE_RE_YMD = re.compile(r"\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b")     # 2025-09-24
TIME_RE_HHMM = re.compile(r"\b(\d{1,2}):(\d{2})\b")

def normalize_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_natural_deadline(text: str, base_dt: datetime) -> datetime | None:
    """
    'bugun', 'ertaga', 'indin/indinga', ruscha 'сегодня/завтра/послезавтра' kabi so'zlar,
    'DD.MM.YYYY HH:MM', 'YYYY-MM-DD HH:MM', faqat 'HH:MM' bo‘lsa — bugungi sana.
    """
    t = text.lower().strip()

    # 1) To‘liq sana + vaqt (YMD yoki DMY)
    m = DATE_RE_YMD.search(t)
    if m:
        y, mon, d = map(int, m.groups())
        # vaqt bormi?
        tm = TIME_RE_HHMM.search(t)
        hh, mm = (0, 0)
        if tm:
            hh = int(tm.group(1)); mm = int(tm.group(2))
        try:
            return datetime(y, mon, d, hh, mm, tzinfo=TZ)
        except Exception:
            pass

    m = DATE_RE_DMY.search(t)
    if m:
        d, mon, y = m.groups()
        d, mon, y = int(d), int(mon), int(y)
        if y < 100:  # 25 => 2025 deb qabul qilamiz (zarur bo‘lsa sozlang)
            y += 2000
        tm = TIME_RE_HHMM.search(t)
        hh, mm = (0, 0)
        if tm:
            hh = int(tm.group(1)); mm = int(tm.group(2))
        try:
            return datetime(y, mon, d, hh, mm, tzinfo=TZ)
        except Exception:
            pass

    # 2) Faqqat vaqt ('10:00') va sana yo‘q → bugun
    tm = TIME_RE_HHMM.search(t)
    if tm:
        hh = int(tm.group(1)); mm = int(tm.group(2))
        today = base_dt.date()
        try:
            return datetime(today.year, today.month, today.day, hh, mm, tzinfo=TZ)
        except Exception:
            pass

    # 3) Natural so‘zlar: bugun/ertaga/indin(ga), ruscha
    day_offset = 0
    if any(w in t for w in ["ertaga", "завтра"]):
        day_offset = 1
    elif any(w in t for w in ["indin", "indinga", "послезавтра"]):
        day_offset = 2
    elif any(w in t for w in ["bugun", "сегодня", "today"]):
        day_offset = 0
    else:
        # Hech narsa topilmasa None
        return None

    # Offset + default time (18:00) yoki text ichidagi vaqt
    hh, mm = (18, 0)
    tm = TIME_RE_HHMM.search(t)
    if tm:
        hh = int(tm.group(1)); mm = int(tm.group(2))
    target_day = (base_dt + timedelta(days=day_offset)).date()
    try:
        return datetime(target_day.year, target_day.month, target_day.day, hh, mm, tzinfo=TZ)
    except Exception:
        return None

def parse_assignee(raw: str) -> str | None:
    """@username yoki ismni qaytarish uchun: agar @ bo‘lsa to‘g‘ridan, aks holda DB orqali resolve qilamiz."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.startswith("@"):
        return raw
    # Ism bo‘lishi mumkin — DB orqali topamiz (username qaytarsa '@' bilan birga return qilamiz)
    try:
        user = db.resolve_assignee(raw)  # ism/username orqali topadi (siz database.py da yozasiz)
        if user and user.get("username"):
            return "@" + user["username"]
    except Exception:
        pass
    return None

# ------------------ Menyular ------------------
def manager_home_kb(lang: str):
    # Invites bo‘limi qo‘shildi
    return kb([
        [(T(lang, "btn_assign_task"), "m:assign"), (T(lang, "btn_status"), "m:status")],
        [(T(lang, "btn_reports"), "m:reports"), (T(lang, "btn_employees"), "m:employees")],
        [(T(lang, "btn_employee_invite") or "Invites", "m:invites"), (T(lang, "btn_language"), "u:language")],
    ])

def employee_home_kb(lang: str):
    return kb([
        [(T(lang, "btn_my_tasks"), "e:mytasks"), (T(lang, "btn_send_report"), "e:report")],
        [(T(lang, "btn_language"), "u:language")]
    ])

def employees_menu_kb(lang: str):
    return kb([
        [(T(lang, "btn_employees_list"), "emp:list")],
        [(T(lang, "btn_employee_add"), "emp:add"), (T(lang, "btn_employee_remove"), "emp:remove")],
        [(T(lang, "btn_cancel"), "back:home")]
    ])

def invite_requests_kb(lang: str, requests: list[dict]):
    """Admin uchun pending invite requestlar ro‘yxati inline tugmalar bilan."""
    rows = []
    for r in requests:
        rid = r["id"]
        title = f"@{r.get('username') or '-'} | {r.get('full_name') or '-'}"
        rows.append([(title, "noop")])
        rows.append([
            (T(lang, "btn_assign_task") or "✅ Qabul", f"inv:approve:{rid}"),
            (T(lang, "btn_cancel") or "❌ Rad", f"inv:reject:{rid}")
        ])
    if not rows:
        rows = [[(T(lang, "no_employees") or "Bo‘sh", "noop")]]
    rows.append([(T(lang, "btn_cancel"), "back:home")])
    return kb(rows)

# ------------------ /start ------------------
async def cmd_start(update: Update, context: ContextTypes.DefaultType = None):
    tguser = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", getattr(Config, "DEFAULT_LANG", "uz"))
    role = u.get("role") or ("MANAGER" if is_manager(tguser) else "EMPLOYEE")
    if u.get("role") != role:
        db.set_user_role(tguser.id, role)

    # Agar hodim aktyor emas (admin tasdig‘i yo‘q) bo‘lsa — invite so‘rashi kerak
    if role != "MANAGER":
        try:
            is_active = db.is_user_active(tguser.id)  # siz database.py da implement qilasiz
        except Exception:
            is_active = True  # agar implement qilinmagan bo‘lsa, bloklamaymiz

        if not is_active:
            text = (
                T(lang, "only_private") + "\n\n" +
                (T(lang, "invite_used_success") or "Sizga admin tomonidan invite link yuborilishi bilan botdan foydalana olasiz.")
            )
            markup = kb([
                [(T(lang, "btn_employee_invite") or "🔗 Invite so‘rash", "req:invite")],
                [(T(lang, "btn_cancel"), "back:home")]
            ])
            await update.effective_chat.send_message(text=text, reply_markup=markup)
            return

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
        [("🇺🇿 O‘zbek", "lang:uz"), ("🇷🇺 Русский", "lang:ru"), ("🇰🇿 Қазақша", "lang:kk")],
        [(T(lang, "btn_cancel"), "back:home")]
    ])
    await update.effective_chat.send_message(T(lang, "choose_language"), reply_markup=kb_lang)

async def on_cb_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str):
    tg = update.effective_user
    db.set_user_language(tg.id, lang_code)
    # Ko‘rinadigan menyu
    role = db.get_user_role(tg.id)
    text = T(lang_code, "lang_set_ok", lang=lang_code) or f"Language set: {lang_code}"
    await update.effective_chat.send_message(
        text, reply_markup=manager_home_kb(lang_code) if role == "MANAGER" else employee_home_kb(lang_code)
    )

# ------------------ Hodimlar bo‘limi ------------------
async def cb_employees_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    await update.effective_chat.send_message(T(lang, "employees_menu_title"), reply_markup=employees_menu_kb(lang))

async def cb_emp_list(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    emps = db.list_employees()
    if not emps:
        await update.effective_chat.send_message(T(lang, "no_employees"), reply_markup=employees_menu_kb(lang))
        return
    lines = [T(lang, "employees_list_header")]
    for e in emps:
        lines.append(T(lang, "employees_list_line", username=e.get('username') or '-', full_name=e.get('full_name') or '-'))
    await update.effective_chat.send_message("\n".join(lines), reply_markup=employees_menu_kb(lang))

async def ask_emp_add(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    context.user_data["awaiting_emp_add_username"] = True
    await update.effective_chat.send_message(T(lang, "prompt_employee_username"), reply_markup=employees_menu_kb(lang))

async def ask_emp_remove(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    context.user_data["awaiting_emp_remove"] = True
    await update.effective_chat.send_message(T(lang, "prompt_employee_username"), reply_markup=employees_menu_kb(lang))

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnli xabarlar uchun holatga qarab yo‘naltirish:
       - hodim qo‘shish: @username -> so‘ng ism
       - hodim o‘chirish
       - invite reject sababi
       - taskni rad qilish sababi
       - taskni 'bajardim' hisobot matni
    """
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", "uz")
    role = u.get("role") or ("MANAGER" if is_manager(tg) else "EMPLOYEE")
    text = (update.message.text or "").strip()

    # --- Admin: hodim qo‘shish oqimi ---
    if context.user_data.pop("awaiting_emp_add_username", False):
        if not text.startswith("@"):
            await update.effective_chat.send_message(T(lang, "enter_username_error"), reply_markup=employees_menu_kb(lang))
            return
        context.user_data["new_emp_username"] = text.lstrip("@")
        context.user_data["awaiting_emp_add_fullname"] = True
        await update.effective_chat.send_message(T(lang, "report_prompt") or "Hodim ismini kiriting (masalan, Abduvohid).")
        return

    if context.user_data.pop("awaiting_emp_add_fullname", False):
        username = context.user_data.pop("new_emp_username", "")
        full_name = text
        try:
            ok, link = db.create_invite_for(username=username, full_name=full_name)
            if ok:
                await update.effective_chat.send_message(T(lang, "invite_created", username=username, link=link), reply_markup=employees_menu_kb(lang))
            else:
                await update.effective_chat.send_message((T(lang, "unknown_command") or "Xatolik."), reply_markup=employees_menu_kb(lang))
        except Exception as ex:
            logger.exception("Invite create failed: %s", ex)
            await update.effective_chat.send_message("Invite yaratishda xatolik.", reply_markup=employees_menu_kb(lang))
        return

    if context.user_data.pop("awaiting_emp_remove", False):
        username = text.lstrip("@")
        ok = db.remove_employee_by_username(username)
        if ok:
            await update.effective_chat.send_message(T(lang, "employee_removed_ok", username=username), reply_markup=employees_menu_kb(lang))
        else:
            await update.effective_chat.send_message((T(lang, "unknown_command") or "Bunday hodim topilmadi."), reply_markup=employees_menu_kb(lang))
        return

    # --- Admin: invite REJECT sababi ---
    if context.user_data.get("awaiting_inv_reject_for"):
        req_id = context.user_data.pop("awaiting_inv_reject_for")
        reason = text
        try:
            db.reject_invite_request(req_id, reason)
            await update.effective_chat.send_message("❌ Invite so‘rovi rad etildi.", reply_markup=manager_home_kb(lang))
        except Exception as ex:
            logger.exception("Reject invite failed: %s", ex)
            await update.effective_chat.send_message("Rad etishda xatolik.", reply_markup=manager_home_kb(lang))
        return

    # --- Employee: task REJECT sababi ---
    if context.user_data.get("awaiting_task_reject_reason"):
        task_id = context.user_data.pop("awaiting_task_reject_reason")
        reason = text
        try:
            db.set_task_status(task_id, "rejected", by=tg.id, reason=reason)
            # Manager(lar)ga xabar
            managers = db.list_managers()
            for m in managers:
                try:
                    await context.bot.send_message(m["telegram_id"], f"❌ @{u.get('username') or '-'} #{task_id} ni rad qildi.\nSabab: {reason}")
                except Exception:
                    pass
            await update.effective_chat.send_message("❌ Vazifa rad qilindi.", reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.exception("Task reject failed: %s", ex)
            await update.effective_chat.send_message("Rad etishda xatolik.", reply_markup=employee_home_kb(lang))
        return

    # --- Employee: task DONE hisobot matni ---
    if context.user_data.get("awaiting_task_done_report"):
        task_id = context.user_data.pop("awaiting_task_done_report")
        report = text
        try:
            ok = db.mark_task_done_with_report(task_id, tg.id, report)
            if ok:
                # Manager(lar)ga bildirish
                managers = db.list_managers()
                for m in managers:
                    try:
                        await context.bot.send_message(
                            m["telegram_id"],
                            T(lang, "task_done_notify_manager", username=u.get('username') or '-', task_id=task_id)
                        )
                    except Exception:
                        pass
                await update.effective_chat.send_message(T(lang, "task_done_ok", task_id=task_id), reply_markup=employee_home_kb(lang))
            else:
                await update.effective_chat.send_message("Holatni o‘zgartirish imkonsiz.", reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.exception("Task done failed: %s", ex)
            await update.effective_chat.send_message("Xatolik sodir bo‘ldi.", reply_markup=employee_home_kb(lang))
        return

# ------------------ Vazifa berish (/task) ------------------
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        await update.effective_chat.send_message(T(lang, "not_authorized"))
        return

    # Format: /task @username "task matn" 2025-08-25 18:00 [High]
    args = update.message.text.split(maxsplit=1)
    if len(args) == 1:
        await update.effective_chat.send_message(T(lang, "assign_task_prompt"))
        return

    payload = args[1].strip()
    assigned_to, title, deadline_str, priority = parse_task_command(payload)

    # Agar sana berilmagan bo‘lsa yoki faqat vaqt bo‘lsa → bugungi sana
    if not deadline_str:
        nat = parse_natural_deadline(payload, datetime.now(TZ))
        if nat:
            deadline_str = normalize_dt(nat)

    # Xodim: @username yo‘q bo‘lsa ism orqali topish
    if not assigned_to:
        # birinchi tokenni assignee sifatida qabul qilishga urinib ko‘ramiz
        maybe = payload.split()[0]
        assigned_to = parse_assignee(maybe) or ""

    task_id = db.create_task(
        title=title,
        description=title,
        created_by=tg.id,
        assigned_to_username=assigned_to.lstrip("@") if assigned_to else "",
        deadline=deadline_str,
        priority=priority,
    )

    # Xodimga bildirishnoma + inline tugmalar
    emp = None
    if assigned_to:
        emp = db.get_user_by_username(assigned_to.lstrip("@"))
    if emp:
        try:
            btns = kb([  # Qabul / Rad / Bajardim
                [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
                [("☑️ Bajardim", f"task:done:{task_id}")]
            ])
            await context.bot.send_message(
                chat_id=emp["telegram_id"],
                text=T(emp.get("language", "uz"), "task_assigned_to", title=title, deadline=deadline_str or "-", priority=priority),
                reply_markup=btns
            )
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(
        T(lang, "task_assigned_manager_ok", username=(assigned_to or "-").lstrip("@"), task_id=task_id),
        reply_markup=manager_home_kb(lang)
    )

    # Deadline eslatma
    await schedule_task_deadline(context.application, task_id)

def parse_task_command(payload: str):
    """
    Kutiladigan ko‘rinishlar:
      @username "task matn" 2025-08-25 18:00 [High]
      Abduvohid "task matn" 10:00 [High]         (ism orqali)
      "task matn" ertaga 09:00 [Low]             (assignee keyin belgilanadi)
    """
    assigned = ""
    title = ""
    deadline = ""
    priority = "Medium"

    rest = payload

    # username/ism
    if rest.startswith("@"):
        parts = rest.split(maxsplit=1)
        assigned = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
    else:
        # Birinchi so‘zni assignee bo‘lishi mumkin deb ajratib olamiz, keyin tekshiramiz
        parts = rest.split(maxsplit=1)
        if parts:
            maybe_assignee = parts[0]
            if maybe_assignee.startswith("@"):
                assigned = maybe_assignee
                rest = parts[1] if len(parts) > 1 else ""
            else:
                # Ism bo‘lishi mumkin — hozircha restdan olib qo‘ymaymiz, keyin parse_assignee() da tekshiramiz
                pass

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
        # Birinchi katta bo‘limni sarlavha deb olish qiyin, shuning uchun qolganini vaqt/sana/piority ni olib tashlab, title deb qabul qilamiz
        title = rest
        rest = ""

    # deadline + priority [High]
    if "[" in rest and "]" in rest:
        pr = rest[rest.index("[")+1:rest.index("]")].strip()
        if pr:
            priority = pr.title()
        rest = (rest[:rest.index("[")] + rest[rest.index("]")+1:]).strip()

    # qolganini deadline sifatida qabul qilamiz
    deadline = rest.strip() or ""

    # Agar deadline matni ISO bo‘lsa normalize
    try:
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline)
            deadline = normalize_dt(deadline_dt)
    except Exception:
        # Natural parserdan keyin normalize qilamiz (cmd_task ichida)
        pass

    # Ism bo‘lsa resolve
    if not assigned:
        first_token = payload.split()[0] if payload.split() else ""
        assigned = parse_assignee(first_token) or ""

    return assigned, (title or "(no title)"), deadline, priority

# ------------------ /status (manager) ------------------
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        await update.effective_chat.send_message(T(lang, "not_authorized"))
        return

    items = db.get_status_overview()  # [(employee, [tasks])]
    lines = [T(lang, "manager_status_header")]
    for row in items:
        emp = row["employee"]
        tasks = row["tasks"]
        uname = emp.get('username') or '-'
        fname = emp.get('full_name') or '-'
        lines.append(f"👤 @{uname} — {fname}")
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
        await update.effective_chat.send_message(T(lang, "not_authorized"))
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
    lines = [T(lang, "your_tasks_header")]
    lines.extend([fmt_task(t) for t in tasks])
    await update.effective_chat.send_message("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=employee_home_kb(lang))

# ------------------ /done (employee) ------------------
async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    args = update.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await update.effective_chat.send_message((T(lang, "help_text") or "Foydalanish: /done <task_id>"))
        return
    task_id = int(args[1])
    # Hisobotsiz oddiy done
    ok = db.set_task_status(task_id, "done", by=tg.id)
    if ok:
        managers = db.list_managers()
        for m in managers:
            try:
                await context.bot.send_message(m["telegram_id"], T(lang, "task_done_notify_manager", username=u.get('username') or '-', task_id=task_id))
            except Exception:
                pass
        await update.effective_chat.send_message(T(lang, "task_done_ok", task_id=task_id), reply_markup=employee_home_kb(lang))
    else:
        await update.effective_chat.send_message("Holatni o‘zgartirish imkonsiz.", reply_markup=employee_home_kb(lang))

# ------------------ Xodim kundalik hisobot (employee) ------------------
async def cb_employee_report(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    # Qisqacha matn so‘rash
    await update.effective_chat.send_message(T(lang, "report_prompt"))
    context.user_data["awaiting_task_done_report"] = 0  # 0 => umumiy kundalik (taskga bog‘liq emas)

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
    # Sana yo‘q bo‘lsa natural parser
    if not deadline:
        nat = parse_natural_deadline(title, datetime.now(TZ))  # gap ichidan ham vaqt topishi mumkin
        if nat:
            deadline = normalize_dt(nat)
    # Assignee yo‘q bo‘lsa ism/username dan topish
    if not assigned_to:
        first_token = title.split()[0] if title.split() else ""
        assigned_to = parse_assignee(first_token) or ""

    task_id = db.create_task(
        title=title,
        description=title,
        created_by=tg.id,
        assigned_to_username=assigned_to.lstrip("@") if assigned_to else "",
        deadline=deadline,
        priority=priority or "Medium",
    )
    # xodimga xabar
    emp = None
    if assigned_to:
        emp = db.get_user_by_username(assigned_to.lstrip("@"))
    if emp:
        try:
            btns = kb([
                [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
                [("☑️ Bajardim", f"task:done:{task_id}")]
            ])
            await context.bot.send_message(
                chat_id=emp["telegram_id"],
                text=T(emp.get("language", "uz"), "task_assigned_to", title=title, deadline=deadline or "-", priority=priority or "Medium"),
                reply_markup=btns
            )
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(
        T(lang, "task_assigned_manager_ok", username=(assigned_to or "-").lstrip("@"), task_id=task_id),
        reply_markup=manager_home_kb(lang)
    )
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
            # juda soddalashtirilgan parse
            a2, t2, d2, p2 = parse_task_command(text)
            assigned_to = a2 or ""
            title = t2 or "Voice task"
            # Natural date
            nat = parse_natural_deadline(text, datetime.now(TZ))
            if nat:
                deadline = normalize_dt(nat)
            else:
                deadline = d2 or ""
            priority = p2 or "Medium"
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
    # Agar naive bo‘lsa, JobQueue timezone ishlatiladi.
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
        text = T(lang, "daily_morning") if when == "morning" else T(lang, "daily_evening")
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
    # deadline_soon kalitiga mos
    dd = ""
    if t.get("deadline"):
        try:
            dd = datetime.fromisoformat(t["deadline"]).strftime("%Y-%m-%d %H:%M")
        except Exception:
            dd = t["deadline"]
    msg = T(lang, "deadline_soon", task_id=task_id, title=t.get("title","-"), deadline=dd or "-")
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

    # Til menyusini ochish
    if data == "u:language":
        return await cmd_language(update, context)

    # Tilni o‘rnatish
    if data.startswith("lang:"):
        code = data.split(":", 1)[1]
        return await on_cb_language(update, context, code)

    # Invite so‘rash (employee)
    if data == "req:invite":
        try:
            db.create_invite_request(tg.id, u.get("username"), u.get("full_name"))
            await update.effective_chat.send_message("✅ So‘rovingiz yuborildi. Admin tasdiqlashini kuting.")
            # Admin(lar)ga xabar
            for m in db.list_managers():
                try:
                    await context.bot.send_message(
                        m["telegram_id"],
                        f"🆕 Invite so‘rovi: @{u.get('username') or '-'} — {u.get('full_name') or '-'}"
                    )
                except Exception:
                    pass
        except Exception as ex:
            logger.exception("Invite request failed: %s", ex)
            await update.effective_chat.send_message("Xatolik: so‘rov yuborilmadi.")
        return

    # Hodimlar bo‘limi
    if data == "m:employees":
        return await cb_employees_menu(update, context, lang)
    if data == "emp:list":
        return await cb_emp_list(update, context, lang)
    if data == "emp:add":
        return await ask_emp_add(update, context, lang)
    if data == "emp:remove":
        return await ask_emp_remove(update, context, lang)

    # Invites (admin paneli)
    if data == "m:invites":
        reqs = db.list_invite_requests()
        return await update.effective_chat.send_message("🧾 Pending invites:", reply_markup=invite_requests_kb(lang, reqs))

    if data.startswith("inv:approve:"):
        rid = int(data.split(":")[-1])
        try:
            link = db.approve_invite_request(rid)
            await update.effective_chat.send_message(f"✅ Tasdiqlandi.\n🔗 Invite: {link}", reply_markup=manager_home_kb(lang))
        except Exception as ex:
            logger.exception("Approve invite failed: %s", ex)
            await update.effective_chat.send_message("Tasdiqlashda xatolik.", reply_markup=manager_home_kb(lang))
        return

    if data.startswith("inv:reject:"):
        rid = int(data.split(":")[-1])
        context.user_data["awaiting_inv_reject_for"] = rid
        await update.effective_chat.send_message("Rad etish sababini yuboring:")
        return

    # Manager menyulari
    if data == "m:assign":
        await update.effective_chat.send_message(T(lang, "assign_task_prompt"))
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

    # Task lifecycle: accept/reject/done
    if data.startswith("task:acc:"):
        task_id = int(data.split(":")[-1])
        try:
            db.set_task_status(task_id, "accepted", by=tg.id)
            await update.effective_chat.send_message("✅ Vazifa qabul qilindi.", reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.exception("Task accept failed: %s", ex)
            await update.effective_chat.send_message("Qabul qilishda xatolik.", reply_markup=employee_home_kb(lang))
        return

    if data.startswith("task:rej:"):
        task_id = int(data.split(":")[-1])
        context.user_data["awaiting_task_reject_reason"] = task_id
        await update.effective_chat.send_message("Rad etish sababini yuboring:")
        return

    if data.startswith("task:done:"):
        task_id = int(data.split(":")[-1])
        context.user_data["awaiting_task_done_report"] = task_id
        await update.effective_chat.send_message("Qisqacha hisobot yuboring (nima bajarildi):")
        return

    # Orqaga
    if data == "back:home":
        role = db.get_user_role(tg.id)
        text = T(lang, "welcome_manager") if role == "MANAGER" else T(lang, "welcome_employee")
        await update.effective_chat.send_message(
            text, reply_markup=manager_home_kb(lang) if role == "MANAGER" else employee_home_kb(lang)
        )

# ------------------ Post-init: ishga tushganda rejalashtirish ------------------
async def on_start(app: Application):
    # PTB v21.6: ApplicationBuilder.timezone() yo‘q -> JobQueue ga timezone o‘rnatiladi
    if app.job_queue:
        try:
            app.job_queue.set_timezone(TZ)
        except Exception:
            try:
                app.job_queue.scheduler.configure(timezone=TZ)  # type: ignore[attr-defined]
            except Exception as e:
                logger.warning("Timezone set failed: %s", e)
    await schedule_user_jobs(app)
    await schedule_daily_manager_report(app)
    logger.info("Startup scheduling done")

# ------------------ Application builder ------------------
def build_application() -> Application:
    app = (
        Application
        .builder()
        .token(Config.TELEGRAM_BOT_TOKEN)
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

    # Text router (hodim qo‘shish/uchirish, sabablari, hisobotlar)
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
