
# Telegram Vazifa Boshqaruv Boti (Python 3.11+, PTB 20.7)

Bu bot shaxsiy chatda ishlovchi **MENEJER–XODIM** tizimi: vazifalarni tayinlash, kuzatish, hisobot va eslatmalar, ovozdan matnga va AI yordamida vazifaga ajratish. Ma'lumotlar **SQLite** da.

## Imkoniyatlar
- Faqat shaxsiy chat (guruhlar yo‘q)
- Rollar: **MENEJER** va **XODIM**
- Menejer: `/task`, `/status`, `/report`, ovozli xabar → Whisper → AI-parsing
- Xodim: `/mytasks`, `/done <ID>`, `/report` oqimi
- Ko‘p tilli (UZ/RU/KK), `/language`
- Eslatmalar: 09:00 va 18:00
- Deadline eslatmalari (−2 soat va deadline vaqti)
- Ustuvorlik: Low/Medium/High/Urgent
- **Hodimlar bo‘limi**: ro‘yxat, qo‘shish (invite), o‘chirish
- **@username orqali deep-link taklif**: `https://t.me/<bot>?start=inv_<kod>`

## O‘rnatish
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # .env ni to‘ldiring
python bot.py
```

## Foydalanish
- Menejer paneli: `/start` → “👤 Hodimlar” bo‘limi
- Taklif: “➕ Hodim qo‘shish” yoki “🔗 Taklif havolasi” → @username yuboring → bot havola beradi
- O‘chirish: “🗑️ Hodimni o‘chirish” → ro‘yxatdan tanlang
- Xodim `/start inv_...` orqali kirsa, roli avtomatik **XODIM** bo‘ladi

## Jadval va loglar
- TZ: Asia/Tashkent (o‘zgartirish `.env` da)
- Log daraja: `LOG_LEVEL` (`INFO` standart)
