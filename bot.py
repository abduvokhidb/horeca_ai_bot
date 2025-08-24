# bot.py
import asyncio
import logging
import os
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, Contact,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, MessageHandler,
    ContextTypes, filters,
)

from config import Config
from database import Database
from languages import T
from utils import parse_human_or_natural, to_db_str, to_human_str
from ai import transcribe_voice, translate_text, parse_task_from_text, pm_assistant_answer, ai_available

LOG_LEVEL = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("taskbot")

db = Database(Config.DATABASE_PATH)
TZ: ZoneInfo = Config.TIMEZONE

# Times
def to_time(v, default_str: str) -> time:
    if isinstance(v, time): return v
    s = str(v or default_str)
    try:
        hh, mm = s.split(":")[:2]
        return time(int(hh), int(mm))
    except Exception:
        hh, mm = default_str.split(":")[:2]
        return time(int(hh), int(mm))

MORNING_TIME = to_time(os.getenv("MORNING_REMINDER","09:00"), "09:00")
EVENING_TIME = to_time(os.getenv("EVENING_REMINDER","18:00"), "18:00")
REPORT_TIME  = to_time(os.getenv("DAILY_REPORT_TIME","18:00"), "18:00")

# Labels
def L(lang:str,k:str)->str: return T(lang,k)
def main_menu_manager(lang:str)->ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(L(lang,"lbl_assign")), KeyboardButton(L(lang,"lbl_employees"))],
        [KeyboardButton(L(lang,"lbl_dashboard")), KeyboardButton(L(lang,"lbl_reports"))],
        [KeyboardButton(L(lang,"lbl_requests")), KeyboardButton(L(lang,"lbl_settings"))],
        [KeyboardButton(L(lang,"lbl_chat")), KeyboardButton(L(lang,"lbl_ai"))],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)
def main_menu_employee(lang:str)->ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(L(lang,"lbl_my_tasks")), KeyboardButton(L(lang,"lbl_send_report"))],
        [KeyboardButton(L(lang,"lbl_settings")), KeyboardButton(L(lang,"lbl_chat"))],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def is_manager(user)->bool:
    if user is None: return False
    tid = user.id
    uname = (user.username or "").lower()
    ids = {int(x) for x in (Config.MANAGER_IDS or "").split(",") if x.strip().isdigit()}
    unames = {u.strip().lstrip("@").lower() for u in (Config.MANAGER_USERNAMES or "").split(",") if u.strip()}
    return tid in ids or (uname and uname in unames)

# Helpers
def kb_inline(rows): return InlineKeyboardMarkup([[InlineKeyboardButton(txt, callback_data=data) for (txt,data) in row] for row in rows])

def fmt_task_line(t:dict)->str:
    # Display deadline HH:MM DD.MM.YYYY
    dd = "-"
    if t.get("deadline"):
        try: dd = to_human_str(datetime.fromisoformat(t["deadline"]))
        except Exception: dd = t["deadline"]
    pr = t.get("priority","Medium")
    return f"#{t['id']} • {t.get('title','(no title)')} — *{t.get('status','new').upper()}* • ⏰ {dd} • 🔥 {pr}"

async def ensure_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
    tg = update.effective_user
    if not tg: return {}
    user = db.upsert_user(tg.id, tg.username, f"{tg.first_name or ''} {tg.last_name or ''}".strip())
    # Auto-role detect for managers
    role = user.get("role")
    mflag = is_manager(tg)
    newrole = "MANAGER" if mflag else (role or None)
    if (mflag and role!="MANAGER"):
        db.set_user_role(tg.id,"MANAGER")
        user = db.get_user(tg.id) or user
    return user

# Onboarding /start (with optional invite token)
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    user = await ensure_user(update, context)
    lang = user.get("language","uz")
    args = (update.message.text or "").split(maxsplit=1)
    if len(args)>0 and len(args)==2 and args[1].strip():
        token = args[1].strip()
        try:
            ok = db.consume_invite_token(token, tg.id, tg.username, user.get("full_name"))
            if ok:
                db.set_user_role(tg.id,"EMPLOYEE")
                user = db.get_user(tg.id) or user
                lang = user.get("language","uz")
                await update.effective_chat.send_message("✅ Invite qabul qilindi.")
            # else: invalid token — e’tiborsiz
        except Exception:
            pass

    role = user.get("role") or ("MANAGER" if is_manager(tg) else "EMPLOYEE")
    if user.get("role") != role: db.set_user_role(tg.id, role)

    # Language pick if unknown (use Telegram locale as default suggestion)
    if not user.get("language"):
        await show_language_picker(update, context, lang)
        await update.effective_chat.send_message(L(lang,"hint_pick_language"))
        return

    # Registration for employees without phone/name
    if role=="EMPLOYEE" and not (user.get("phone") and user.get("full_name")):
        await ask_registration(update, context, lang)
        return

    # Home
    txt = L(lang, "welcome_manager") if role=="MANAGER" else L(lang,"welcome_employee")
    await update.effective_chat.send_message(
        f"{txt}\n{L(lang,'hint_task_format')}",
        reply_markup=main_menu_manager(lang) if role=="MANAGER" else main_menu_employee(lang),
        parse_mode=ParseMode.HTML
    )

async def show_language_picker(update: Update, context: ContextTypes.DEFAULT_TYPE, lang:str):
    kb = kb_inline([
        [("🇺🇿 O‘zbek", "lang:uz"), ("🇷🇺 Русский", "lang:ru"), ("🇰🇿 Қазақша", "lang:kk")]
    ])
    await update.effective_chat.send_message(L(lang,"choose_language"), reply_markup=kb)

async def ask_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, lang:str):
    # Simple wizard: ask full name, then phone (contact button)
    context.user_data["reg_wait_name"] = True
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(L(lang,"lbl_register"))]], resize_keyboard=True, one_time_keyboard=True
    )
    await update.effective_chat.send_message(L(lang,"hint_welcome_new"), reply_markup=kb)
    await update.effective_chat.send_message(L(lang,"ask_new_name"))

# Language callbacks
async def on_cb_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code:str):
    tg = update.effective_user
    db.set_user_language(tg.id, lang_code)
    user = db.get_user(tg.id) or {}
    role = user.get("role") or ("MANAGER" if is_manager(tg) else "EMPLOYEE")
    await update.effective_chat.send_message(L(lang_code,"language_set", lang=lang_code))
    await update.effective_chat.send_message(
        L(lang_code,"hint_task_format"),
        reply_markup=main_menu_manager(lang_code) if role=="MANAGER" else main_menu_employee(lang_code)
    )

# Settings
async def open_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    kb = ReplyKeyboardMarkup([
        [KeyboardButton(L(lang,"lbl_change_lang")), KeyboardButton(L(lang,"lbl_change_name"))],
        [KeyboardButton(L(lang,"lbl_change_phone"))],
        [KeyboardButton(L(lang,"lbl_back"))],
    ], resize_keyboard=True)
    await update.effective_chat.send_message(L(lang,"settings_title"), reply_markup=kb)
    await update.effective_chat.send_message(L(lang,"hint_settings"))

# ---- Core routers ----

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    text = (update.message.text or "").strip()

    # Registration flow
    if context.user_data.pop("reg_wait_name", False):
        db.update_profile(tg.id, full_name=text)
        # ask phone
        context.user_data["reg_wait_phone"] = True
        kb = ReplyKeyboardMarkup([[KeyboardButton(L(lang,"lbl_change_phone"), request_contact=True)]], resize_keyboard=True)
        await update.effective_chat.send_message(L(lang,"ask_new_phone"), reply_markup=kb)
        return
    if context.user_data.pop("reg_wait_phone", False):
        # could be plain text number
        phone = text
        db.update_profile(tg.id, phone=phone)
        await update.effective_chat.send_message(L(lang,"profile_saved"),
            reply_markup=main_menu_manager(lang) if (u.get("role")=="MANAGER") else main_menu_employee(lang))
        return

    # Settings changes
    if text == L(lang,"lbl_change_lang"):
        return await show_language_picker(update, context, lang)
    if text == L(lang,"lbl_change_name"):
        context.user_data["await_new_name"] = True
        await update.effective_chat.send_message(L(lang,"ask_new_name"))
        return
    if context.user_data.pop("await_new_name", False):
        db.update_profile(tg.id, full_name=text)
        await update.effective_chat.send_message(L(lang,"profile_saved"),
            reply_markup=main_menu_manager(lang) if (u.get("role")=="MANAGER") else main_menu_employee(lang))
        return
    if text == L(lang,"lbl_change_phone"):
        context.user_data["await_new_phone"] = True
        kb = ReplyKeyboardMarkup([[KeyboardButton(L(lang,"lbl_change_phone"), request_contact=True)]], resize_keyboard=True)
        await update.effective_chat.send_message(L(lang,"ask_new_phone"), reply_markup=kb)
        return
    if context.user_data.pop("await_new_phone", False):
        db.update_profile(tg.id, phone=text)
        await update.effective_chat.send_message(L(lang,"profile_saved"),
            reply_markup=main_menu_manager(lang) if (u.get("role")=="MANAGER") else main_menu_employee(lang))
        return

    # Reply keyboard main navigation
    if text == L(lang,"lbl_settings"):
        return await open_settings(update, context)
    if text == L(lang,"lbl_employees"):
        return await employees_menu(update, context)
    if text == L(lang,"lbl_requests"):
        return await open_invites(update, context)
    if text == L(lang,"lbl_dashboard"):
        return await cmd_status(update, context)
    if text == L(lang,"lbl_reports"):
        return await cmd_report(update, context)
    if text == L(lang,"lbl_assign"):
        # Task wizard natural language
        if not is_manager(tg):
            return await update.effective_chat.send_message(L(lang,"only_manager"))
        context.user_data["tw_wait_nl"] = True
        await update.effective_chat.send_message("Tabiiy tilda vazifa yozing.\n" + L(lang,"hint_task_format"))
        return
    if text == L(lang,"lbl_my_tasks"):
        return await cmd_mytasks(update, context)
    if text == L(lang,"lbl_send_report"):
        context.user_data["awaiting_task_done_report"] = 0
        await update.effective_chat.send_message(L(lang,"report_prompt"))
        return
    if text == L(lang,"lbl_chat"):
        return await open_chat(update, context)
    if text == L(lang,"lbl_ai"):
        return await open_ai_assistant(update, context)

    # Task Wizard NL
    if context.user_data.pop("tw_wait_nl", False):
        await create_task_from_nl(update, context, text, lang)
        return

    # Chat mode (employee or manager replying)
    if context.user_data.get("chat_reply_to"):
        to_id = context.user_data.get("chat_reply_to")
        try:
            await context.bot.send_message(to_id, f"📩 {text}")
            await update.effective_chat.send_message("✅ Yuborildi.")
        except Exception:
            await update.effective_chat.send_message("❌ Yuborilmadi.")
        context.user_data.pop("chat_reply_to", None)
        return

async def contact_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    contact: Contact = update.message.contact
    if contact and contact.phone_number:
        db.update_profile(tg.id, phone=contact.phone_number)
        await update.effective_chat.send_message(L(lang,"profile_saved"),
            reply_markup=main_menu_manager(lang) if (u.get("role")=="MANAGER") else main_menu_employee(lang))

# Employees
async def employees_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    if not is_manager(tg):
        return await update.effective_chat.send_message(L(lang,"only_manager"))
    rows = db.list_employees()
    if not rows:
        await update.effective_chat.send_message(L(lang,"employees_list_header") + "\n—")
    else:
        lines = [L(lang,"employees_list_header")]
        for e in rows:
            lines.append(L(lang,"employees_list_line", username=(e.get('username') or '-'), full_name=e.get('full_name') or '-'))
        await update.effective_chat.send_message("\n".join(lines))
    await update.effective_chat.send_message(L(lang,"emp_add_hint"))
    await update.effective_chat.send_message(L(lang,"emp_remove_hint"))

# Invites / Requests (inline manage)
async def open_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    if not is_manager(tg):
        return await update.effective_chat.send_message(L(lang,"only_manager"))
    reqs = db.list_invite_requests()
    if not reqs:
        return await update.effective_chat.send_message(L(lang,"invites_empty"))
    rows = []
    for r in reqs:
        rid = r["id"]
        ttl = f"@{r.get('username') or '-'} — {r.get('full_name') or '-'}"
        rows.append([(ttl,"noop")])
        rows.append([(L(lang,"btn_invite_accept"), f"inv:ok:{rid}"), (L(lang,"btn_invite_reject"), f"inv:rej:{rid}")])
    await update.effective_chat.send_message(L(lang,"invites_title"), reply_markup=kb_inline(rows))

# AI assistant
async def open_ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    await update.effective_chat.send_message("PM savolingizni yozing. (AI)")

    context.user_data["ai_wait_prompt"] = True

async def ai_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    if context.user_data.pop("ai_wait_prompt", False):
        # Some context hint (light)
        stats = db.build_daily_summary()
        hint = f"Employees: {len(stats)}. Today summary exists."
        ans = await pm_assistant_answer(update.message.text, context_hint=hint)
        await update.effective_chat.send_message(ans)
        return

# Chat mediator
async def open_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    if is_manager(tg):
        await update.effective_chat.send_message("Kimga javob berish uchun reply tugmasidan foydalaning (xabar kelganda).")
    else:
        mans = db.list_managers()
        if not mans:
            return await update.effective_chat.send_message("Hozircha menejer yo‘q.")
        # default first manager
        context.user_data["chat_reply_to"] = mans[0]["telegram_id"]
        await update.effective_chat.send_message(L(lang,"hint_chat"))
        await update.effective_chat.send_message("Xabaringizni yozing:")

# Voice → task
async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language","uz")
    voice = update.message.voice
    if not voice: return
    # Only managers can create tasks by voice
    if not is_manager(tg): return
    f = await context.bot.get_file(voice.file_id)
    path = await f.download_to_drive(custom_path=f"/tmp/{voice.file_unique_id}.oga")
    txt = await transcribe_voice(str(path)) if ai_available() else ""
    if not txt:
        await update.effective_chat.send_message("Ovoz tanib bo‘lmadi.")
        return
    now_iso = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    known = [uu.get("username") for uu in db.list_all_users() if uu.get("username")]
    parsed = await parse_task_from_text(txt, now_iso, known)
    # fallback natural parse
    if not parsed.get("deadline"):
        nd = parse_human_or_natural(txt, datetime.now(TZ), TZ)
        parsed["deadline"] = to_db_str(nd) if nd else ""
    # assignee fallback
    if not parsed.get("assignee"):
        tok = txt.split()[0] if txt.split() else ""
        a = db.resolve_assignee(tok)
        parsed["assignee"] = ("@" + a["username"]) if (a and a.get("username")) else ""

    # translate to employee lang
    assigned_to = parsed.get("assignee","").lstrip("@")
    emp = db.get_user_by_username(assigned_to) if assigned_to else None
    title = parsed.get("title") or "Voice task"
    deadline = parsed.get("deadline") or ""
    pr = (parsed.get("priority") or "Medium").title()

    task_id = db.create_task(title, title, tg.id, assigned_to, deadline, pr)

    if emp:
        msg = T(emp.get("language","uz"), "task_assigned", title=title,
                deadline=(to_human_str(datetime.fromisoformat(deadline)) if deadline else "-"), priority=pr)
        if ai_available():
            # translate title+text to employee language (light)
            msg = await translate_text(msg, {"uz":"Uzbek","ru":"Russian","kk":"Kazakh"}[emp.get("language","uz")])
        btns = kb_inline([
            [("✅ Qabul", f"task:acc:{task_id}"), ("❌ Rad", f"task:rej:{task_id}")],
            [("☑️ Bajardim", f"task:done:{task_id}")]
        ])
        try:
            await context.bot.send_message(emp["telegram_id"], msg, reply_markup=btns)
        except Exception as e:
            logger.warning("Notify employee failed: %s", e)

    await update.effective_chat.send_message(T(lang,"task_created", task_id=task_id))
    await schedule_task_deadline(context.application, task_id)

# Create task from natural text (manager)
async def create_task_from_nl(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str):
    tg = update.effective_user
    now_iso = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    known = [uu.get("username") for uu in db.list_all_users() if uu.get("username")]
    parsed = await parse_task_from_text(text, now_iso, known)
    if not parsed.get("deadline"):
        nd = parse_human_or_natural(text, datetime.now(TZ), TZ)
        parsed["deadline"] = to_db_str(nd) if nd else ""
    if not parsed.get("assignee"):
        tok = text.split()[0] if text.split() else ""
        a = db.resolve_assignee(tok)
        parsed["assignee"] = ("@" + a["username"]) if (a and a.get("username")) else ""

    assigned_to = parsed.get("assignee","").lstrip("@")
    pr = (parsed.get("priority") or "Medium").title()
    title = parsed.get("title") or "(no title)"
    deadline = parsed.get("deadline") or ""

    task_id = db.create_task(title, title, tg.id, assigned_to, deadline, pr)
    emp = db.get_user_by_username(assigned_to) if assigned_to else None
    if emp:
        msg = T(emp.get("language","uz"), "task_assigned", title=title,
                deadline=(to_human_str(datetime.fromisoformat(deadline)) if deadline else "-"), priority=pr)
        btns = kb_inline([
            [("✅ Qabul", f"task:acc:{task_id}"), ("❌ Rad", f"task:rej:{task_id}")],
            [("☑️ Bajardim", f"task:done:{task_id}")]
        ])
        await context.bot.send_message(emp["telegram_id"], msg, reply_markup=btns)
    await update.effective_chat.send_message(T(lang,"task_created", task_id=task_id))
    await schedule_task_deadline(context.application, task_id)

# Slash commands preserved
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language","uz")
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    args = update.message.text.split(maxsplit=1)
    if len(args)==1:
        context.user_data["tw_wait_nl"] = True
        return await update.effective_chat.send_message(T(lang,"hint_task_format"))
    payload = args[1].strip()
    # very simple parser: "HH:MM DD.MM.YYYY" etc handled by utils in NL mode
    await create_task_from_nl(update, context, payload, lang)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language","uz")
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    items = db.get_status_overview()
    lines = [T(lang,"manager_status_header")]
    for row in items:
        emp = row["employee"]; tasks = row["tasks"]
        uname = emp.get("username") or "-"
        fname = emp.get("full_name") or "-"
        lines.append(f"👤 @{uname} — {fname}")
        if not tasks:
            lines.append("  • —")
        else:
            for t in tasks:
                lines.append("  • " + fmt_task_line(t))
    await update.effective_chat.send_message("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

async def build_daily_report_text()->str:
    rows = db.build_daily_summary()
    if not rows: return "*Bugun faoliyat bo‘yicha ma’lumot yo‘q.*"
    lines = ["*Kunlik hisobot:*"]
    for r in rows:
        lines.append(f"• @{r['username'] or '-'} — {r['completed']} done / {r['total']} total")
    return "\n".join(lines)

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language","uz")
    if not is_manager(tg):
        return await update.effective_chat.send_message(T(lang,"only_manager"))
    text = await build_daily_report_text()
    await update.effective_chat.send_message(text, parse_mode=ParseMode.MARKDOWN)

async def cmd_mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language","uz")
    tasks = db.list_tasks_for_user(tg.id)
    if not tasks:
        return await update.effective_chat.send_message(T(lang,"no_tasks"), reply_markup=main_menu_employee(lang))
    lines = [T(lang,"your_tasks_header")]
    lines.extend([fmt_task_line(t) for t in tasks])
    await update.effective_chat.send_message("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_employee(lang))

async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = await ensure_user(update, context)
    lang = u.get("language","uz")
    args = update.message.text.split()
    if len(args)<2 or not args[1].isdigit():
        return await update.effective_chat.send_message(T(lang,"done_usage"))
    task_id = int(args[1])
    ok = db.set_task_status(task_id, "done", by=tg.id)
    if ok:
        await update.effective_chat.send_message(T(lang,"done_ok", task_id=task_id))
    else:
        await update.effective_chat.send_message(T(lang,"done_fail", task_id=task_id))

# Attachments
async def cmd_attach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args)<2 or not args[1].isdigit():
        return await update.effective_chat.send_message("Foydalanish: /attach <task_id>")
    context.user_data["await_attach_task"] = int(args[1])
    await update.effective_chat.send_message(T((db.get_user(update.effective_user.id) or {}).get("language","uz"),"hint_attach"))

async def file_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    task_id = context.user_data.get("await_attach_task")
    if not task_id: return
    msg = update.message
    file_id = None; ftype=None; fname=None; caption = msg.caption or ""
    if msg.document:
        file_id = msg.document.file_id; ftype="document"; fname=msg.document.file_name
    elif msg.photo:
        file_id = msg.photo[-1].file_id; ftype="photo"
    elif msg.audio:
        file_id = msg.audio.file_id; ftype="audio"; fname=msg.audio.file_name
    elif msg.video:
        file_id = msg.video.file_id; ftype="video"; fname=None
    elif msg.voice:
        file_id = msg.voice.file_id; ftype="voice"
    if file_id:
        db.add_task_file(task_id, file_id, ftype, fname, caption, tg.id)
        await update.effective_chat.send_message("✅ Biriktirildi.")
        context.user_data.pop("await_attach_task", None)

# Inline callbacks
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    data = update.callback_query.data

    if data.startswith("lang:"):
        return await on_cb_language(update, context, data.split(":")[1])

    if data.startswith("inv:ok:"):
        rid = int(data.split(":")[2])
        try:
            link = db.approve_invite_request(rid)
            await update.effective_chat.send_message(L(lang,"invite_accept_ok") + f"\n{link}")
        except Exception:
            await update.effective_chat.send_message("Xatolik.")
        return
    if data.startswith("inv:rej:"):
        rid = int(data.split(":")[2])
        db.reject_invite_request(rid, "rejected")
        await update.effective_chat.send_message(L(lang,"invite_reject_ok"))
        return

    if data.startswith("task:acc:"):
        task_id = int(data.split(":")[2])
        try:
            db.set_task_status(task_id, "accepted", by=tg.id)
            await update.effective_chat.send_message("✅ Qabul qilindi.")
        except Exception:
            await update.effective_chat.send_message("Xatolik.")
        return
    if data.startswith("task:rej:"):
        task_id = int(data.split(":")[2])
        context.user_data["awaiting_task_reject_reason"] = task_id
        await update.effective_chat.send_message("Rad etish sababini yuboring:")
        return
    if data.startswith("task:done:"):
        task_id = int(data.split(":")[2])
        context.user_data["awaiting_task_done_report"] = task_id
        await update.effective_chat.send_message("Qisqacha hisobot yuboring:")
        return

# Reasons & Reports
async def after_text_reason_or_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    u = db.get_user(tg.id) or {}
    lang = u.get("language","uz")
    text = (update.message.text or "").strip()

    if context.user_data.get("awaiting_task_reject_reason"):
        task_id = context.user_data.pop("awaiting_task_reject_reason")
        db.set_task_status(task_id, "rejected", by=tg.id, reason=text)
        await update.effective_chat.send_message("❌ Rad etildi.")
        return

    if context.user_data.get("awaiting_task_done_report") is not None:
        task_id = context.user_data.pop("awaiting_task_done_report")
        db.mark_task_done_with_report(task_id, tg.id, text)
        await update.effective_chat.send_message(T(lang,"done_ok", task_id=task_id if task_id else 0))
        return

# Reminders & Schedules
async def send_daily_reminder(app: Application, when: str):
    employees = db.list_employees()
    for e in employees:
        lang = e.get("language","uz")
        txt = T(lang,"reminder_morning") if when=="morning" else T(lang,"reminder_evening")
        try:
            await app.bot.send_message(e["telegram_id"], txt, reply_markup=main_menu_employee(lang))
        except Exception as ex:
            logger.warning("Reminder failed: %s", ex)

async def send_deadline_ping(app: Application, task_id: int):
    t = db.get_task(task_id)
    if not t: return
    emp = db.get_user(t["assigned_to"])
    if not emp: return
    lang = emp.get("language","uz")
    dd = "-"
    if t.get("deadline"):
        try: dd = to_human_str(datetime.fromisoformat(t["deadline"]))
        except Exception: dd = t["deadline"]
    msg = T(lang,"deadline_soon", task_id=task_id, title=t.get("title","-"), deadline=dd)
    try:
        await app.bot.send_message(emp["telegram_id"], msg)
    except Exception as e:
        logger.warning("Deadline ping failed: %s", e)

async def schedule_user_jobs(app: Application):
    if app.job_queue is None: return
    for name in ("morning_reminder","evening_reminder"):
        for j in app.job_queue.get_jobs_by_name(name): j.schedule_removal()
    app.job_queue.run_daily(lambda ctx: asyncio.create_task(send_daily_reminder(ctx.application,"morning")),
                            time=MORNING_TIME, days=(0,1,2,3,4,5,6), name="morning_reminder")
    app.job_queue.run_daily(lambda ctx: asyncio.create_task(send_daily_reminder(ctx.application,"evening")),
                            time=EVENING_TIME, days=(0,1,2,3,4,5,6), name="evening_reminder")

async def schedule_daily_manager_report(app: Application):
    if app.job_queue is None: return
    for j in app.job_queue.get_jobs_by_name("daily_manager_report"): j.schedule_removal()
    app.job_queue.run_daily(lambda ctx: asyncio.create_task(daily_manager_report(ctx.application)),
                            time=REPORT_TIME, days=(0,1,2,3,4,5,6), name="daily_manager_report")

async def schedule_task_deadline(app: Application, task_id: int):
    if app.job_queue is None: return
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
    mans = db.list_managers()
    text = await build_daily_report_text()
    for m in mans:
        try: await app.bot.send_message(m["telegram_id"], text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e: logger.warning("Manager report failed: %s", e)

# Post-init
async def on_start(app: Application):
    if app.job_queue:
        try:
            app.job_queue.set_timezone(TZ)
        except Exception:
            try: app.job_queue.scheduler.configure(timezone=TZ)  # type: ignore
            except Exception as e: logger.warning("Timezone set failed: %s", e)
    await schedule_user_jobs(app)
    await schedule_daily_manager_report(app)
    logger.info("Startup scheduling done")

def build_application()->Application:
    app = (Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(on_start).build())

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("mytasks", cmd_mytasks))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("attach", cmd_attach))

    # Reply keyboard routes (match by labels in current lang handled in text_router)
    app.add_handler(MessageHandler(filters.CONTACT, contact_router))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))

    # Files for attachments
    file_filter = filters.Document | filters.PHOTO | filters.AUDIO | filters.VIDEO | filters.VOICE
    app.add_handler(MessageHandler(file_filter, file_router))

    # AI prompt route
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_router))
    # Core text router (registration, settings, menus, wizard)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    # Callback queries
    app.add_handler(CallbackQueryHandler(on_callback))

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
