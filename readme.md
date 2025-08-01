# 🤖 Horeca AI Bot - Production Ready

Restoran hodimlarini boshqarish va tozalik nazorati uchun AI-powered Telegram bot.

## 🚀 Deploy to Render

### 1. GitHub Repository Setup
Bu repository allaqachon tayyor: `https://github.com/abduvokhidb/horeca_ai_bot.git`

### 2. Render.com Deploy Qadamlari

1. **Render.com**ga kiring
2. **"New +"** tugmasini bosing
3. **"Web Service"** ni tanlang
4. **"Connect a repository"** tugmasi
5. GitHub hisobingizni ulang
6. `horeca_ai_bot` repository'ni tanlang

### 3. Deploy Sozlamalari

```yaml
Name: horeca-ai-bot
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python bot.py
```

**Environment Variables:**
- `BOT_TOKEN`: 8005801479:AAENfmXu1fCX7srHvBxLPhLaKNwydC_r23A
- `PORT`: 10000 (auto-set by Render)

### 4. Deploy Process

1. **"Create Web Service"** tugmasi
2. Build jarayoni 2-3 daqiqa davom etadi
3. ✅ Deploy tayyor!

## 📱 Test Qilish

### Bot Username: @horeca_aibot

**Test Raqamlar:**
- 👨‍💼 Admin: `+998900007747`
- ☕ Barista: `+998901234567`
- 💰 Kassir: `+998901234568`
- 🧹 Tozalovchi: `+998901234569`
- 🎩 Manager: `+998901234570`

### Test Jarayoni:
1. Telegram'da @horeca_aibot ga `/start` yuboring
2. Telefon raqamingizni kiriting
3. Knopkalarni sinab ko'ring
4. AI yordamchiga savol bering
5. Rasm yuklang (tozalovchi sifatida)

## ⚡ Funksiyalar

### ✅ Ishlaydigan Funksiyalar:
- 👥 **Hodimlar tizimi** - ro'yxatdan o'tish, profil
- 🧹 **Tozalik nazorati** - AI rasm tahlili
- 🤖 **AI Yordamchi** - real-time savol-javob
- 📊 **Statistika** - ish faoliyati hisobotlari
- 🛠️ **Admin panel** - boshqaruv funksiyalari
- 🌐 **Health check** - server monitoring

### 🔮 Keyingi Versiyalar:
- Ball tizimi va gamifikatsiya
- iiko API integratsiyasi
- Push bildirishnomalar
- Kengaytirilgan analytics

## 🗂️ Fayl Strukturasi

```
horeca_ai_bot/
├── bot.py              # Asosiy bot kodi
├── requirements.txt    # Python dependencies
├── render.yaml        # Render config
├── README.md          # Bu fayl
└── photos/            # Yuklangan rasmlar (avtomatik)
```

## 💾 Database

**SQLite** database quyidagi jadvallar bilan:
- `employees` - Hodimlar ma'lumotlari
- `cleaning_checks` - Tozalik tekshiruvlari
- `restaurant_info` - Restoran ma'lumotlari
- `ai_requests` - AI so'rovlari

## 🔧 Environment Variables

```bash
BOT_TOKEN=8005801479:AAENfmXu1fCX7srHvBxLPhLaKNwydC_r23A
DATABASE_PATH=horeca_bot.db
PORT=10000
```

## 📊 Monitoring

- **Health Check**: `https://your-app.onrender.com/health`
- **Status**: Render dashboard
- **Logs**: Render logs section

## 🛠️ Development

### Local Run:
```bash
# Clone repository
git clone https://github.com/abduvokhidb/horeca_ai_bot.git
cd horeca_ai_bot

# Install dependencies
pip install -r requirements.txt

# Run bot
python bot.py
```

### Deploy to Render:
1. Push changes to GitHub
2. Render automatically deploys
3. Check logs for status

## 🆘 Troubleshooting

### Bot Not Responding:
- Check Render logs
- Verify BOT_TOKEN
- Check health endpoint

### Database Issues:
- SQLite auto-creates on first run
- Check file permissions
- Verify data persistence

### Deploy Fails:
- Check requirements.txt
- Verify Python version compatibility
- Check Render build logs

## 📞 Support

- **Telegram**: @horeca_aibot
- **GitHub Issues**: Repository issues tab
- **Email**: admin@yourrestaurant.com

---

**🎉 Bot 24/7 ishlaydi va avtomatik yangilanadi!**

**Deploy Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 2025