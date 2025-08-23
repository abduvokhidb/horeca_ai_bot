# 📋 Task Management Telegram Bot

Ko'p tilli (O'zbek, Rus, Qozoq) vazifalar boshqaruvi boti.

## ✨ Xususiyatlar

- 🌐 **3 ta til**: O'zbek, Rus, Qozoq
- 📋 **Vazifalar boshqaruvi**: yaratish, tahrirlash, o'chirish
- 📁 **Loyihalar**: vazifalarni guruhlash
- 👥 **Jamoalar**: birgalikda ishlash
- 📅 **Kalendar**: muddatlarni kuzatish
- 📊 **Hisobotlar**: statistika va tahlil
- 🔔 **Bildirishnomalar**: eslatmalar

## 🚀 O'rnatish

### 1. Repository'ni klonlash
```bash
git clone https://github.com/yourusername/task-management-bot.git
cd task-management-bot
```

### 2. Virtual environment yaratish
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Environment sozlash
```bash
cp .env.example .env
```

`.env` faylini tahrirlang va bot tokenini kiriting:
```
BOT_TOKEN=your_bot_token_here
```

### 5. Bot token olish
1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` komandasi bilan yangi bot yarating
3. Bot nomini va username kiriting
4. Olingan tokenni `.env` fayliga qo'ying

### 6. Botni ishga tushirish
```bash
python bot.py
```

## 📝 Asosiy komandalar

- `/start` - Botni boshlash
- `/help` - Yordam
- `/newtask` - Yangi vazifa
- `/mytasks` - Vazifalarim
- `/projects` - Loyihalar
- `/teams` - Jamoalar
- `/settings` - Sozlamalar

## 📁 Fayl strukturasi

```
task-management-bot/
├── bot.py              # Asosiy bot fayli
├── config.py           # Konfiguratsiya
├── database.py         # Ma'lumotlar bazasi
├── languages.py        # Tillar
├── requirements.txt    # Kutubxonalar
├── .env.example        # Environment namuna
├── .gitignore         # Git ignore
└── README.md          # Dokumentatsiya
```

## 🔧 Konfiguratsiya

`.env` faylida quyidagi sozlamalar mavjud:

- `BOT_TOKEN` - Bot tokeni (majburiy)
- `ADMIN_IDS` - Admin ID'lari (ixtiyoriy)
- `DB_FILE` - Ma'lumotlar bazasi fayli
- `TIMEZONE` - Vaqt zonasi
- `DEBUG` - Debug rejimi

## 🌐 Tillarni qo'shish

Yangi til qo'shish uchun `languages.py` faylida yangi til obyektini qo'shing:

```python
LANGUAGES = {
    'en': {
        'name': '🇬🇧 English',
        'welcome': 'Welcome!',
        # ... boshqa tarjimalar
    }
}
```

## 🐛 Muammolarni hal qilish

### Python versiyasi
Bot Python 3.8+ talab qiladi. Python 3.13 da muammolar bo'lsa, Python 3.11 yoki 3.12 dan foydalaning.

### Token xatoligi
Agar "Unauthorized" xatosi chiqsa, tokenni tekshiring va to'g'ri kiritilganligiga ishonch hosil qiling.

### Ma'lumotlar saqlanmayapti
`bot_data.json` fayli yaratilganligini va yozish huquqi borligini tekshiring.

## 🤝 Hissa qo'shish

1. Fork qiling
2. Yangi branch yarating (`git checkout -b feature/amazing`)
3. O'zgarishlarni commit qiling (`git commit -m 'Add feature'`)
4. Push qiling (`git push origin feature/amazing`)
5. Pull Request oching

## 📄 Litsenziya

MIT License

## 💬 Aloqa

Savollar bo'lsa: [@your_telegram](https://t.me/your_telegram)

## ⭐ Minnatdorchilik

Agar loyiha yoqsa, ⭐ qo'yishni unutmang!
