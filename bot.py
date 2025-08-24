# bot.py — PTB v21.6
import asyncio, logging, os, re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, ContextTypes, filters,
)

from config import Config
from database import Database
from languages import T

LOG_LEVEL = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("taskbot")

db = Database(Config.DATABASE_PATH)
TZ: ZoneInfo = Config.TIMEZONE

def _to_time(s: str, default: str) -> time:
    try:
        hh, mm = (s or default).split(":", 1)
        return time(int(hh), int(mm))
    except Exception:
        hh, mm = default.split(":", 1)
        return time(int(hh), int(mm))

MORNING_TIME = _to_time(Config.MORNING_REMINDER, "09:00")
EVENING_TIME = _to_time(Config.EVENING_REMINDER, "18:00")
REPORT_TIME  = _to_time(Config.DAILY_REPORT_TIME, "18:00")

# Reply-keyboard labels
LBL_TASK      = "📝 Vazifa berish"
LBL_STATUS    = "📊 Holat"
LBL_REPORTS   = "🧾 Hisobotlar"
LBL_EMPLOYEES = "👤 Hodimlar"
LBL_INVITES   = "📨 So‘rovlar"
LBL_LANG      = "🌐 Til"
LBL_MY_TASKS  = "✅ Mening vazifalarim"
LBL_SEND_REP  = "🧾 Hisobot yuborish"

def is_manager(user) -> bool:
    if not user: return False
    tid = user.id
    ids = {int(x) for x in (Config.MANAGER_IDS or "").split(",") if x.strip().isdigit()}
    unames = {u.strip().lower() for u in (Config.MANAGER_USERNAMES or "").split(",") if u.strip()}
    return (tid in ids) or ((user.username or "").lower() in unames)

def kb_inline(rows: List[List[tuple]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(txt, callback_data=cd) for (txt, cd) in row] for row in rows])

def manager_home_kb(lang: str) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(LBL_TASK), KeyboardButton(LBL_STATUS)],
        [KeyboardButton(LBL_REPORTS), KeyboardButton(LBL_EMPLOYEES)],
        [KeyboardButton(LBL_INVITES), KeyboardButton(LBL_LANG)],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def employee_home_kb(lang: str) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(LBL_MY_TASKS), KeyboardButton(LBL_SEND_REP)],
        [KeyboardButton(LBL_LANG)],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def ensure_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
    tg = update.effective_user
    if not tg: return {}
    user = db.upsert_user(tg.id, tg.username, f"{tg.first_name or ''} {tg.last_name or ''}".strip())
    if not user.get("role"):
        # auto-assign role for configured managers
        role = "MANAGER" if is_manager(tg) else "EMPLOYEE"
        db.set_user_role(tg.id, role)
        user["role"] = role
    return user

def fmt_task(t: dict) -> str:
    dd = "-"
    if t.get("deadline"):
        try: dd = datetime.fromisoformat(t["deadline"]).strftime("%Y-%m-%d %H:%M")
        except Exception: dd = t["deadline"]
    return f"#{t['id']} • {t.get('title','(no title)')} — *{t.get('status','new').upper()}* • ⏰ {dd} • 🔥 {t.get('priority','Medium')}"

# Natural date parsing (supports HH:MM DD.MM.YYYY)
RE_DMY = re.compile(r"\b(\d{1,2})[.](\d{1,2})[.](\d{4})\b")
RE_TIME = re.compile(r"\b(\d{1,2}):(\d{2})\b")

def normalize_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_deadline_hhmm_dmy(text: str, base: datetime) -> Optional[str]:
    """Siz so‘ragan format: HH:MM DD.MM.YYYY (agar sanasiz bo‘lsa — bugun)"""
    t = text.strip()
    tm = RE_TIME.search(t)
    date = RE_DMY.search(t)
    if tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
    else:
        return None
    if date:
        d, m, y = map(int, date.groups())
        try:
            return normalize_dt(datetime(y, m, d, hh, mm, tzinfo=TZ))
        except Exception:
            return None
    # faqat vaqt — bugun
    today = base.date()
    return normalize_dt(datetime(today.year, today.month, today.day, hh, mm, tzinfo=TZ))

def parse_assignee(token: str) -> Optional[str]:
    token = (token or "").strip()
    if not token: return None
    if token.startswith("@"): return token
    u = db.resolve_assignee(token)
    if u and u.get("username"): return "@" + u["username"]
    return None

# --- AI agent (optional) ---
OPENAI_API_KEY = Config.OPENAI_API_KEY
OPENAI_TASK_MODEL = Config.OPENAI_TASK_MODEL

async def ai_parse_task(text: str, now_iso: str, known_usernames: List[str]) -> dict:
    """Kirishdan {assignee,title,deadline,priority} ajratadi. OPENAI bo'lmasa — fallback."""
    nat = parse_deadline_hhmm_dmy(text, datetime.now(TZ))
    if not OPENAI_API_KEY:
        return {
            "assignee": parse_assignee(text.split()[0] if text.split() else "") or "",
            "title": text.strip() or "No title",
            "deadline": nat or "",
            "priority": "Medium",
        }
    try:
        from openai import OpenAI
        import json
        client = OpenAI(api_key=OPENAI_API_KEY)
        sys = (
            "Siz Telegram uchun Task Agent. Kirishdan vazifa strukturasi chiqaring. "
            "Natijani JSON qaytaring: {\"assignee\":\"@username|name|null\",\"title\":\"...\","
            "\"deadline\":\"YYYY-MM-DD HH:MM\",\"priority\":\"Low|Medium|High|Urgent\"}. "
            "Sana-voqea ifodalari (ertaga, indin, bugun, ‘ovolkungi’) va shevalarni ham tushuning. "
            "Agar sana ko‘rsatilmasa, foydalanuvchi bergan HH:MM DD.MM.YYYY formatini topishga harakat qiling; bo‘lmasa bugungi HH:MM qabul qiling."
        )
        prompt = f"now={now_iso}\nknown_users={known_usernames}\ntext={text}"
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=OPENAI_TASK_MODEL,
            messages=[{"role":"system","content":sys},{"role":"user","content":prompt}],
            response_format={"type":"json_object"},
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
        out = {
            "assignee": asg,
            "title": data.get("title") or (text.strip() or "No title"),
            "deadline": data.get("deadline") or (parse_deadline_hhmm_dmy(text, datetime.now(TZ)) or ""),
            "priority": pr if pr in {"Low","Medium","High","Urgent"} else "Medium",
        }
        return out
    except Exception as e:
        logger.warning("AI parse failed: %s", e)
        return {
            "assignee": parse_assignee(text.split()[0] if text.split() else "") or "",
            "title": text.strip() or "No title",
            "deadline": nat or "",
            "priority": "Medium",
        }

# --- /start ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)

    text = T(lang, "welcome_manager") if is_manager(tg) else T(lang, "welcome_employee")
    await update.effective_chat.send_message(
        text=text,
        reply_markup=manager_home_kb(lang) if is_manager(tg) else employee_home_kb(lang),
        parse_mode=ParseMode.HTML
    )

# --- Language ---
async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)
    kb = kb_inline([
        [("🇺🇿 O‘zbek", "lang:uz"), ("🇷🇺 Русский", "lang:ru"), ("🇰🇿 Қазақша", "lang:kk")],
        [(T(lang,"btn_back"), "back:home")]
    ])
    await update.effective_chat.send_message(T(lang, "choose_language"), reply_markup=kb)

async def on_cb_language(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    tg = update.effective_user
    db.set_user_language(tg.id, code)
    text = T(code, "language_set", lang=code)
    await update.effective_chat.send_message(
        text, reply_markup=manager_home_kb(code) if is_manager(tg) else employee_home_kb(code)
    )

# --- Employees ---
def employees_menu_kb(lang: str) -> InlineKeyboardMarkup:
    return kb_inline([
        [(T(lang,"btn_emp_list"), "emp:list")],
        [(T(lang,"btn_emp_add"), "emp:add"), (T(lang,"btn_emp_remove"), "emp:remove")],
        [(T(lang,"btn_back"), "back:home")]
    ])

async def cb_employees_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    if not is_manager(update.effective_user):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    await update.effective_chat.send_message(T(lang,"employees_title"), reply_markup=employees_menu_kb(lang))

async def cb_emp_list(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    if not is_manager(update.effective_user):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    emps = db.list_employees()
    if not emps:
        return await update.effective_chat.send_message(T(lang,"employees_empty"), reply_markup=employees_menu_kb(lang))
    lines = [T(lang,"employees_list_header")]
    for e in emps:
        lines.append(T(lang,"employees_list_line", username=e.get("username") or "-", full_name=e.get("full_name") or "-"))
    await update.effective_chat.send_message("\n".join(lines), reply_markup=employees_menu_kb(lang))

async def ask_emp_add(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    if not is_manager(update.effective_user):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    context.user_data["awaiting_emp_add_username"] = True
    await update.effective_chat.send_message(T(lang,"emp_add_hint"), reply_markup=employees_menu_kb(lang))

async def ask_emp_remove(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    if not is_manager(update.effective_user):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    context.user_data["awaiting_emp_remove"] = True
    await update.effective_chat.send_message(T(lang,"emp_remove_hint"), reply_markup=employees_menu_kb(lang))

# --- text router (flows) ---
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", Config.DEFAULT_LANG)
    text = (update.message.text or "").strip()

    # employees add
    if context.user_data.pop("awaiting_emp_add_username", False):
        if not text.startswith("@"):
            return await update.effective_chat.send_message(T(lang,"enter_username_error"), reply_markup=employees_menu_kb(lang))
        context.user_data["new_emp_username"] = text.lstrip("@")
        # create direct invite
        ok, link = db.create_invite_for(context.user_data.pop("new_emp_username"), full_name=None)
        if ok:
            await update.effective_chat.send_message(T(lang,"invite_created", username=text.lstrip("@"), link=link),
                                                     reply_markup=employees_menu_kb(lang))
        else:
            await update.effective_chat.send_message("Invite yaratib bo‘lmadi.", reply_markup=employees_menu_kb(lang))
        return

    if context.user_data.pop("awaiting_emp_remove", False):
        username = text.lstrip("@")
        ok = db.remove_employee_by_username(username)
        await update.effective_chat.send_message(
            T(lang, "emp_removed" if ok else "emp_remove_fail", username=username),
            reply_markup=employees_menu_kb(lang)
        )
        return

    # task reject reason
    if context.user_data.get("awaiting_task_reject_reason"):
        task_id = context.user_data.pop("awaiting_task_reject_reason")
        reason = text
        try:
            db.set_task_status(task_id, "rejected", by=tg.id, reason=reason)
            await update.effective_chat.send_message("❌ Vazifa rad qilindi.", reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.exception("Task reject failed: %s", ex)
            await update.effective_chat.send_message("Rad etishda xatolik.", reply_markup=employee_home_kb(lang))
        return

    # task done report
    if context.user_data.get("awaiting_task_done_report"):
        task_id = context.user_data.pop("awaiting_task_done_report")
        report = text
        try:
            ok = db.mark_task_done_with_report(task_id, tg.id, report)
            if ok:
                for m in db.list_managers():
                    try:
                        await context.bot.send_message(m["telegram_id"], T(lang,"task_done_notify_manager", username=u.get('username') or '-', task_id=task_id))
                    except Exception:
                        pass
                await update.effective_chat.send_message(T(lang,"done_ok", task_id=task_id), reply_markup=employee_home_kb(lang))
            else:
                await update.effective_chat.send_message(T(lang,"done_fail", task_id=task_id), reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.exception("Task done failed: %s", ex)
            await update.effective_chat.send_message("Xatolik sodir bo‘ldi.", reply_markup=employee_home_kb(lang))
        return

    # task wizard (natural)
    if context.user_data.pop("tw_wait_nl", False):
        now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
        known = [u.get("username") for u in db.list_employees() if u.get("username")]
        parsed = await ai_parse_task(text, now, known)
        if not parsed.get("deadline"):
            parsed["deadline"] = parse_deadline_hhmm_dmy(text, datetime.now(TZ)) or ""
        assigned_to = parsed.get("assignee") or parse_assignee(text.split()[0] if text.split() else "") or ""
        task_id = db.create_task(
            title=parsed.get("title") or "(no title)",
            description=parsed.get("title") or "(no title)",
            created_by=tg.id,
            assigned_to_username=assigned_to.lstrip("@") if assigned_to else "",
            deadline=parsed.get("deadline"),
            priority=parsed.get("priority") or "Medium",
        )
        # notify employee
        emp = db.get_user_by_username(assigned_to.lstrip("@")) if assigned_to else None
        if emp:
            btns = kb_inline([
                [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
                [("☑️ Bajardim", f"task:done:{task_id}")]
            ])
            try:
                await context.bot.send_message(emp["telegram_id"],
                    T(emp.get("language","uz"), "task_assigned", title=parsed.get("title"), deadline=parsed.get("deadline") or "-", priority=parsed.get("priority")),
                    reply_markup=btns)
            except Exception as e:
                logger.warning("Notify employee failed: %s", e)

        await update.effective_chat.send_message(T(lang,"task_created", task_id=task_id),
                                                 reply_markup=manager_home_kb(lang))
        await schedule_task_deadline(context.application, task_id)
        return

# --- /task (slash saqlanadi) ---
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    parts = update.message.text.split(maxsplit=1)
    if len(parts) == 1:
        context.user_data["tw_wait_nl"] = True
        return await update.effective_chat.send_message(T(lang,"assign_task_prompt"))
    payload = parts[1].strip()
    # parse: /task @user "title" 10:00 24.09.2025 [High]
    assigned = ""
    title = ""
    priority = "Medium"
    deadline = ""

    # 1) @username
    if payload.startswith("@"):
        toks = payload.split(maxsplit=1)
        assigned = toks[0]; payload = toks[1] if len(toks) > 1 else ""

    # 2) "title"
    if '"' in payload:
        try:
            i = payload.index('"'); j = payload.index('"', i+1)
            title = payload[i+1:j].strip()
            payload = (payload[:i] + payload[j+1:]).strip()
        except ValueError:
            title = payload; payload = ""
    else:
        title = payload; payload = ""

    # 3) [Priority]
    if "[" in payload and "]" in payload:
        pr = payload[payload.index("[")+1:payload.index("]")].strip().title()
        if pr in {"Low","Medium","High","Urgent"}: priority = pr
        payload = (payload[:payload.index("[")] + payload[payload.index("]")+1:]).strip()

    # 4) time & date (HH:MM DD.MM.YYYY)
    deadline = parse_deadline_hhmm_dmy(payload, datetime.now(TZ)) or ""

    if not assigned:
        maybe = parts[1].split()[0] if parts[1].split() else ""
        assigned = parse_assignee(maybe) or ""

    task_id = db.create_task(
        title=(title or "(no title)"),
        description=(title or "(no title)"),
        created_by=tg.id,
        assigned_to_username=assigned.lstrip("@") if assigned else "",
        deadline=deadline,
        priority=priority,
    )
    emp = db.get_user_by_username(assigned.lstrip("@")) if assigned else None
    if emp:
        btns = kb_inline([
            [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
            [("☑️ Bajardim", f"task:done:{task_id}")]
        ])
        try:
            await context.bot.send_message(emp["telegram_id"],
                T(emp.get("language","uz"), "task_assigned", title=title, deadline=deadline or "-", priority=priority),
                reply_markup=btns)
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(T(lang,"task_created", task_id=task_id), reply_markup=manager_home_kb(lang))
    await schedule_task_deadline(context.application, task_id)

# --- /status ---
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    items = db.get_status_overview()
    lines = [T(lang,"manager_status_header")]
    for row in items:
        emp = row["employee"]; tasks = row["tasks"]
        uname = emp.get("username") or '-'; fname = emp.get("full_name") or '-'
        lines.append(f"👤 @{uname} — {fname}")
        if not tasks: lines.append("  • —")
        else:
            for t in tasks: lines.append("  • " + fmt_task(t))
    await update.effective_chat.send_message("\n".join(lines), parse_mode=ParseMode.MARKDOWN,
                                             reply_markup=manager_home_kb(lang))

# --- Hisobotlar (managerga ko‘rsatma matni) ---
async def build_daily_report_text() -> str:
    rows = db.build_daily_summary()
    if not rows: return "*Bugun faoliyat bo‘yicha ma’lumot yo‘q.*"
    out = ["*Kunlik hisobot:*"]
    for r in rows:
        out.append(f"• @{r['username'] or '-'} — {r['completed']} done / {r['total']} total")
    return "\n".join(out)

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    text = await build_daily_report_text()
    await update.effective_chat.send_message(text, parse_mode=ParseMode.MARKDOWN,
                                             reply_markup=manager_home_kb(lang))

# --- Employee buyruqlari ---
async def cmd_mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)
    tasks = db.list_tasks_for_user(tg.id)
    if not tasks:
        return await update.effective_chat.send_message(T(lang,"no_tasks"), reply_markup=employee_home_kb(lang))
    lines = [T(lang,"your_tasks_header")]
    lines.extend([fmt_task(t) for t in tasks])
    await update.effective_chat.send_message("\n".join(lines), parse_mode=ParseMode.MARKDOWN,
                                             reply_markup=employee_home_kb(lang))

async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)
    args = update.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        return await update.effective_chat.send_message(T(lang,"done_usage"))
    task_id = int(args[1])
    ok = db.set_task_status(task_id, "done", by=tg.id)
    if ok:
        for m in db.list_managers():
            try:
                await context.bot.send_message(m["telegram_id"], T(lang,"task_done_notify_manager", username=u.get('username') or '-', task_id=task_id))
            except Exception:
                pass
        await update.effective_chat.send_message(T(lang,"done_ok", task_id=task_id), reply_markup=employee_home_kb(lang))
    else:
        await update.effective_chat.send_message(T(lang,"done_fail", task_id=task_id), reply_markup=employee_home_kb(lang))

async def cb_employee_report(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    await update.effective_chat.send_message("Bugungi hisobotni yozib yuboring.\n(IDsiz yuborsangiz umumiy kundalik sifatida saqlanadi)")
    context.user_data["awaiting_task_done_report"] = 0

# --- Voice → AI ---
async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language", Config.DEFAULT_LANG)
    if not is_manager(tg):  # faqat menejer ovozdan vazifa bera oladi
        return
    voice = update.message.voice
    if not voice: return
    file = await context.bot.get_file(voice.file_id)
    path = await file.download_to_drive(custom_path=f"/tmp/{voice.file_unique_id}.oga")

    title = "Voice task"; assigned = ""; deadline = ""; priority = "Medium"
    if Config.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            with open(path, "rb") as f:
                tr = client.audio.transcriptions.create(model="whisper-1", file=f)
            txt = tr.text.strip()
            now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
            known = [u.get("username") for u in db.list_employees() if u.get("username")]
            parsed = await ai_parse_task(txt, now, known)
            title = parsed.get("title") or "Voice task"
            deadline = parsed.get("deadline") or (parse_deadline_hhmm_dmy(txt, datetime.now(TZ)) or "")
            priority = parsed.get("priority") or "Medium"
            assigned = parsed.get("assignee") or parse_assignee(txt.split()[0] if txt.split() else "") or ""
        except Exception as e:
            logger.warning("Whisper parse failed: %s", e)

    task_id = db.create_task(
        title=title, description=title, created_by=tg.id,
        assigned_to_username=assigned.lstrip("@") if assigned else "",
        deadline=deadline, priority=priority
    )

    emp = db.get_user_by_username(assigned.lstrip("@")) if assigned else None
    if emp:
        btns = kb_inline([
            [("✅ Qabul qilish", f"task:acc:{task_id}"), ("❌ Rad qilish", f"task:rej:{task_id}")],
            [("☑️ Bajardim", f"task:done:{task_id}")]
        ])
        try:
            await context.bot.send_message(emp["telegram_id"],
                T(emp.get("language","uz"), "task_assigned", title=title, deadline=deadline or "-", priority=priority),
                reply_markup=btns)
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(T(lang,"task_created", task_id=task_id), reply_markup=manager_home_kb(lang))
    await schedule_task_deadline(context.application, task_id)

# --- scheduler helpers ---
async def send_daily_reminder(app: Application, when: str):
    for e in db.list_employees():
        lang = e.get("language", "uz")
        text = T(lang, "reminder_morning" if when=="morning" else "reminder_evening")
        try:
            await app.bot.send_message(e["telegram_id"], text, reply_markup=employee_home_kb(lang))
        except Exception as ex:
            logger.warning("Reminder failed to %s: %s", e.get("username"), ex)

async def send_deadline_ping(app: Application, task_id: int):
    t = db.get_task(task_id)
    if not t: return
    emp = db.get_user(t["assigned_to"])
    if not emp: return
    lang = emp.get("language","uz")
    msg = T(lang,"deadline_ping", task=fmt_task(t))
    try:
        await app.bot.send_message(emp["telegram_id"], msg, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.warning("Deadline ping failed: %s", e)

async def schedule_user_jobs(app: Application):
    if not app.job_queue: return
    for j in app.job_queue.get_jobs_by_name("morning_reminder"): j.schedule_removal()
    for j in app.job_queue.get_jobs_by_name("evening_reminder"): j.schedule_removal()
    app.job_queue.run_daily(lambda ctx: asyncio.create_task(send_daily_reminder(ctx.application, "morning")),
                            time=MORNING_TIME, name="morning_reminder")
    app.job_queue.run_daily(lambda ctx: asyncio.create_task(send_daily_reminder(ctx.application, "evening")),
                            time=EVENING_TIME, name="evening_reminder")
    logger.info("Daily reminders scheduled at %s and %s", MORNING_TIME, EVENING_TIME)

async def schedule_daily_manager_report(app: Application):
    if not app.job_queue: return
    for j in app.job_queue.get_jobs_by_name("daily_manager_report"): j.schedule_removal()
    app.job_queue.run_daily(lambda ctx: asyncio.create_task(daily_manager_report(ctx.application)),
                            time=REPORT_TIME, name="daily_manager_report")
    logger.info("Daily manager report scheduled at %s", REPORT_TIME)

async def schedule_task_deadline(app: Application, task_id: int):
    if not app.job_queue: return
    t = db.get_task(task_id)
    if not t or not t.get("deadline"): return
    try:
        dt = datetime.fromisoformat(t["deadline"])
    except Exception:
        return
    for j in app.job_queue.get_jobs_by_name(f"deadline_{task_id}"): j.schedule_removal()
    app.job_queue.run_once(lambda ctx: asyncio.create_task(send_deadline_ping(ctx.application, task_id)),
                           when=dt, name=f"deadline_{task_id}")

async def daily_manager_report(app: Application):
    managers = db.list_managers()
    text = await build_daily_report_text()
    for m in managers:
        try:
            await app.bot.send_message(m["telegram_id"], text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.warning("Manager report failed: %s", e)

# --- callbacks ---
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", Config.DEFAULT_LANG)
    data = update.callback_query.data

    if data == "u:language":
        return await cmd_language(update, context)
    if data.startswith("lang:"):
        return await on_cb_language(update, context, data.split(":",1)[1])

    # employees
    if data == "m:employees": return await cb_employees_menu(update, context, lang)
    if data == "emp:list":    return await cb_emp_list(update, context, lang)
    if data == "emp:add":     return await ask_emp_add(update, context, lang)
    if data == "emp:remove":  return await ask_emp_remove(update, context, lang)

    # invites (simple list -> approve/reject flow demo)
    if data == "m:invites":
        reqs = db.list_invite_requests()
        rows = []
        for r in reqs:
            rid = r["id"]; title = f"@{r.get('username') or '-'} | {r.get('full_name') or '-'}"
            rows.append([(title, "noop")])
            rows.append([("✅ Qabul", f"inv:approve:{rid}"), ("❌ Rad", f"inv:reject:{rid}")])
        if not rows: rows = [[("— Bo‘sh —", "noop")]]
        rows.append([(T(lang,"btn_back"), "back:home")])
        return await update.effective_chat.send_message(T(lang,"invites_title"), reply_markup=kb_inline(rows))

    if data.startswith("inv:approve:"):
        rid = int(data.split(":")[-1])
        try:
            link = db.approve_invite_request(rid)
            await update.effective_chat.send_message(f"✅ {T(lang,'invite_accept_ok')}\n🔗 {link}",
                                                     reply_markup=manager_home_kb(lang))
        except Exception as ex:
            logger.exception("approve invite: %s", ex)
            await update.effective_chat.send_message("Tasdiqlashda xatolik.", reply_markup=manager_home_kb(lang))
        return

    if data.startswith("inv:reject:"):
        rid = int(data.split(":")[-1])
        context.user_data["awaiting_inv_reject_for"] = rid
        await update.effective_chat.send_message("Rad etish sababini yuboring:")
        return

    # manager quick entries
    if data == "m:assign":
        context.user_data["tw_wait_nl"] = True
        return await update.effective_chat.send_message(T(lang,"assign_task_prompt"))
    if data == "m:status":
        return await cmd_status(update, context)
    if data == "m:reports":
        return await cmd_report(update, context)

    # employee quick
    if data == "e:mytasks":
        return await cmd_mytasks(update, context)
    if data == "e:report":
        return await cb_employee_report(update, context, lang)

    # task lifecycle
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
        role_is_manager = is_manager(tg)
        text = T(lang, "welcome_manager" if role_is_manager else "welcome_employee")
        await update.effective_chat.send_message(text,
            reply_markup=manager_home_kb(lang) if role_is_manager else employee_home_kb(lang))

# --- post init ---
async def on_start(app: Application):
    # Telegram polling 409 oldini olish uchun webhookni tozalash PTB o'zi qiladi; biz schedule qilamiz
    if app.job_queue:
        try:
            app.job_queue.set_timezone(TZ)
        except Exception:
            try:
                app.job_queue.scheduler.configure(timezone=TZ)  # type: ignore
            except Exception as e:
                logger.warning("Timezone set failed: %s", e)
    await schedule_user_jobs(app)
    await schedule_daily_manager_report(app)
    logger.info("Startup scheduling done")

# --- builders ---
async def task_wizard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language", Config.DEFAULT_LANG)
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    context.user_data["tw_wait_nl"] = True
    await update.effective_chat.send_message(T(lang,"assign_task_prompt"))

async def on_callback_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    class _D: pass
    d = _D(); d.data = data
    update.callback_query = d
    await on_callback(update, context)

def build_application() -> Application:
    app = (Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(on_start).build())

    # slash
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("mytasks", cmd_mytasks))
    app.add_handler(CommandHandler("done", cmd_done))

    # reply kb
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_TASK)}$"), task_wizard_start))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_STATUS)}$"), cmd_status))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_REPORTS)}$"), cmd_report))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_EMPLOYEES)}$"),
                                   lambda u,c: cb_employees_menu(u,c,(db.get_user(u.effective_user.id) or {}).get('language',Config.DEFAULT_LANG))))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_INVITES)}$"),
                                   lambda u,c: on_callback_from_text(u,c,"m:invites")))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_LANG)}$"), cmd_language))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_MY_TASKS)}$"), cmd_mytasks))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(LBL_SEND_REP)}$"),
                                   lambda u,c: cb_employee_report(u,c,(db.get_user(u.effective_user.id) or {}).get('language',Config.DEFAULT_LANG))))

    # callbacks, text, voice
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))  # fayl handlerlar yo‘q

    return app

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
# --- main (polling/webhook auto) ---
import os

def main():
    app = build_application()
    logger.info("Starting bot …")

    # WEBHOOK ni yoqish shartlari:
    # - USE_WEBHOOK=1 yoki RENDER_EXTERNAL_URL mavjud
    # - PORT mavjud bo'lishi kerak (Render uni beradi)
    use_webhook = os.getenv("USE_WEBHOOK", "0") == "1" or bool(os.getenv("RENDER_EXTERNAL_URL"))
    port = int(os.getenv("PORT", "8080"))
    base_url = os.getenv("WEBHOOK_BASE", os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")
    secret_token = os.getenv("WEBHOOK_SECRET", "")  # ixtiyoriy: Telegram x-secret-token

    if use_webhook and base_url:
        # Webhook URL -> https://<host>/<token>
        webhook_url = f"{base_url}/{Config.TELEGRAM_BOT_TOKEN}"
        logger.info("Running in WEBHOOK mode at %s", webhook_url)

        # PTB v21: run_webhook
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=Config.TELEGRAM_BOT_TOKEN,
            webhook_url=webhook_url,
            secret_token=secret_token or None,
            drop_pending_updates=True,          # eski navbatni tozalaydi
            allowed_updates=Update.ALL_TYPES,   # barcha update turlari
        )
    else:
        # Polling (faqat bitta instansiya!)
        logger.info("Running in POLLING mode")
        # deleteWebhook pollingdan oldin allaqachon post_init da bor, lekin yana ham o‘rnatamiz:
        try:
            app.bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass

        app.run_polling(
            poll_interval=2.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        raise
