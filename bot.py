
import asyncio
import logging
import os
from datetime import datetime, timedelta, time
from typing import Optional, Tuple, Dict, Any, List
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, constants
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
)

from config import Config, PRIORITY_LEVELS, DEFAULT_PRIORITY, get_manager_usernames, get_manager_ids
from languages import t, DEFAULT_LANG
from database import Database

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
)
logger = logging.getLogger("taskbot")

db = Database(Config.DATABASE_PATH)
TZ = Config.TIMEZONE

# ---------- Utilities ----------
def private_chat_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat and update.effective_chat.type != "private":
            lang = DEFAULT_LANG
            user = await db.get_user(update.effective_user.id) if update.effective_user else None
            if user:
                lang = user["language"]
            await update.effective_chat.send_message(t(lang, "only_private"))
            return
        return await func(update, context)
    return wrapper

def is_manager(user_row: Optional[Dict[str, Any]]) -> bool:
    if not user_row:
        return False
    if user_row["role"] == "MANAGER":
        return True
    usernames = get_manager_usernames()
    ids = get_manager_ids()
    username = (user_row["username"] or "").lower()
    if username and username in usernames:
        return True
    if user_row["telegram_id"] in ids:
        return True
    return False

def manager_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_row = await db.get_user(update.effective_user.id)
        lang = user_row["language"] if user_row else DEFAULT_LANG
        if not is_manager(user_row):
            await update.effective_message.reply_text(
                t(lang, "not_authorized"),
                reply_markup=main_keyboard(user_row),
            )
            return
        return await func(update, context, user_row)
    return wrapper

def main_keyboard(user_row: Optional[Dict[str, Any]]):
    lang = user_row["language"] if user_row else DEFAULT_LANG
    if user_row and is_manager(user_row):
        kb = [
            [
                InlineKeyboardButton(t(lang, "btn_assign_task"), callback_data="mgr:assign"),
                InlineKeyboardButton(t(lang, "btn_status"), callback_data="mgr:status"),
            ],
            [
                InlineKeyboardButton(t(lang, "btn_reports"), callback_data="mgr:reports"),
                InlineKeyboardButton(t(lang, "btn_employees"), callback_data="mgr:employees"),
            ],
            [InlineKeyboardButton(t(lang, "btn_language"), callback_data="common:language"),
             InlineKeyboardButton(t(lang, "btn_help"), callback_data="common:help")]
        ]
    else:
        kb = [
            [
                InlineKeyboardButton(t(lang, "btn_my_tasks"), callback_data="emp:mytasks"),
                InlineKeyboardButton(t(lang, "btn_send_report"), callback_data="emp:report"),
            ],
            [
                InlineKeyboardButton(t(lang, "btn_language"), callback_data="common:language"),
                InlineKeyboardButton(t(lang, "btn_help"), callback_data="common:help"),
            ]
        ]
    return InlineKeyboardMarkup(kb)

def language_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang:kk"),
            ],
            [InlineKeyboardButton("⬅️", callback_data="common:back")]
        ]
    )

def build_invite_link(context: ContextTypes.DEFAULT_TYPE, code: str) -> str:
    bot_username = context.application.bot_data.get('bot_username') or 'your_bot'
    return f'https://t.me/{bot_username}?start=inv_{code}'

def parse_task_command(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    import shlex
    from dateutil import parser as dtparser
    username = None
    title = None
    deadline_iso = None
    priority = DEFAULT_PRIORITY
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()

    for p in parts:
        if p.startswith("@"):
            username = p[1:]
            break

    if '"' in text:
        try:
            first = text.index('"')
            last = text.index('"', first + 1)
            title = text[first + 1:last].strip()
        except ValueError:
            pass

    import re
    m = re.search(r"\[(Low|Medium|High|Urgent)\]", text, re.IGNORECASE)
    if m:
        priority = m.group(1).capitalize()

    cleaned = text.replace("/task", "")
    if username:
        cleaned = cleaned.replace(f"@{username}", "")
    if title:
        cleaned = cleaned.replace(f"\"{title}\"", "")
    if m:
        cleaned = cleaned.replace(m.group(0), "")
    cleaned = cleaned.strip()
    try:
        dt = dtparser.parse(cleaned, dayfirst=True, fuzzy=True)
        deadline_iso = dt.isoformat()
    except Exception:
        deadline_iso = None

    return username, title, deadline_iso, priority

async def transcribe_voice(file_path: str) -> Optional[str]:
    if not (Config.ENABLE_WHISPER and Config.OPENAI_API_KEY and OpenAI):
        return None
    try:
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        with open(file_path, "rb") as f:
            resp = client.audio.transcriptions.create(model="whisper-1", file=f)
        return getattr(resp, "text", None)
    except Exception as e:
        logger.exception("Whisper transcription failed: %s", e)
        return None

async def ai_parse_task(natural_text: str) -> Dict[str, Any]:
    prompt = f"""Extract task info from the manager's instruction. Return JSON with keys:
username (w/o @, may be null), title (short), deadline_iso (ISO 8601 or null), priority (Low|Medium|High|Urgent).
Instruction: {natural_text}"""
    try:
        if Config.ENABLE_PARSER and Anthropic and Config.ANTHROPIC_API_KEY:
            client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            msg = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
                system="You are a precise JSON extraction engine.",
            )
            content = msg.content[0].text if msg and msg.content else "{}"
            import json
            data = json.loads(content)
            return {
                "username": (data.get("username") or None),
                "title": data.get("title") or None,
                "deadline_iso": data.get("deadline_iso") or None,
                "priority": (data.get("priority") or DEFAULT_PRIORITY).capitalize(),
            }
        elif Config.ENABLE_PARSER and OpenAI and Config.OPENAI_API_KEY:
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise JSON extraction engine. Respond with only JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            import json
            content = resp.choices[0].message.content
            data = json.loads(content)
            return {
                "username": (data.get("username") or None),
                "title": data.get("title") or None,
                "deadline_iso": data.get("deadline_iso") or None,
                "priority": (data.get("priority") or DEFAULT_PRIORITY).capitalize(),
            }
    except Exception as e:
        logger.exception("AI parse failed: %s", e)

    u, title, deadline, pr = parse_task_command(natural_text)
    return {"username": u, "title": title, "deadline_iso": deadline, "priority": pr}

def employees_keyboard(employees: List[Dict[str, Any]], prefix: str="empchoose:") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for e in employees:
        uname = e["username"] or str(e["telegram_id"])
        row.append(InlineKeyboardButton(f"@{uname}", callback_data=f"{prefix}{e['telegram_id']}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️", callback_data="common:back")])
    return InlineKeyboardMarkup(buttons)

async def schedule_user_jobs(app: Application, user_id: int):
    for name, at in (("morning", Config.MORNING_REMINDER), ("evening", Config.EVENING_REMINDER)):
        jobname = f"{name}:{user_id}"
        for j in app.job_queue.get_jobs_by_name(jobname):
            j.schedule_removal()
        app.job_queue.run_daily(callback=reminder_job, time=at, days=(0,1,2,3,4,5,6), name=jobname, data={"user_id": user_id}, tzinfo=TZ)

async def schedule_task_deadline(app: Application, task_id: int, chat_id: int, title: str, deadline_iso: Optional[str]):
    if not deadline_iso:
        return
    try:
        dl = datetime.fromisoformat(deadline_iso)
        for offset, tag in ((timedelta(hours=-2), "soon"), (timedelta(0), "due")):
            when = dl + offset
            if when > datetime.now(when.tzinfo or TZ):
                name = f"deadline:{task_id}:{tag}"
                for j in app.job_queue.get_jobs_by_name(name):
                    j.schedule_removal()
                app.job_queue.run_once(callback=deadline_job, when=when, name=name, data={
                    "task_id": task_id, "chat_id": chat_id, "title": title, "deadline": deadline_iso
                }, tzinfo=TZ)
    except Exception as e:
        logger.warning("Failed to schedule deadline reminders: %s", e)

# ---------- Handlers ----------
@private_chat_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    # Deep-link invites: /start inv_xxxxx
    if context.args and len(context.args) >= 1 and context.args[0].startswith('inv_'):
        code = context.args[0].split('inv_',1)[1]
        inv = await db.get_invite(code)
        await db.upsert_user(u.id, u.username, u.full_name)
        user_row = await db.get_user(u.id)
        if inv and not inv.get('used_by'):
            await db.set_user_role(u.id, 'EMPLOYEE')
            await db.mark_invite_used(code, used_by=u.id, used_at=datetime.utcnow().isoformat())
            await schedule_user_jobs(context.application, u.id)
            lang = user_row['language'] if user_row else DEFAULT_LANG
            msg = t(lang, 'invite_used_success')
            if inv.get('username') and (u.username or '').lower() != inv['username'].lower():
                msg += '\n' + t(lang, 'invite_username_mismatch')
            await update.message.reply_text(msg, reply_markup=main_keyboard(await db.get_user(u.id)))
            return

    await db.upsert_user(u.id, u.username, u.full_name)
    user_row = await db.get_user(u.id)
    if u.username and u.username.lower() in get_manager_usernames():
        await db.set_user_role(u.id, "MANAGER"); user_row["role"] = "MANAGER"
    if u.id in get_manager_ids():
        await db.set_user_role(u.id, "MANAGER"); user_row["role"] = "MANAGER"
    await schedule_user_jobs(context.application, u.id)

    lang = user_row["language"]
    text = t(lang, "welcome_manager") if is_manager(user_row) else t(lang, "welcome_employee")
    await update.message.reply_text(text, reply_markup=main_keyboard(user_row))

@manager_only
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE, mgr_row: Dict[str, Any]):
    lang = mgr_row["language"]
    if not context.args:
        await update.message.reply_text(t(lang, "assign_task_prompt"), reply_markup=main_keyboard(mgr_row))
        return
    parsed_text = update.message.text or ""
    username, title, deadline_iso, priority = parse_task_command(parsed_text)
    if not title:
        await update.message.reply_text(t(lang, "assign_task_prompt"), reply_markup=main_keyboard(mgr_row))
        return
    assignee_row = None
    if username:
        assignee_row = await db.get_user_by_username(username)
    if not assignee_row:
        employees = await db.get_all_employees()
        await update.message.reply_text(t(lang, "select_employee"), reply_markup=employees_keyboard(employees, prefix=f"assign:{title}|{deadline_iso or ''}|{priority}:"))
        return
    task_id = await db.add_task(title=title, description=title, created_by=mgr_row["telegram_id"], assigned_to=assignee_row["telegram_id"], deadline=deadline_iso, priority=priority)
    try:
        await context.bot.send_message(assignee_row["telegram_id"],
            t(assignee_row["language"], "task_assigned_to", title=title, deadline=deadline_iso or "-", priority=priority),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t(assignee_row["language"], "btn_mark_done"), callback_data=f"done:{task_id}"),
                InlineKeyboardButton(t(assignee_row["language"], "btn_open_tasks"), callback_data="emp:mytasks"),
            ]])
        )
    except Exception as e:
        logger.warning("Failed to notify employee: %s", e)
    await schedule_task_deadline(context.application, task_id, assignee_row["telegram_id"], title, deadline_iso)
    await update.message.reply_text(t(lang, "task_assigned_manager_ok", username=assignee_row["username"] or assignee_row["telegram_id"], task_id=task_id), reply_markup=main_keyboard(mgr_row))

@manager_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE, mgr_row: Dict[str, Any]):
    lang = mgr_row["language"]
    items = await db.employee_status_counters()
    lines = [t(lang, "manager_status_header")]
    for it in items:
        lines.append(t(lang, "manager_status_item", username=it["username"], total=it["total"], done=it["done"], open=it["open"]))
    await update.message.reply_text("\n".join(lines), reply_markup=main_keyboard(mgr_row), disable_web_page_preview=True)

@manager_only
async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE, mgr_row: Dict[str, Any]):
    lang = mgr_row["language"]
    today = datetime.now(TZ).date().isoformat()
    rows = await db.aggregate_day(today)
    lines = [t(lang, "manager_report_header", date=today)]
    for r in rows:
        lines.append(t(lang, "manager_report_line", username=r["username"], done=r["done"], open=r["open"]))
    await update.message.reply_text("\n".join(lines), reply_markup=main_keyboard(mgr_row), disable_web_page_preview=True)

@private_chat_required
async def cmd_mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user_row = await db.get_user(u.id)
    lang = user_row["language"] if user_row else DEFAULT_LANG
    tasks = await db.list_tasks_for_user(u.id)
    if not tasks:
        await update.message.reply_text(t(lang, "no_tasks"), reply_markup=main_keyboard(user_row))
        return
    lines = [t(lang, "your_tasks_header")]
    for tsk in tasks:
        dd = tsk['deadline'] or "-"
        lines.append(t(lang, "task_line", id=tsk["id"], priority=tsk["priority"], title=tsk["title"], status=tsk["status"], deadline=dd))
    await update.message.reply_text("\n".join(lines), reply_markup=main_keyboard(user_row), disable_web_page_preview=True)

@private_chat_required
async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user_row = await db.get_user(u.id)
    lang = user_row["language"] if user_row else DEFAULT_LANG
    if not context.args:
        await update.message.reply_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))
        return
    try:
        task_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))
        return
    task = await db.get_task(task_id)
    if not task or task["assigned_to"] != u.id:
        await update.message.reply_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))
        return
    await db.mark_task_done(task_id)
    await update.message.reply_text(t(lang, "task_done_ok", task_id=task_id), reply_markup=main_keyboard(user_row))
    text = t(lang, "task_done_notify_manager", username=user_row["username"] or u.full_name, task_id=task_id)
    for mid in get_manager_ids():
        try: await context.bot.send_message(mid, text)
        except Exception: pass

@private_chat_required
async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user_row = await db.get_user(u.id)
    await update.message.reply_text(t(user_row["language"], "choose_language"), reply_markup=language_keyboard())

@private_chat_required
async def cmd_report_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user_row = await db.get_user(u.id)
    lang = user_row["language"]
    context.user_data["awaiting_report"] = True
    await update.message.reply_text(t(lang, "report_prompt"), reply_markup=main_keyboard(user_row))

@private_chat_required
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user_row = await db.get_user(u.id)
    lang = user_row["language"] if user_row else DEFAULT_LANG
    if context.user_data.get("awaiting_report"):
        today = datetime.now(TZ).date().isoformat()
        agg = await db.aggregate_day(today)
        done_today = 0
        for r in agg:
            if r["username"] == (user_row["username"] or "-"):
                done_today = r["done"]
                break
        await db.add_report(user_id=u.id, date_iso=today, content=update.message.text, tasks_completed=done_today)
        context.user_data["awaiting_report"] = False
        await update.message.reply_text(t(lang, "report_saved"), reply_markup=main_keyboard(user_row))
        return

    # Manager provides @username for invite
    if context.user_data.get('await_username_for_invite') and is_manager(user_row):
        text = (update.message.text or '').strip()
        if not text.startswith('@') or len(text) < 2:
            await update.message.reply_text(t(lang, 'enter_username_error'), reply_markup=main_keyboard(user_row))
            return
        username = text[1:]
        import secrets, string
        code = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        await db.create_invite(code=code, username=username, created_by=u.id, created_at=datetime.utcnow().isoformat())
        link = build_invite_link(context, code)
        await update.message.reply_text(t(lang, 'invite_created', username=username, link=link), reply_markup=main_keyboard(user_row), disable_web_page_preview=True)
        context.user_data['await_username_for_invite'] = False
        return

    await update.message.reply_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))

@manager_only
async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, mgr_row: Dict[str, Any]):
    lang = mgr_row["language"]
    voice = update.message.voice
    if not voice:
        return
    file = await context.bot.get_file(voice.file_id)
    tmp_dir = "/tmp/taskbot"; os.makedirs(tmp_dir, exist_ok=True)
    local_path = os.path.join(tmp_dir, f"{voice.file_unique_id}.oga")
    await file.download_to_drive(local_path)
    text = await transcribe_voice(local_path) or ""
    if not text:
        await update.message.reply_text(t(lang, "unknown_command"), reply_markup=main_keyboard(mgr_row))
        return
    parsed = await ai_parse_task(text)
    username = parsed.get("username")
    title = parsed.get("title") or "Task"
    deadline_iso = parsed.get("deadline_iso")
    priority = (parsed.get("priority") or DEFAULT_PRIORITY)

    assignee_row = None
    if username:
        assignee_row = await db.get_user_by_username(username)
    if not assignee_row:
        employees = await db.get_all_employees()
        await update.message.reply_text(t(lang, "voice_parsed", username=username or "?", title=title or "?", deadline=deadline_iso or "-", priority=priority))
        await update.message.reply_text(t(lang, "select_employee"), reply_markup=employees_keyboard(employees, prefix=f"assign:{title}|{deadline_iso or ''}|{priority}:"))
        return

    task_id = await db.add_task(title=title, description=title, created_by=mgr_row["telegram_id"], assigned_to=assignee_row["telegram_id"], deadline=deadline_iso, priority=priority)
    await schedule_task_deadline(context.application, task_id, assignee_row["telegram_id"], title, deadline_iso)
    try:
        await context.bot.send_message(assignee_row["telegram_id"],
            t(assignee_row["language"], "task_assigned_to", title=title, deadline=deadline_iso or "-", priority=priority),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t(assignee_row["language"], "btn_mark_done"), callback_data=f"done:{task_id}"),
                InlineKeyboardButton(t(assignee_row["language"], "btn_open_tasks"), callback_data="emp:mytasks"),
            ]])
        )
    except Exception as e:
        logger.warning("Failed to notify assignee from voice: %s", e)
    await update.message.reply_text(t(lang, "task_assigned_manager_ok", username=assignee_row["username"] or assignee_row["telegram_id"], task_id=task_id), reply_markup=main_keyboard(mgr_row))

# ---------- Callback queries ----------
@private_chat_required
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    u = update.effective_user
    user_row = await db.get_user(u.id)
    lang = user_row["language"] if user_row else DEFAULT_LANG
    data = q.data or ""

    if data == "mgr:assign":
        await q.edit_message_text(t(lang, "assign_task_prompt"), reply_markup=main_keyboard(user_row))
    elif data == "mgr:status":
        fake_update = Update(update.update_id, message=update.effective_message)
        await cmd_status(fake_update, context, user_row)
    elif data == "mgr:reports":
        fake_update = Update(update.update_id, message=update.effective_message)
        await cmd_report(fake_update, context, user_row)
    elif data == "mgr:employees":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(lang, "btn_employees_list"), callback_data="empl:list"),
             InlineKeyboardButton(t(lang, "btn_employee_add"), callback_data="empl:add")],
            [InlineKeyboardButton(t(lang, "btn_employee_invite"), callback_data="empl:invite"),
             InlineKeyboardButton(t(lang, "btn_employee_remove"), callback_data="empl:remove")],
            [InlineKeyboardButton("⬅️", callback_data="common:back")]
        ])
        await q.edit_message_text(t(lang, "employees_menu_title"), reply_markup=kb)
    elif data == "empl:list":
        emps = await db.get_all_employees()
        if not emps:
            await q.edit_message_text(t(lang, "no_employees"), reply_markup=main_keyboard(user_row))
        else:
            lines = [t(lang, "employees_list_header")]
            for e in emps:
                lines.append(t(lang, "employees_list_line", username=e["username"] or e["telegram_id"], full_name=e["full_name"] or "-"))
            await q.edit_message_text("\n".join(lines), reply_markup=main_keyboard(user_row))
    elif data in ("empl:add", "empl:invite"):
        context.user_data["await_username_for_invite"] = True
        await q.edit_message_text(t(lang, "prompt_employee_username"), reply_markup=main_keyboard(user_row))
    elif data == "empl:remove":
        emps = await db.get_all_employees()
        if not emps:
            await q.edit_message_text(t(lang, "no_employees"), reply_markup=main_keyboard(user_row))
        else:
            buttons = []
            row = []
            for e in emps:
                label = f"@{e['username']}" if e["username"] else str(e["telegram_id"])
                row.append(InlineKeyboardButton(label, callback_data=f"empl:del:{e['telegram_id']}"))
                if len(row) == 2:
                    buttons.append(row); row = []
            if row: buttons.append(row)
            buttons.append([InlineKeyboardButton("⬅️", callback_data="mgr:employees")])
            await q.edit_message_text(t(lang, "employees_list_header"), reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("assign:"):
        try:
            payload, tid = data.split("assign:",1)[1].split(":")
            title, deadline, priority = payload.split("|")
            assignee_id = int(tid)
            task_id = await db.add_task(title=title, description=title, created_by=u.id, assigned_to=assignee_id, deadline=(deadline or None), priority=priority or DEFAULT_PRIORITY)
            assignee = await db.get_user(assignee_id)
            if assignee:
                await context.bot.send_message(assignee_id,
                    t(assignee["language"], "task_assigned_to", title=title, deadline=deadline or "-", priority=priority or DEFAULT_PRIORITY),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(t(assignee["language"], "btn_mark_done"), callback_data=f"done:{task_id}"),
                        InlineKeyboardButton(t(assignee["language"], "btn_open_tasks"), callback_data="emp:mytasks"),
                    ]])
                )
            await schedule_task_deadline(context.application, task_id, assignee_id, title, deadline or None)
            await q.edit_message_text(t(lang, "task_assigned_manager_ok", username=assignee["username"] if assignee else assignee_id, task_id=task_id), reply_markup=main_keyboard(user_row))
        except Exception as e:
            logger.exception("Assign via callback failed: %s", e)
            await q.edit_message_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))
    elif data.startswith("empl:del:"):
        try:
            tid = int(data.split(":")[-1])
            emp = await db.get_user(tid)
            ok = await db.deactivate_user(tid)
            for name in (f"morning:{tid}", f"evening:{tid}"):
                for j in context.application.job_queue.get_jobs_by_name(name):
                    j.schedule_removal()
            uname = (emp["username"] if emp else tid)
            await q.edit_message_text(t(lang, "employee_removed_ok", username=uname), reply_markup=main_keyboard(user_row))
        except Exception as e:
            logger.exception("Failed to delete employee: %s", e)
            await q.edit_message_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))
    elif data == "emp:mytasks":
        fake_update = Update(update.update_id, message=update.effective_message)
        await cmd_mytasks(fake_update, context)
    elif data == "emp:report":
        fake_update = Update(update.update_id, message=update.effective_message)
        await cmd_report_employee(fake_update, context)
    elif data == "common:language":
        await q.edit_message_text(t(lang, "choose_language"), reply_markup=language_keyboard())
    elif data.startswith("lang:"):
        new_lang = data.split(":")[1]
        await db.set_user_language(u.id, new_lang)
        await q.edit_message_text(t(new_lang, "lang_set_ok", lang=new_lang), reply_markup=main_keyboard(await db.get_user(u.id)))
    elif data == "common:help":
        await q.edit_message_text(t(lang, "help_text"), reply_markup=main_keyboard(user_row))
    elif data == "common:back":
        await q.edit_message_text(t(lang, "welcome_manager") if is_manager(user_row) else t(lang, "welcome_employee"), reply_markup=main_keyboard(user_row))
    elif data.startswith("done:"):
        try:
            task_id = int(data.split(":",1)[1])
            task = await db.get_task(task_id)
            if not task or task["assigned_to"] != u.id:
                await q.edit_message_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))
                return
            await db.mark_task_done(task_id)
            await q.edit_message_text(t(lang, "task_done_ok", task_id=task_id), reply_markup=main_keyboard(user_row))
            text = t(lang, "task_done_notify_manager", username=user_row["username"] or u.full_name, task_id=task_id)
            for mid in get_manager_ids():
                try: await context.bot.send_message(mid, text)
                except Exception: pass
        except Exception:
            await q.edit_message_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))
    else:
        await q.edit_message_text(t(lang, "unknown_command"), reply_markup=main_keyboard(user_row))

# ---------- Jobs ----------
async def reminder_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data or {}
    user_id = data.get("user_id")
    if not user_id:
        return
    user_row = await db.get_user(user_id)
    if not user_row:
        return
    lang = user_row["language"]
    if context.job.name.startswith("morning:"):
        msg = t(lang, "daily_morning")
    else:
        msg = t(lang, "daily_evening")
    try:
        await context.bot.send_message(user_id, msg, reply_markup=main_keyboard(user_row))
    except Exception as e:
        logger.warning("Failed to send reminder to %s: %s", user_id, e)

async def deadline_job(context: ContextTypes.DEFAULT_TYPE):
    d = context.job.data or {}
    chat_id = d.get("chat_id")
    title = d.get("title")
    deadline = d.get("deadline")
    task_id = d.get("task_id")
    if not chat_id:
        return
    user_row = await db.get_user(chat_id)
    lang = user_row["language"] if user_row else DEFAULT_LANG
    try:
        await context.bot.send_message(chat_id, t(lang, "deadline_soon", task_id=task_id, title=title, deadline=deadline))
    except Exception:
        pass

async def daily_manager_report(app: Application):
    today = datetime.now(TZ).date().isoformat()
    rows = await db.aggregate_day(today)
    if not rows:
        return
    text_lines = ["📊 Daily Report", f"Date: {today}"]
    for r in rows:
        text_lines.append(f"@{r['username']}: ✅ {r['done']} | 🟡 {r['open']}")
    text = "\n".join(text_lines)
    for mid in get_manager_ids():
        try:
            await app.bot.send_message(mid, text)
        except Exception:
            pass

async def schedule_daily_manager_report(app: Application):
    for j in app.job_queue.get_jobs_by_name("daily_manager_report"):
        j.schedule_removal()
    app.job_queue.run_daily(callback=lambda ctx: asyncio.create_task(daily_manager_report(ctx.application)), time=Config.DAILY_REPORT_TIME, days=(0,1,2,3,4,5,6), name="daily_manager_report", tzinfo=TZ)

# ---------- Application setup ----------
def build_application() -> Application:
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("mytasks", cmd_mytasks))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("language", cmd_language))

    app.add_handler(MessageHandler(filters.VOICE & (~filters.COMMAND), on_voice))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), on_text))
    app.add_handler(CallbackQueryHandler(on_callback))

    async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.exception("Error handling update: %s", context.error)
        try:
            if isinstance(update, Update) and update.effective_user:
                user_row = await db.get_user(update.effective_user.id)
                lang = user_row["language"] if user_row else DEFAULT_LANG
                await context.bot.send_message(update.effective_user.id, "⚠️ Xatolik. Qayta urinib ko‘ring.", reply_markup=main_keyboard(user_row))
        except Exception:
            pass
    app.add_error_handler(on_error)

    async def on_start(app: Application):
        await db.connect()
        await schedule_daily_manager_report(app)
        me = await app.bot.get_me()
        app.bot_data['bot_username'] = me.username
        logger.info("Bot started as @%s", me.username)

    app.post_init = on_start
    return app

def main():
    if not Config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    app = build_application()
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
