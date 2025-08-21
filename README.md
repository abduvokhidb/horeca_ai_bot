# Telegram Task Bot

Oddiy Telegram bot — xodimlarga vazifalar berish va ularni yakunlashni nazorat qilish uchun.

## O‘rnatish

1. GitHub’dan klon qiling:
   ```bash
   git clone https://github.com/username/telegram-task-bot.git
   cd telegram-task-bot
   ```

2. Kutubxonalarni o‘rnating:
   ```bash
   pip install -r requirements.txt
   ```

3. `.env` faylda yoki Render sozlamalarida tokenni belgilang:
   ```
   BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   ```

4. Render’da deploy qilish:
   - New Web Service → Python → GitHub repo
   - `Procfile` avtomatik ishlaydi
   - Environment variables: `BOT_TOKEN`

## Buyruqlar
- `/start` – boshlash
- `/vazifalar` – vazifalar ro‘yxati
- `/yakunlash` – vazifani tugallash
