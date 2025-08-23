# bot.py
# PTB v21.6 + JobQueue (extras) uchun kengaytirilgan bot (reply-keyboard + AI Task Agent)
# Python 3.11+
import asyncio
import logging
import os
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
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
db = Database(getattr(Config, "DATABASE_PATH", "taskbot.db"))

TZ = Config.TIMEZONE if isinstance(Config.TIMEZONE, ZoneInfo) else ZoneInfo(str(Config.TIMEZONE))

def to_time(v, default_str: str) -> time:
    if isinstance(v, time):
        return v
    s = str(v or default_str)
    try:
        hh, mm = s.split(":")[:2]
        return time(int(hh), int(mm))
    except Exception:
        hh, mm = default_str.split(":")[:2]
        return time(int(hh), int(mm))

MORNING_TIME = to_time(getattr(Config, "MORNING_REMINDER", "09:00"), "09:00")
EVENING_TIME = to_time(getattr(Config, "EVENING_REMINDER", "18:00"), "18:00")
REPORT_TIME  = to_time(getattr(Config, "DAILY_REPORT_TIME", "18:00"), "18:00")

# ------------------ Labels (reply keyboard) ------------------
LBL_TASK      = "📝 Vazifa berish"
LBL_STATUS    = "📊 Holat"
LBL_REPORTS   = "🧾 Hisobotlar"
LBL_EMPLOYEES = "👤 Hodimlar"
LBL_INVITES   = "🔗 Invaytlar"
LBL_LANG      = "🌐 Til"
LBL_MY_TASKS  = "✅ Mening vazifalarim"
LBL_SEND_REP  = "🧾 Hisobot yuborish"

# ------------------ Foydali yordamchilar ------------------
def is_manager(user) -> bool:
    if user is None:
        return False
    tid = user.id
    uname = (user.username or "").lower()
    ids = {int(x) for x in str(getattr(Config, "MANAGER_IDS", "") or "").split(",") if x.strip().isdigit()}
    unames = {u.strip().lstrip("@").lower() for u in str(getattr(Config, "MANAGER_USERNAMES", "") or "").split(",") if u.strip()}
    return tid in ids or (uname and uname in unames)

def kb_inline(rows):
    return InlineKeyboardMarkup([[InlineKeyboardButton(txt, callback_data=data) for (txt, data) in row] for row in rows])

def manager_home_kb(lang: str):
    rows = [
        [KeyboardButton(LBL_TASK), KeyboardButton(LBL_STATUS)],
        [KeyboardButton(LBL_REPORTS), KeyboardButton(LBL_EMPLOYEES)],
        [KeyboardButton(LBL_INVITES), KeyboardButton(LBL_LANG)],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def employee_home_kb(lang: str):
    rows = [
        [KeyboardButton(LBL_MY_TASKS), KeyboardButton(LBL_SEND_REP)],
        [KeyboardButton(LBL_LANG)],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def ensure_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
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
    t = text.lower().strip()

    # 1) YYYY-MM-DD
    m = DATE_RE_YMD.search(t)
    if m:
        y, mon, d = map(int, m.groups())
        tm = TIME_RE_HHMM.search(t)
        hh, mm = (0, 0)
        if tm:
            hh = int(tm.group(1)); mm = int(tm.group(2))
        try:
            return datetime(y, mon, d, hh, mm, tzinfo=TZ)
        except Exception:
            pass

    # 2) DD.MM.YYYY
    m = DATE_RE_DMY.search(t)
    if m:
        d, mon, y = m.groups()
        d, mon, y = int(d), int(mon), int(y)
        if y < 100:  # 25 => 2025
            y += 2000
        tm = TIME_RE_HHMM.search(t)
        hh, mm = (0, 0)
        if tm:
            hh = int(tm.group(1)); mm = int(tm.group(2))
        try:
            return datetime(y, mon, d, hh, mm, tzinfo=TZ)
        except Exception:
            pass

    # 3) Faqat vaqt bo‘lsa → bugun
    tm = TIME_RE_HHMM.search(t)
    if tm:
        hh = int(tm.group(1)); mm = int(tm.group(2))
        today = base_dt.date()
        return datetime(today.year, today.month, today.day, hh, mm, tzinfo=TZ)

    # 4) Natural so‘zlar
    day_offset = None
    if any(w in t for w in ["ertaga", "завтра"]):
        day_offset = 1
    elif any(w in t for w in ["indin", "indinga", "послезавтра"]):
        day_offset = 2
    elif any(w in t for w in ["bugun", "сегодня", "today"]):
        day_offset = 0

    if day_offset is not None:
        hh, mm = (18, 0)
        tm = TIME_RE_HHMM.search(t)
        if tm:
            hh = int(tm.group(1)); mm = int(tm.group(2))
        target = (base_dt + timedelta(days=day_offset)).date()
        return datetime(target.year, target.month, target.day, hh, mm, tzinfo=TZ)

    return None

def parse_assignee(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.startswith("@"):
        return raw
    try:
        user = db.resolve_assignee(raw)
        if user and user.get("username"):
            return "@" + user["username"]
    except Exception:
        pass
    return None

# ------------------ OpenAI Task Agent ------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_TASK_MODEL = os.getenv("OPENAI_TASK_MODEL", "gpt-4o-mini")

async def ai_parse_nl_task(text: str, now_iso: str, known_usernames: list[str]) -> dict:
    """Tabiiy yozuvdan {assignee,title,deadline,priority} chiqaradi. JSON qaytaradi."""
    if not OPENAI_API_KEY:
        # Fallback — hech bo'lmaganda Title sifatida matn
        nat = parse_natural_deadline(text, datetime.now(TZ))
        return {
            "assignee": parse_assignee(text.split()[0] if text.split() else "") or "",
            "title": text.strip() or "No title",
            "deadline": normalize_dt(nat) if nat else "",
            "priority": "Medium",
        }
    try:
        # Import kechiktirilgan
        from openai import OpenAI
        import json
        client = OpenAI(api_key=OPENAI_API_KEY)
        system = (
            "Siz Telegram ish jarayoni uchun Task Manager agentisiz. "
            "Kirish matnidan vazifa ma'lumotlarini strukturalang. "
            "Natijani JSON qaytaring: {"
            "\"assignee\":\"@username yoki toza ism yoki null\", "
            "\"title\":\"qisqa sarlavha\", "
            "\"deadline\":\"YYYY-MM-DD HH:MM\", "
            "\"priority\":\"Low|Medium|High|Urgent\"}"
        )
        prompt = f"now_date={now_iso}\nknown_users={known_usernames}\ntext={text}"
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=OPENAI_TASK_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = resp.choices[0].message.content
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        asg = data.get("assignee") or ""
        if asg and not asg.startswith("@") and asg in known_usernames:
            asg = "@" + asg
        pr = (data.get("priority") or "Medium").title()
        return {
            "assignee": asg,
            "title": data.get("title") or "No title",
            "deadline": data.get("deadline") or "",
            "priority": pr if pr in {"Low","Medium","High","Urgent"} else "Medium",
        }
    except Exception as e:
        logger.warning("AI parse error: %s", e)
        nat = parse_natural_deadline(text, datetime.now(TZ))
        return {
            "assignee": parse_assignee(text.split()[0] if text.split() else "") or "",
            "title": text.strip() or "No title",
            "deadline": normalize_dt(nat) if nat else "",
            "priority": "Medium",
        }

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
    kb_lang = kb_inline([
        [("🇺🇿 O‘zbek", "lang:uz"), ("🇷🇺 Русский", "lang:ru"), ("🇰🇿 Қазақша", "lang:kk")],
        [(T(lang, "btn_back", default="◀️ Orqaga"), "back:home")]
    ])
    await update.effective_chat.send_message(T(lang, "choose_language"), reply_markup=kb_lang)

async def on_cb_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str):
    tg = update.effective_user
    db.set_user_language(tg.id, lang_code)
    role = db.get_user_role(tg.id)
    text = T(lang_code, "language_set")
    await update.effective_chat.send_message(
        text, reply_markup=manager_home_kb(lang_code) if role == "MANAGER" else employee_home_kb(lang_code)
    )

# ------------------ Hodimlar bo‘limi ------------------
def employees_menu_kb(lang: str):
    return kb_inline([
        [(T(lang, "btn_emp_list"), "emp:list")],
        [(T(lang, "btn_emp_add"), "emp:add"), (T(lang, "btn_emp_remove"), "emp:remove")],
        [(T(lang, "btn_back"), "back:home")]
    ])

async def cb_employees_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    await update.effective_chat.send_message(T(lang, "employees_title"), reply_markup=employees_menu_kb(lang))

async def cb_emp_list(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    emps = db.list_employees()
    if not emps:
        await update.effective_chat.send_message(T(lang, "employees_empty"), reply_markup=employees_menu_kb(lang))
        return
    lines = [T(lang, "employees_list_header")]
    for e in emps:
        lines.append(T(lang, "employees_list_line", username=e.get('username') or '-', full_name=e.get('full_name') or '-'))
    await update.effective_chat.send_message("\n".join(lines), reply_markup=employees_menu_kb(lang))

async def ask_emp_add(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    context.user_data["awaiting_emp_add_username"] = True
    await update.effective_chat.send_message(T(lang, "emp_add_hint"), reply_markup=employees_menu_kb(lang))

async def ask_emp_remove(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    context.user_data["awaiting_emp_remove"] = True
    await update.effective_chat.send_message(T(lang, "emp_remove_hint"), reply_markup=employees_menu_kb(lang))

# ------------------ Text router ------------------
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", "uz")
    text = (update.message.text or "").strip()

    # --- Admin: hodim qo‘shish oqimi (@username -> ism) ---
    if context.user_data.pop("awaiting_emp_add_username", False):
        if not text.startswith("@"):
            await update.effective_chat.send_message(T(lang, "enter_username_error"), reply_markup=employees_menu_kb(lang))
            return
        context.user_data["new_emp_username"] = text.lstrip("@")
        context.user_data["awaiting_emp_add_fullname"] = True
        await update.effective_chat.send_message("Hodim to‘liq ismini kiriting (masalan, Abduvohid):")
        return

    if context.user_data.pop("awaiting_emp_add_fullname", False):
        username = context.user_data.pop("new_emp_username", "")
        full_name = text
        try:
            ok, link = db.create_invite_for(username=username, full_name=full_name)
            if ok:
                await update.effective_chat.send_message(T(lang, "invite_created", username=username, link=link), reply_markup=employees_menu_kb(lang))
            else:
                await update.effective_chat.send_message("Invite yaratib bo‘lmadi.", reply_markup=employees_menu_kb(lang))
        except Exception as ex:
            logger.exception("Invite create failed: %s", ex)
            await update.effective_chat.send_message("Invite yaratishda xatolik.", reply_markup=employees_menu_kb(lang))
        return

    if context.user_data.pop("awaiting_emp_remove", False):
        username = text.lstrip("@")
        ok = db.remove_employee_by_username(username)
        if ok:
            await update.effective_chat.send_message(T(lang, "emp_removed", username=username), reply_markup=employees_menu_kb(lang))
        else:
            await update.effective_chat.send_message(T(lang, "emp_remove_fail", username=username), reply_markup=employees_menu_kb(lang))
        return

    # --- Invite REJECT sababi ---
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

    # --- Task REJECT sababi ---
    if context.user_data.get("awaiting_task_reject_reason"):
        task_id = context.user_data.pop("awaiting_task_reject_reason")
        reason = text
        try:
            db.set_task_status(task_id, "rejected", by=tg.id, reason=reason)
            for m in db.list_managers():
                try:
                    await context.bot.send_message(m["telegram_id"], f"❌ @{u.get('username') or '-'} #{task_id} ni rad qildi.\nSabab: {reason}")
                except Exception:
                    pass
            await update.effective_chat.send_message("❌ Vazifa rad qilindi.", reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.exception("Task reject failed: %s", ex)
            await update.effective_chat.send_message("Rad etishda xatolik.", reply_markup=employee_home_kb(lang))
        return

    # --- Task DONE hisobot matni ---
    if context.user_data.get("awaiting_task_done_report"):
        task_id = context.user_data.pop("awaiting_task_done_report")
        report = text
        try:
            ok = db.mark_task_done_with_report(task_id, tg.id, report)
            if ok:
                for m in db.list_managers():
                    try:
                        await context.bot.send_message(m["telegram_id"], T(lang, "task_done_notify_manager", username=u.get('username') or '-', task_id=task_id))
                    except Exception:
                        pass
                await update.effective_chat.send_message(T(lang, "done_ok", task_id=task_id), reply_markup=employee_home_kb(lang))
            else:
                await update.effective_chat.send_message(T(lang, "done_fail", task_id=task_id), reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.exception("Task done failed: %s", ex)
            await update.effective_chat.send_message("Xatolik sodir bo‘ldi.", reply_markup=employee_home_kb(lang))
        return

    # --- TASK WIZARD: natural language ---
    if context.user_data.pop("tw_wait_nl", False):
        now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
        known = [u.get("username") for u in db.list_all_users() if u.get("username")]
        parsed = await ai_parse_nl_task(text, now, known)

        if not parsed.get("deadline"):
            nat = parse_natural_deadline(text, datetime.now(TZ))
            if nat:
                parsed["deadline"] = normalize_dt(nat)

        assigned_to = parsed.get("assignee") or ""
        if not assigned_to:
            tok = text.split()[0] if text.split() else ""
            assigned_to = parse_assignee(tok) or ""

        task_id = db.create_task(
            title=parsed.get("title") or "(no title)",
            description=parsed.get("title") or "(no title)",
            created_by=tg.id,
            assigned_to_username=assigned_to.lstrip("@") if assigned_to else "",
            deadline=parsed.get("deadline") or "",
            priority=parsed.get("priority") or "Medium",
        )

        emp = db.get_user_by_username(assigned_to.lstrip("@")) if assigned_to else None
        if emp:
            btns = kb_inline([
                [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
                [("☑️ Bajardim", f"task:done:{task_id}")]
            ])
            try:
                await context.bot.send_message(
                    emp["telegram_id"],
                    T(emp.get("language","uz"), "task_assigned", title=parsed.get("title"), deadline=parsed.get("deadline") or "-", priority=parsed.get("priority")),
                    reply_markup=btns
                )
            except Exception as e:
                logger.warning("Notify employee failed: %s", e)

        await update.effective_chat.send_message(
            T(lang, "task_created", task_id=task_id),
            reply_markup=manager_home_kb(lang)
        )
        await schedule_task_deadline(context.application, task_id)
        return

# ------------------ Vazifa berish (/task) (slash saqlanadi) ------------------
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        await update.effective_chat.send_message(T(lang, "only_manager"))
        return

    args = update.message.text.split(maxsplit=1)
    if len(args) == 1:
        # Wizardni ishga tushiramiz
        context.user_data["tw_wait_nl"] = True
        await update.effective_chat.send_message(
            T(lang, "assign_task_prompt") + "\n\nYoki oddiy yozing: “Whoop indinga 09:00 gacha hisobotlar tayyor bo‘lsin [Urgent]”."
        )
        return

    payload = args[1].strip()
    assigned_to, title, deadline_str, priority = parse_task_command(payload)

    if not deadline_str:
        nat = parse_natural_deadline(payload, datetime.now(TZ))
        if nat:
            deadline_str = normalize_dt(nat)

    if not assigned_to:
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

    emp = db.get_user_by_username(assigned_to.lstrip("@")) if assigned_to else None
    if emp:
        btns = kb_inline([
            [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
            [("☑️ Bajardim", f"task:done:{task_id}")]
        ])
        try:
            await context.bot.send_message(
                chat_id=emp["telegram_id"],
                text=T(emp.get("language", "uz"), "task_assigned", title=title, deadline=deadline_str or "-", priority=priority),
                reply_markup=btns
            )
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(T(lang, "task_created", task_id=task_id), reply_markup=manager_home_kb(lang))
    await schedule_task_deadline(context.application, task_id)

def parse_task_command(payload: str):
    assigned = ""
    title = ""
    deadline = ""
    priority = "Medium"

    rest = payload

    if rest.startswith("@"):
        parts = rest.split(maxsplit=1)
        assigned = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
    else:
        parts = rest.split(maxsplit=1)
        if parts and parts[0].startswith("@"):
            assigned = parts[0]
            rest = parts[1] if len(parts) > 1 else ""

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

    if "[" in rest and "]" in rest:
        pr = rest[rest.index("[")+1:rest.index("]")].strip()
        if pr:
            priority = pr.title()
        rest = (rest[:rest.index("[")] + rest[rest.index("]")+1:]).strip()

    deadline = rest.strip() or ""
    try:
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline)
            deadline = normalize_dt(deadline_dt)
    except Exception:
        pass

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
        await update.effective_chat.send_message(T(lang, "only_manager"))
        return

    items = db.get_status_overview()
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
async def build_daily_report_text() -> str:
    rows = db.build_daily_summary()
    if not rows:
        return "*Bugun faoliyat bo‘yicha ma’lumot yo‘q.*"
    lines = ["*Kunlik hisobot:*"]
    for r in rows:
        lines.append(f"• @{r['username'] or '-'} — {r['completed']} done / {r['total']} total")
    return "\n".join(lines)

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        await update.effective_chat.send_message(T(lang, "only_manager"))
        return
    text = await build_daily_report_text()
    await update.effective_chat.send_message(text, parse_mode=ParseMode.MARKDOWN, reply_markup=manager_home_kb(lang))

# ------------------ Employee buyruqlari ------------------
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

async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    args = update.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await update.effective_chat.send_message(T(lang, "done_usage"))
        return
    task_id = int(args[1])
    ok = db.set_task_status(task_id, "done", by=tg.id)
    if ok:
        for m in db.list_managers():
            try:
                await context.bot.send_message(m["telegram_id"], T(lang, "task_done_notify_manager", username=u.get('username') or '-', task_id=task_id))
            except Exception:
                pass
        await update.effective_chat.send_message(T(lang, "done_ok", task_id=task_id), reply_markup=employee_home_kb(lang))
    else:
        await update.effective_chat.send_message(T(lang, "done_fail", task_id=task_id), reply_markup=employee_home_kb(lang))

async def cb_employee_report(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    await update.effective_chat.send_message(T(lang, "report_prompt"))
    context.user_data["awaiting_task_done_report"] = 0  # umumiy kundalik

# ------------------ Voice -> task ------------------
async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", "uz")
    if not is_manager(tg):
        return
    voice = update.message.voice
    if not voice:
        return
    file = await context.bot.get_file(voice.file_id)
    path = await file.download_to_drive(custom_path=f"/tmp/{voice.file_unique_id}.oga")

    # Agar OPENAI_API_KEY mavjud bo'lsa Whisper
    title = "Voice task"; assigned_to=""; deadline=""; priority="Medium"
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            with open(path, "rb") as f:
                tr = client.audio.transcriptions.create(model="whisper-1", file=f)
            txt = tr.text.strip()
            now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
            known = [u.get("username") for u in db.list_all_users() if u.get("username")]
            parsed = await ai_parse_nl_task(txt, now, known)
            title = parsed.get("title") or "Voice task"
            deadline = parsed.get("deadline") or (normalize_dt(parse_natural_deadline(txt, datetime.now(TZ))) if parse_natural_deadline(txt, datetime.now(TZ)) else "")
            priority = parsed.get("priority") or "Medium"
            assigned_to = parsed.get("assignee") or parse_assignee(txt.split()[0] if txt.split() else "") or ""
        except Exception as e:
            logger.warning("Whisper parse failed: %s", e)

    task_id = db.create_task(
        title=title,
        description=title,
        created_by=tg.id,
        assigned_to_username=assigned_to.lstrip("@") if assigned_to else "",
        deadline=deadline,
        priority=priority,
    )

    emp = db.get_user_by_username(assigned_to.lstrip("@")) if assigned_to else None
    if emp:
        btns = kb_inline([
            [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
            [("☑️ Bajardim", f"task:done:{task_id}")]
        ])
        try:
            await context.bot.send_message(
                chat_id=emp["telegram_id"],
                text=T(emp.get("language", "uz"), "task_assigned", title=title, deadline=deadline or "-", priority=priority),
                reply_markup=btns
            )
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(T(lang, "task_created", task_id=task_id), reply_markup=manager_home_kb(lang))
    await schedule_task_deadline(context.application, task_id)

# ------------------ Rejalashtirish ------------------
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
    dd = ""
    if t.get("deadline"):
        try:
            dd = datetime.fromisoformat(t["deadline"]).strftime("%Y-%m-%d %H:%M")
        except Exception:
            dd = t["deadline"]
    msg = T(lang, "deadline_ping", task=fmt_task(t)) if T(lang,"deadline_ping")!= "deadline_ping" else T(lang, "deadline_soon", task_id=task_id, title=t.get("title","-"), deadline=dd or "-")
    try:
        await app.bot.send_message(emp["telegram_id"], msg, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.warning("Deadline ping failed: %s", e)

async def schedule_user_jobs(app: Application):
    if app.job_queue is None:
        logger.warning("JobQueue yo‘q, schedule_user_jobs o‘tkazildi")
        return
    for name in ("morning_reminder", "evening_reminder"):
        for j in app.job_queue.get_jobs_by_name(name):
            j.schedule_removal()
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
    for j in app.job_queue.get_jobs_by_name(f"deadline_{task_id}"):
        j.schedule_removal()
    app.job_queue.run_once(
        callback=lambda ctx: asyncio.create_task(send_deadline_ping(ctx.application, task_id)),
        when=dt, name=f"deadline_{task_id}"
    )

async def daily_manager_report(app: Application):
    managers = db.list_managers()
    text = await build_daily_report_text()
    for m in managers:
        try:
            await app.bot.send_message(chat_id=m["telegram_id"], text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.warning("Manager report failed: %s", e)

# ------------------ Callback router ------------------
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", "uz")
    data = update.callback_query.data

    if data == "u:language":
        return await cmd_language(update, context)

    if data.startswith("lang:"):
        code = data.split(":", 1)[1]
        return await on_cb_language(update, context, code)

    # Hodimlar
    if data == "m:employees":
        return await cb_employees_menu(update, context, lang)
    if data == "emp:list":
        return await cb_emp_list(update, context, lang)
    if data == "emp:add":
        return await ask_emp_add(update, context, lang)
    if data == "emp:remove":
        return await ask_emp_remove(update, context, lang)

    # Invites paneli (pending ro‘yxat)
    if data == "m:invites":
        reqs = db.list_invite_requests()
        rows = []
        for r in reqs:
            rid = r["id"]
            title = f"@{r.get('username') or '-'} | {r.get('full_name') or '-'}"
            rows.append([(title, "noop")])
            rows.append([("✅ Qabul", f"inv:approve:{rid}"), ("❌ Rad", f"inv:reject:{rid}")])
        if not rows:
            rows = [[("— Bo‘sh —", "noop")]]
        rows.append([(T(lang, "btn_back"), "back:home")])
        return await update.effective_chat.send_message("🧾 Pending invites:", reply_markup=kb_inline(rows))

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
        context.user_data["tw_wait_nl"] = True
        await update.effective_chat.send_message("Tabiiy tilda vazifa yozing (masalan, “Whoop indinga 09:00 gacha … [Urgent]”).")
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

    # Task lifecycle
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

    if data == "back:home":
        role = db.get_user_role(tg.id)
        text = T(lang, "welcome_manager") if role == "MANAGER" else T(lang, "welcome_employee")
        await update.effective_chat.send_message(
            text, reply_markup=manager_home_kb(lang) if role == "MANAGER" else employee_home_kb(lang)
        )

# ------------------ Post-init ------------------
async def on_start(app: Application):
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

    # Slash commands (saqlanadi)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("mytasks", cmd_mytasks))
    app.add_handler(CommandHandler("done", cmd_done))

    # Reply-keyboard tugmalari
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_TASK)}$"), task_wizard_start))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_STATUS)}$"), cmd_status))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_REPORTS)}$"), cmd_report))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_EMPLOYEES)}$"),
                                   lambda u,c: cb_employees_menu(u,c,(db.get_user(u.effective_user.id) or {}).get('language','uz'))))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_INVITES)}$"),
                                   lambda u,c: on_callback_from_text(u,c,"m:invites")))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_LANG)}$"), cmd_language))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_MY_TASKS)}$"), cmd_mytasks))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_SEND_REP)}$"),
                                   lambda u,c: cb_employee_report(u,c,(db.get_user(u.effective_user.id) or {}).get('language','uz'))))

    # Callbacklar & umumiy text router
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    # Voice
    app.add_handler(MessageHandler(filters.VOICE, on_voice))

    return app

async def task_wizard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    context.user_data["tw_wait_nl"] = True
    await update.effective_chat.send_message(
        "Tabiiy tilda vazifa yozing.\nMisol: “Whoop indinga soat 09:00 gacha barcha hisobotlar tayyor bo‘lsin [Urgent]”."
    )

async def on_callback_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    class _D: pass
    d = _D(); d.data = data
    update.callback_query = d
    await on_callback(update, context)

# ------------------ main ------------------
def main():
    app = build_application()
    logger.info("Starting bot …")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        raise
