# bot.py
import os
import html
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, Defaults, ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram import Update
from source_quqon import get_latest_table, to_text_table

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylda ko‘rsatilmagan")

# Telegram app
app = ApplicationBuilder().token(BOT_TOKEN).defaults(Defaults(parse_mode=ParseMode.HTML)).build()

async def _safe_reply(chat, text: str):
    """HTML xatolarsiz javob yuborish."""
    try:
        await chat.send_message(html.escape(text), disable_web_page_preview=True)
    except BadRequest:
        await chat.send_message(text, disable_web_page_preview=True)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _safe_reply(
        update.effective_chat,
        "Assalomu alaykum!\n"
        "/jadval — barcha masjidlar jadvali\n"
        "/vaqt <qidiruv> — ma’lum masjid bo‘yicha filter"
    )

async def cmd_jadval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_latest_table()
    if not rows:
        await _safe_reply(update.effective_chat, "Hozircha jadval topilmadi.")
        return
    await _safe_reply(update.effective_chat, to_text_table(rows))

async def cmd_vaqt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = " ".join(context.args).strip() if context.args else ""
    rows = get_latest_table()
    if not rows:
        await _safe_reply(update.effective_chat, "Ma’lumot yo‘q.")
        return
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in r["masjid"].lower()]
        if not rows:
            await _safe_reply(update.effective_chat, "Mos masjid topilmadi.")
            return
    await _safe_reply(update.effective_chat, to_text_table(rows))

def main():
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("jadval", cmd_jadval))
    app.add_handler(CommandHandler("vaqt", cmd_vaqt))
    app.run_polling()

if __name__ == "__main__":
    main()
