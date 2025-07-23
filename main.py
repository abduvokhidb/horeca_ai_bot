import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import openai
from config import BOT_TOKEN, OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.INFO)

keyboard = ReplyKeyboardMarkup([
    ["📊 Отчёт за день", "📈 Дешборд (PDF)"],
    ["⚙️ Настройки", "🤖 Задать вопрос"]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в HORECA AI Bot!", reply_markup=keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📊 Отчёт за день":
        await update.message.reply_text("💵 Выручка: 12,480,000 сум\n🧾 Средний чек: 67,826 сум\n👥 Гостей: 184\n\n🍽 ТОП-3 блюда:\n1. Адана кебаб — 58\n2. Лахмаджун — 46\n3. Чай турецкий — 102")
    elif text == "📈 Дешборд (PDF)":
        await update.message.reply_text("📎 PDF-дешборд скоро будет доступен.")
    elif text == "⚙️ Настройки":
        await update.message.reply_text("⚙️ Раздел настроек в разработке.")
    elif text == "🤖 Задать вопрос":
        await update.message.reply_text("Напишите вопрос, и я постараюсь ответить как эксперт.")
        context.user_data["awaiting_question"] = True
    elif context.user_data.get("awaiting_question"):
        await update.message.chat.send_action(action="typing")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты профессиональный ресторанный помощник, знаешь всё о кухне, персонале, iiko, инструкциях, открытии смен, обслуживании, управлении кофейней."},
                {"role": "user", "content": text}
            ],
            temperature=0.5
        )
        answer = response["choices"][0]["message"]["content"]
        await update.message.reply_text(answer)
        context.user_data["awaiting_question"] = False

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    app.run_polling()
