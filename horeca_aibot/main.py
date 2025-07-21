import logging
from aiogram import Bot, Dispatcher, types, executor
from config import TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📊 Отчёт за день", "📈 Дешборд (PDF)", "⚙️ Настройки")
    await message.answer("Добро пожаловать в HORECA AI Bot!", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "📊 Отчёт за день")
async def daily_report(message: types.Message):
    await message.answer("💵 Выручка: 12,480,000 сум\n🧾 Средний чек: 67,826 сум\n👥 Гостей: 184\n\n🍽 ТОП-3 блюда:\n1. Адана кебаб — 58\n2. Лахмаджун — 46\n3. Чай турецкий — 102")

@dp.message_handler(lambda message: message.text == "📈 Дешборд (PDF)")
async def dashboard(message: types.Message):
    await message.answer("📎 Дешборд в PDF пока в разработке.")

@dp.message_handler(lambda message: message.text == "⚙️ Настройки")
async def settings(message: types.Message):
    await message.answer("⚙️ Раздел настроек скоро появится.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
