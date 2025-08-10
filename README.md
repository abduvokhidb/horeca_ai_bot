# Namoz Vaqti Bot — Test

Ushbu branch/test kodi `@namozvaqtitest` kanalidan *API ishlatmasdan* (t.me/s/ orqali) namoz vaqtlarini oladi. 
Matn topilsa — matndan, topilmasa — postdagi rasm(lar)dan **OCR** orqali (Lotin/Kiril/Arab) vaqtlarni chiqaradi.

## O‘rnatish
1) Python 3.10+
2) `.env` fayl yarating:
```
BOT_TOKEN=YOUR_ROTATED_TEST_BOT_TOKEN
CHANNEL_URL=https://t.me/s/namozvaqtitest
```
3) Kutubxonalar:
```
pip install -r requirements-2.txt
```
4) Ishga tushirish:
```
python bot-3.py
```

## Buyruqlar
- `/jadval` — barcha masjidlar jadvali
- `/vaqt <qidiruv>` — masjid nomi bo‘yicha filter

> Eslatma: OCR modeli birinchi ishga tushishda yuklanadi, kichik kechikish normal.
