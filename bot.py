# BROADCAST MESSAGE HANDLER
# =========================

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast xabarini yuborish"""
    user_id = str(update.effective_user.id)
    
    if not is_admin(user_id):
        return
    
    if user_id not in admin_temp_data or admin_temp_data[user_id].get('action') != 'broadcast_message':
        return
    
    broadcast_text = update.message.text
    
    if broadcast_text == '/cancel':
        del admin_temp_data[user_id]
        await update.message.reply_text(
            "❌ Broadcast bekor qilindi",
            reply_markup=get_admin_keyboard()
        )
        return
    
    # Tasdiqlash
    admin_temp_data[user_id]['message'] = broadcast_text
    
    keyboard = [
        [InlineKeyboardButton("✅ Ha, yuborish", callback_data="admin_confirm_broadcast")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_cancel_broadcast")]
    ]
    
    await update.message.reply_text(
        f"""📢 *BROADCAST TASDIQLASH*

Quyidagi xabar *{len(user_settings)}* ta foydalanuvchiga yuboriladi:

---
{broadcast_text}
---

Tasdiqlaysizmi?""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast tasdiqlash"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in admin_temp_data:
        await query.answer("❌ Ma'lumot topilmadi")
        return
    
    broadcast_message = admin_temp_data[user_id]['message']
    
    # Yuborish jarayoni
    await query.edit_message_text("📤 Xabar yuborilmoqda...")
    
    sent_count = 0
    error_count = 0
    
    for target_user_id in user_settings.keys():
        try:
            await bot_app.bot.send_message(
                chat_id=int(target_user_id),
                text=f"📢 *ADMIN XABARI*\n\n{broadcast_message}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            error_count += 1
            logger.warning(f"❌ Broadcast xabar yuborilmadi {target_user_id}: {e}")
    
    # Statistikani yangilash
    push_notification_stats['broadcast'] += sent_count
    push_notification_stats['error'] += error_count
    
    # Admin'ga natija
    result_message = f"""✅ *BROADCAST YAKUNLANDI*

📊 Natijalar:
• Muvaffaqiyatli yuborilgan: *{sent_count}*
• Xatoliklar: *{error_count}*
• Jami foydalanuvchilar: *{len(user_settings)}*

📅 Vaqt: {datetime.now().strftime("%d.%m.%Y %H:%M")}"""
    
    await query.edit_message_text(
        result_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]
        ])
    )
    
    # Temp data tozalash
    del admin_temp_data[user_id]

# MASJID QOSHISH VA TAHRIRLASH
# =============================

async def handle_add_masjid_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi masjid qo'shish setup"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    admin_temp_data[user_id] = {'action': 'add_masjid', 'step': 'name'}
    
    await query.edit_message_text(
        """➕ *YANGI MASJID QO'SHISH*

1️⃣ **Masjid nomini kiriting:**

Masalan: `YANGI JOME MASJIDI`

Bekor qilish uchun /cancel yozing.""",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_add_masjid_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi masjid ma'lumotlarini olish"""
    user_id = str(update.effective_user.id)
    
    if not is_admin(user_id) or user_id not in admin_temp_data:
        return
    
    data = admin_temp_data[user_id]
    
    if data.get('action') != 'add_masjid':
        return
    
    if update.message.text == '/cancel':
        del admin_temp_data[user_id]
        await update.message.reply_text(
            "❌ Masjid qo'shish bekor qilindi",
            reply_markup=get_admin_keyboard()
        )
        return
    
    step = data.get('step')
    
    if step == 'name':
        data['name'] = update.message.text.upper()
        data['step'] = 'coordinates'
        
        await update.message.reply_text(
            f"""✅ Nom saqlandi: *{data['name']}*

2️⃣ **Koordinatalarni kiriting:**

Format: `latitude,longitude`
Masalan: `40.3925,71.7412`

Google Maps'dan koordinata olishingiz mumkin.""",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif step == 'coordinates':
        try:
            coords = update.message.text.split(',')
            lat = float(coords[0].strip())
            lon = float(coords[1].strip())
            
            data['coordinates'] = [lat, lon]
            data['step'] = 'patterns'
            
            await update.message.reply_text(
                f"""✅ Koordinatalar saqlandi: *{lat}, {lon}*

3️⃣ **Pattern'larni kiriting:**

Masjid nomining turli variantlarini kiriting (vergul bilan ajratib):

Masalan: `yangi masjid, yangi jome, yangi masjidi`""",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            await update.message.reply_text(
                "❌ Noto'g'ri format! Namuna: `40.3925,71.7412`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif step == 'patterns':
        patterns = [p.strip().lower() for p in update.message.text.split(',')]
        data['patterns'] = patterns
        data['step'] = 'times'
        
        await update.message.reply_text(
            f"""✅ Pattern'lar saqlandi: *{len(patterns)} ta*

4️⃣ **Namaz vaqtlarini kiriting:**

Format: `Bomdod:HH:MM,Peshin:HH:MM,Asr:HH:MM,Shom:HH:MM,Hufton:HH:MM`

Masalan: `Bomdod:05:00,Peshin:12:30,Asr:15:45,Shom:18:15,Hufton:20:00`""",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif step == 'times':
        try:
            times_data = {}
            for time_pair in update.message.text.split(','):
                prayer, time = time_pair.split(':')
                times_data[prayer.strip()] = time.strip()
            
            # Yangi masjid yaratish
            masjid_key = data['name'].replace(' ', '_').replace('JOME', '').replace('MASJIDI', '').strip('_')
            
            MASJIDLAR_3_ALIFBO[masjid_key] = {
                'full_name': data['name'],
                'coordinates': data['coordinates'],
                'patterns': {
                    'lotin': data['patterns'],
                    'kiril': [],
                    'arab': []
                },
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            masjidlar_data[masjid_key] = times_data
            
            # Natija
            result_message = f"""✅ *YANGI MASJID QO'SHILDI*

🕌 Nom: *{data['name']}*
📍 Koordinatalar: *{data['coordinates'][0]}, {data['coordinates'][1]}*
🔤 Pattern'lar: *{len(data['patterns'])} ta*
🕐 Vaqtlar: *{len(times_data)} ta*

🆔 Kalit: `{masjid_key}`"""
            
            await update.message.reply_text(
                result_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_admin_keyboard()
            )
            
            # Temp data tozalash
            del admin_temp_data[user_id]
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Xatolik: {e}\n\nTo'g'ri format: `Bomdod:05:00,Peshin:12:30,...`",
                parse_mode=ParseMode.MARKDOWN
            )

# UTILITY FUNCTIONS
# =================

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def detect_script_type(text: str) -> str:
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
    cyrillic_chars = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
    latin_chars = sum(1 for char in text if 'a' <= char.lower() <= 'z')
    
    total_chars = arabic_chars + cyrillic_chars + latin_chars
    
    if total_chars == 0:
        return "lotin"
    
    if arabic_chars / total_chars > 0.3:
        return "arab"
    elif cyrillic_chars / total_chars > 0.3:
        return "kiril"
    else:
        return "lotin"

def find_mosque_3_alifbo(text: str, threshold: float = 0.7) -> Optional[str]:
    text = text.lower().strip()
    script_type = detect_script_type(text)
    
    logger.info(f"🔍 Masjid qidirilmoqda: '{text[:50]}...' ({script_type} alifbosi)")
    
    best_match = None
    best_score = 0
    
    for mosque_key, mosque_data in MASJIDLAR_3_ALIFBO.items():
        for alifbo, patterns in mosque_data["patterns"].items():
            weight = 1.0 if alifbo == script_type else 0.8
            
            for pattern in patterns:
                score = similarity(text, pattern) * weight
                if score > threshold and score > best_score:
                    best_score = score
                    best_match = mosque_key
                
                if pattern in text:
                    logger.info(f"✅ To'g'ridan-to'g'ri mos keldi: {mosque_key} ({alifbo})")
                    return mosque_key
    
    if best_match:
        logger.info(f"🎯 Eng yaxshi mos kelishi: {best_match} ({best_score:.2f})")
    
    return best_match

def extract_prayer_times_3_alifbo(text: str) -> Dict[str, str]:
    prayer_times = {}
    text = text.lower()
    script_type = detect_script_type(text)
    
    logger.info(f"🕐 Namaz vaqtlari qidirilmoqda ({script_type} alifbosi)...")
    
    for alifbo, patterns in NAMAZ_VAQTLARI_3_ALIFBO.items():
        for prayer_name, pattern in patterns.items():
            if prayer_name not in prayer_times:
                matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
                if matches:
                    time_str = matches[0].replace('-', ':').replace('–', ':').replace('—', ':').replace('.', ':')
                    prayer_key = prayer_name.capitalize()
                    if prayer_key not in prayer_times:
                        prayer_times[prayer_key] = time_str
                        logger.info(f"    ✅ {prayer_key}: {time_str} ({alifbo})")
    
    return prayer_times

# CHANNEL MONITORING
# ==================

async def scrape_telegram_channel_3_alifbo():
    global last_posts_hash
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        logger.info(f"🌐 Kanal tekshirilmoqda: {CHANNEL_URL}")
        
        response = requests.get(CHANNEL_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        posts = soup.find_all('div', class_='tgme_widget_message')
        
        if not posts:
            logger.warning("⚠️ Hech qanday post topilmadi")
            return
        
        logger.info(f"📥 {len(posts)} ta post topildi")
        
        for post in posts[-3:]:
            await process_telegram_post_3_alifbo(post)
            
    except Exception as e:
        logger.error(f"❌ Kanal scraping xatolik: {e}")

async def process_telegram_post_3_alifbo(post):
    try:
        post_link = post.find('a', class_='tgme_widget_message_date')
        post_id = post_link.get('href', '').split('/')[-1] if post_link else 'unknown'
        
        post_content = str(post)
        post_hash = hashlib.md5(post_content.encode()).hexdigest()
        
        if post_id in last_posts_hash and last_posts_hash[post_id] == post_hash:
            return
        
        last_posts_hash[post_id] = post_hash
        logger.info(f"📋 Yangi post tahlil qilinmoqda: {post_id}")
        
        all_text = ""
        text_div = post.find('div', class_='tgme_widget_message_text')
        if text_div:
            all_text += text_div.get_text(strip=True, separator=' ')
            logger.info(f"📝 Matn topildi: {all_text[:100]}...")
        
        if all_text.strip():
            await analyze_post_content_3_alifbo(all_text, post_id)
        
    except Exception as e:
        logger.error(f"❌ Post tahlil xatolik: {e}")

async def analyze_post_content_3_alifbo(text: str, post_id: str):
    logger.info(f"🔍 Post {post_id} tahlil qilinmoqda...")
    
    mosque_key = find_mosque_3_alifbo(text)
    if not mosque_key:
        logger.info(f"⚠️ Post {post_id}da masjid nomi topilmadi")
        return
    
    prayer_times = extract_prayer_times_3_alifbo(text)
    if not prayer_times:
        logger.info(f"⚠️ Post {post_id}da namaz vaqtlari topilmadi")
        return
    
    await update_mosque_data_and_notify(mosque_key, prayer_times, post_id)

async def update_mosque_data_and_notify(mosque_key: str, new_prayer_times: Dict[str, str], post_id: str):
    if mosque_key not in masjidlar_data:
        logger.warning(f"⚠️ Noma'lum masjid: {mosque_key}")
        return
    
    mosque_name = MASJIDLAR_3_ALIFBO[mosque_key]["full_name"]
    old_times = masjidlar_data[mosque_key].copy()
    changes = {}
    
    for prayer, new_time in new_prayer_times.items():
        if prayer in old_times:
            if old_times[prayer] != new_time:
                changes[prayer] = {'old': old_times[prayer], 'new': new_time}
                masjidlar_data[mosque_key][prayer] = new_time
    
    if changes:
        logger.info(f"✅ {mosque_name} vaqtlari yangilandi: {changes}")
        await send_push_notifications(mosque_key, mosque_name, changes, post_id)
    else:
        logger.info(f"ℹ️ {mosque_name} vaqtlari o'zgarmagan")

async def send_push_notifications(mosque_key: str, mosque_name: str, changes: Dict[str, Dict], post_id: str):
    if not bot_app:
        return
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    
    message = f"🔔 *NAMAZ VAQTI YANGILANDI*\n\n🕌 *{mosque_name.replace('JOME MASJIDI', '').strip()}*\n\n"
    
    prayer_emojis = {"Bomdod": "🌅", "Peshin": "☀️", "Asr": "🌆", "Shom": "🌇", "Hufton": "🌙"}
    
    for prayer, change in changes.items():
        emoji = prayer_emojis.get(prayer, "🕐")
        message += f"{emoji} *{prayer}:* {change['old']} → *{change['new']}*\n"
    
    message += f"\n📅 Yangilangan: {now.strftime('%d.%m.%Y %H:%M')}\n📺 Manba: @{CHANNEL_USERNAME}"
    
    sent_count = 0
    for user_id, settings in user_settings.items():
        selected_mosques = set(settings.get('selected_masjids', []))
        if mosque_key in selected_mosques:
            try:
                await bot_app.bot.send_message(
                    chat_id=int(user_id),
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
                sent_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"⚠️ User {user_id}ga xabar yuborilmadi: {e}")
    
    push_notification_stats['auto_update'] += sent_count
    logger.info(f"📤 {sent_count} ta foydalanuvchiga notification yuborildi")

async def start_channel_monitoring_3_alifbo():
    logger.info(f"👀 Kanal monitoring boshlandi: @{CHANNEL_USERNAME}")
    
    while True:
        try:
            await scrape_telegram_channel_3_alifbo()
            await asyncio.sleep(120)  # 2 daqiqa
        except Exception as e:
            logger.error(f"❌ Monitoring xatolik: {e}")
            await asyncio.sleep(300)  # 5 daqiqa

# USER FUNCTIONS
# ==============

def get_user_selected_masjids(user_id: str) -> Set[str]:
    return set(user_settings.get(str(user_id), {}).get('selected_masjids', []))

def save_user_masjids(user_id: str, selected_masjids: Set[str]):
    user_id_str = str(user_id)
    if user_id_str not in user_settings:
        user_settings[user_id_str] = {}
    user_settings[user_id_str]['selected_masjids'] = list(selected_masjids)
    log_masjid_selection(user_id, list(selected_masjids))

def get_main_keyboard():
    keyboard = [
        ['🕐 Barcha vaqtlar', '⏰ Eng yaqin vaqt'],
        ['🕌 Masjidlar', '⚙️ Sozlamalar'],
        ['ℹ️ Yordam']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# BOT HANDLERS
# ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_user_join(str(user_id))
    log_user_activity(str(user_id), 'start')
    
    if str(user_id) not in user_settings:
        save_user_masjids(user_id, set(MASJIDLAR_3_ALIFBO.keys()))
    
    welcome_message = f"""🕌 Assalomu alaykum!

*Qo'qon Masjidlari Namaz Vaqti Botiga xush kelibsiz!*

🔄 *REAL-TIME YANGILANISHLAR:*
Bot @{CHANNEL_USERNAME} kanalini kuzatib turadi!

🔤 *3 ALIFBO QOLLAB-QUVVATLASH:*
• Lotin, Kiril, Arab

⚙️ Sozlamalar orqali masjidlarni tanlang."""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)
    
    log_user_activity(user_id, 'message')
    
    # Admin login check
    if text == ADMIN_PASSWORD:
        await admin_login(update, context)
        return
    
    # Admin panel check
    if is_admin(user_id):
        # Broadcast message check
        if user_id in admin_temp_data and admin_temp_data[user_id].get('action') == 'broadcast_message':
            await handle_broadcast_message(update, context)
            return
        # Add masjid data check
        elif user_id in admin_temp_data and admin_temp_data[user_id].get('action') == 'add_masjid':
            await handle_add_masjid_data(update, context)
            return
        # Admin panel navigation
        elif text in ['📊 User Analytics', '🕌 Masjid Management', '📢 Push Notifications', '📈 Statistics', '🔧 Manual Update', '⚙️ Bot Settings', '🚪 Admin Exit']:
            await handle_admin_panel(update, context)
            return
    
    # Regular user commands
    if text == '⚙️ Sozlamalar':
        log_user_activity(user_id, 'settings')
        await handle_settings(update, context)
    elif text == '🕌 Masjidlar':
        await handle_all_masjids(update, context)
    elif text == '🕐 Barcha vaqtlar':
        await handle_selected_masjids_times(update, context)
    elif text == '⏰ Eng yaqin vaqt':
        await handle_next_prayer(update, context)
    elif text == 'ℹ️ Yordam':
        await handle_help(update, context)
    else:
        await update.message.reply_text(
            "Quyidagi knopkalardan foydalaning:",
            reply_markup=get_main_keyboard()
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query handler"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    # Admin callbacks
    if data.startswith('admin_') and is_admin(user_id):
        await handle_admin_callback(update, context)
        return
    
    # Regular user callbacks
    # ... user callback handlers

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ Sozlamalar bo'limi",
        reply_markup=get_main_keyboard()
    )

async def handle_all_masjids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🕌 *BARCHA MASJIDLAR:*\n\n"
    
    for i, (key, data) in enumerate(MASJIDLAR_3_ALIFBO.items(), 1):
        message += f"{i}. {data['full_name']}\n"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_selected_masjids_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🕐 *NAMAZ VAQTLARI:*\n\n"
    
    for masjid_key in MASJIDLAR_3_ALIFBO.keys():
        if masjid_key in masjidlar_data:
            times = masjidlar_data[masjid_key]
            name = MASJIDLAR_3_ALIFBO[masjid_key]["full_name"]
            
            message += f"🕌 *{name.replace('JOME MASJIDI', '').strip()}*\n"
            message += f"🌅 Bomdod: *{times['Bomdod']}* ☀️ Peshin: *{times['Peshin']}*\n"
            message += f"🌆 Asr: *{times['Asr']}* 🌇 Shom: *{times['Shom']}* 🌙 Hufton: *{times['Hufton']}*\n\n"
    
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    message += f"⏰ Hozirgi vaqt: {current_time}\n🔄 @{CHANNEL_USERNAME} dan real-time yangilanadi"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_next_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    current_time = now.strftime("%H:%M")
    
    message = f"⏰ *ENG YAQIN NAMOZ VAQTI*\n\nHozirgi vaqt: {current_time}"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""ℹ️ *YORDAM*

🔄 *REAL-TIME MONITORING:*
Bot @{CHANNEL_USERNAME} kanalini kuzatadi

🔤 *3 ALIFBO:* Lotin, Kiril, Arab

👨‍💼 *Admin panel:* `{ADMIN_PASSWORD}` yozing

*Funksiyalar:*
🕐 Barcha vaqtlar
⏰ Eng yaqin vaqt  
🕌 Masjidlar ro'yxati
⚙️ Sozlamalar"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Xatolik yuz berdi:", exc_info=context.error)

def main():
    """Asosiy funksiya"""
    global bot_app
    
    try:
        threading.Thread(target=run_flask, daemon=True).start()
        
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Handlerlar
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot_app.add_handler(CallbackQueryHandler(handle_callback_query))
        bot_app.add_error_handler(error_handler)
        
        logger.info("✅ Bot ishga tushmoqda...")
        logger.info(f"🎯 Monitoring kanal: @{CHANNEL_USERNAME}")
        logger.info(f"👨‍💼 Admin parol: {ADMIN_PASSWORD}")
        
        print("🚀 Bot ishga tushdi! ✅")
        print(f"📺 Kanal: @{CHANNEL_USERNAME}")
        print(f"👨‍💼 Admin: '{ADMIN_PASSWORD}' yozing")
        
        # Monitoring thread
        def run_monitoring():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logger.info("🔄 Monitoring thread boshlandi")
                loop.run_until_complete(start_channel_monitoring_3_alifbo())
            except Exception as e:
                logger.error(f"❌ Monitoring xatolik: {e}")
            finally:
                loop.close()
        
        monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
        monitoring_thread.start()
        
        logger.info("✅ Monitoring thread ishga tushirildi")
        
        # Bot polling
        bot_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        print(f"❌ Xatolik: {e}")

if __name__ == '__main__':
    main()import os
import json
import asyncio
import logging
import threading
import math
import re
import requests
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Set, Optional
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import openai
from bs4 import BeautifulSoup
import schedule
import time
from difflib import SequenceMatcher
import hashlib
from collections import defaultdict, Counter

# OCR uchun (agar mavjud bo'lsa)
try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Health check uchun Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return 'Bot ishlaydi', 200

@app.route('/')
def home():
    return 'Masjidlar Bot - Admin Panel Active', 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot sozlamalari
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'quqonnamozvaqti')
CHANNEL_URL = f'https://t.me/s/{CHANNEL_USERNAME}'

# Test mode detection
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
if TEST_MODE:
    logger.info("🧪 TEST MODE faol!")
    test_channel = os.getenv('TEST_CHANNEL_USERNAME', CHANNEL_USERNAME)
    CHANNEL_USERNAME = test_channel
    CHANNEL_URL = f'https://t.me/s/{CHANNEL_USERNAME}'

logger.info(f"🎯 Monitoring kanal: @{CHANNEL_USERNAME}")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable kerak!")
    exit(1)

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# ADMIN PANEL TIZIMI
# ==================

ADMIN_PASSWORD = "menadminman"
admin_sessions = set()  # Faol admin sessiyalar
admin_temp_data = {}    # Vaqtinchalik admin ma'lumotlari

# ANALYTICS VA STATISTIKA
# ========================

user_activity = defaultdict(int)          # user_id: faollik soni
user_join_dates = {}                      # user_id: qo'shilgan sana
user_last_activity = {}                   # user_id: oxirgi faollik
masjid_popularity = defaultdict(int)      # masjid_key: tanlanish soni
daily_stats = defaultdict(lambda: defaultdict(int))  # sana: {metrika: son}
push_notification_stats = defaultdict(int)  # notification statistikasi

def log_user_activity(user_id: str, action: str):
    """Foydalanuvchi faolligini yozish"""
    user_activity[user_id] += 1
    user_last_activity[user_id] = datetime.now()
    
    today = datetime.now().strftime('%Y-%m-%d')
    daily_stats[today]['total_actions'] += 1
    daily_stats[today][action] += 1

def log_user_join(user_id: str):
    """Yangi foydalanuvchi qo'shilishini yozish"""
    if user_id not in user_join_dates:
        user_join_dates[user_id] = datetime.now()
        today = datetime.now().strftime('%Y-%m-%d')
        daily_stats[today]['new_users'] += 1

def log_masjid_selection(user_id: str, selected_masjids: List[str]):
    """Masjid tanlanishini yozish"""
    for masjid_key in selected_masjids:
        masjid_popularity[masjid_key] += 1

def is_admin(user_id: str) -> bool:
    """Admin ekanligini tekshirish"""
    return str(user_id) in admin_sessions

# Global variables
bot_app = None
user_settings = {}
last_posts_hash = {}

# MASJIDLAR MA'LUMOTLARI (JSON formatda saqlash uchun)
# ====================================================

MASJIDLAR_3_ALIFBO = {
    "NORBUTABEK": {
        "full_name": "NORBUTABEK JOME MASJIDI",
        "coordinates": [40.3925, 71.7412],
        "patterns": {
            "lotin": ["norbutabek", "norbu tabek", "norbu-tabek"],
            "kiril": ["норбутабек", "норбу табек"],
            "arab": ["نوربوتابيك", "نوربو تابيك"]
        },
        "created_date": "2025-01-01",
        "last_updated": "2025-08-11"
    },
    "GISHTLIK": {
        "full_name": "GISHTLIK JOME MASJIDI",
        "coordinates": [40.3901, 71.7389],
        "patterns": {
            "lotin": ["gishtlik", "g'ishtlik", "gʻishtlik"],
            "kiril": ["гиштлик", "ғиштлик"],
            "arab": ["غیشتلیك", "گشتلیك"]
        },
        "created_date": "2025-01-01",
        "last_updated": "2025-08-11"
    },
    "SHAYXULISLOM": {
        "full_name": "SHAYXULISLOM JOME MASJIDI",
        "coordinates": [40.3867, 71.7435],
        "patterns": {
            "lotin": ["shayxulislom", "shayx ul islom"],
            "kiril": ["шайхулислом", "шайх ул ислом"],
            "arab": ["شیخ الاسلام", "شایخ الاسلام"]
        },
        "created_date": "2025-01-01",
        "last_updated": "2025-08-11"
    }
}

# NAMAZ VAQTLARI PATTERNS
NAMAZ_VAQTLARI_3_ALIFBO = {
    "lotin": {
        "bomdod": r'(?:bomdod|fajr|subh)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:peshin|zuhr|zuhur)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:asr|ikindi)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:shom|maghrib)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:hufton|isha)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    },
    "kiril": {
        "bomdod": r'(?:бомдод|фажр|субх)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:пешин|зухр)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:аср|икинди)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:шом|магриб)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:хуфтон|иша)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    },
    "arab": {
        "bomdod": r'(?:فجر|صبح)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "peshin": r'(?:ظهر|زهر)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "asr": r'(?:عصر)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "shom": r'(?:مغرب)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})',
        "hufton": r'(?:عشاء|عشا)\s*[:\-–—]\s*(\d{1,2}[:\-–—.]\d{2})'
    }
}

# Default namaz vaqtlari
masjidlar_data = {
    "NORBUTABEK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:45", "Shom": "19:35", "Hufton": "21:15"},
    "GISHTLIK": {"Bomdod": "04:45", "Peshin": "12:50", "Asr": "17:15", "Shom": "19:30", "Hufton": "21:00"},
    "SHAYXULISLOM": {"Bomdod": "04:45", "Peshin": "12:45", "Asr": "17:35", "Shom": "19:35", "Hufton": "21:15"}
}

# ADMIN FUNCTIONS
# ===============

async def admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin login"""
    user_id = str(update.effective_user.id)
    
    if update.message.text == ADMIN_PASSWORD:
        admin_sessions.add(user_id)
        await update.message.reply_text(
            "🔐 *ADMIN PANEL*\n\nXush kelibsiz, Admin!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_keyboard()
        )
        logger.info(f"👨‍💼 Admin login: {user_id}")
    else:
        await update.message.reply_text("❌ Noto'g'ri parol")

def get_admin_keyboard():
    """Admin klaviaturasi"""
    keyboard = [
        ['📊 User Analytics', '🕌 Masjid Management'],
        ['📢 Push Notifications', '⚙️ Bot Settings'],
        ['📈 Statistics', '🔧 Manual Update'],
        ['🚪 Admin Exit']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel handler"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if not is_admin(user_id):
        return
    
    if text == '📊 User Analytics':
        await show_user_analytics(update, context)
    elif text == '🕌 Masjid Management':
        await show_masjid_management(update, context)
    elif text == '📢 Push Notifications':
        await show_push_notifications(update, context)
    elif text == '📈 Statistics':
        await show_statistics(update, context)
    elif text == '🔧 Manual Update':
        await show_manual_update(update, context)
    elif text == '⚙️ Bot Settings':
        await show_bot_settings(update, context)
    elif text == '🚪 Admin Exit':
        admin_sessions.discard(user_id)
        await update.message.reply_text(
            "👋 Admin paneldan chiqildi",
            reply_markup=get_main_keyboard()
        )

async def show_user_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User analytics ko'rsatish"""
    total_users = len(user_settings)
    active_users = len([u for u, last in user_last_activity.items() 
                       if last > datetime.now() - timedelta(days=7)])
    
    # Eng faol userlar
    top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Yangi userlar (oxirgi 7 kun)
    week_ago = datetime.now() - timedelta(days=7)
    new_users = len([d for d in user_join_dates.values() if d > week_ago])
    
    # Masjid tanlash statistikasi
    avg_masjids = sum(len(settings.get('selected_masjids', [])) 
                     for settings in user_settings.values()) / max(total_users, 1)
    
    message = f"""📊 *USER ANALYTICS*

👥 *Umumiy statistika:*
• Jami foydalanuvchilar: *{total_users}*
• Faol foydalanuvchilar (7 kun): *{active_users}*
• Yangi foydalanuvchilar (7 kun): *{new_users}*
• O'rtacha tanlangan masjidlar: *{avg_masjids:.1f}*

🏆 *Top 5 faol foydalanuvchilar:*"""
    
    for i, (user_id, activity) in enumerate(top_users, 1):
        try:
            user = await bot_app.bot.get_chat(int(user_id))
            name = user.first_name or "Noma'lum"
        except:
            name = "Noma'lum"
        message += f"\n{i}. {name}: {activity} ta harakat"
    
    # Inline keyboard
    keyboard = [
        [InlineKeyboardButton("📈 Batafsil statistika", callback_data="admin_detailed_stats")],
        [InlineKeyboardButton("📤 Eksport", callback_data="admin_export_users")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_masjid_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Masjid boshqaruvi"""
    message = "🕌 *MASJID MANAGEMENT*\n\n"
    
    # Masjidlar ro'yxati
    for key, data in MASJIDLAR_3_ALIFBO.items():
        popularity = masjid_popularity[key]
        coords = data['coordinates']
        message += f"• *{data['full_name']}*\n"
        message += f"  📍 Koordinatalar: {coords[0]}, {coords[1]}\n"
        message += f"  📊 Tanlanish: {popularity} marta\n"
        message += f"  📅 Yangilangan: {data['last_updated']}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Yangi masjid", callback_data="admin_add_masjid")],
        [InlineKeyboardButton("✏️ Masjid tahrirlash", callback_data="admin_edit_masjid")],
        [InlineKeyboardButton("🗺️ Koordinatalar yangilash", callback_data="admin_update_coords")],
        [InlineKeyboardButton("🕐 Vaqtlar yangilash", callback_data="admin_update_times")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_push_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Push notification panel"""
    total_sent = sum(push_notification_stats.values())
    
    message = f"""📢 *PUSH NOTIFICATIONS*

📊 *Statistika:*
• Jami yuborilgan: *{total_sent}*
• Muvaffaqiyatli: *{push_notification_stats.get('success', 0)}*
• Xatoliklar: *{push_notification_stats.get('error', 0)}*

💡 *Funksiyalar:*"""
    
    keyboard = [
        [InlineKeyboardButton("🧪 Test notification", callback_data="admin_test_push")],
        [InlineKeyboardButton("📢 Ommaviy xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🎯 Targetli xabar", callback_data="admin_targeted_push")],
        [InlineKeyboardButton("📊 Push statistika", callback_data="admin_push_stats")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Umumiy statistika"""
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    today_stats = daily_stats[today]
    yesterday_stats = daily_stats[yesterday]
    
    # Top masjidlar
    top_masjids = sorted(masjid_popularity.items(), key=lambda x: x[1], reverse=True)[:3]
    
    message = f"""📈 *BOT STATISTIKA*

📅 *Bugun:*
• Jami harakatlar: *{today_stats['total_actions']}*
• Yangi foydalanuvchilar: *{today_stats['new_users']}*
• Start buyruqlari: *{today_stats.get('start', 0)}*
• Sozlamalar o'zgarishi: *{today_stats.get('settings', 0)}*

📅 *Kecha:*
• Jami harakatlar: *{yesterday_stats['total_actions']}*
• Yangi foydalanuvchilar: *{yesterday_stats['new_users']}*

🏆 *Top 3 mashhur masjidlar:*"""
    
    for i, (masjid_key, count) in enumerate(top_masjids, 1):
        name = MASJIDLAR_3_ALIFBO[masjid_key]['full_name']
        message += f"\n{i}. {name.replace('JOME MASJIDI', '').strip()}: *{count}*"
    
    keyboard = [
        [InlineKeyboardButton("📊 Haftalik hisobot", callback_data="admin_weekly_report")],
        [InlineKeyboardButton("📈 O'sish grafigi", callback_data="admin_growth_chart")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_manual_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual yangilanish"""
    message = """🔧 *MANUAL UPDATE*

Quyidagi operatsiyalarni bajarishingiz mumkin:"""
    
    keyboard = [
        [InlineKeyboardButton("🕐 Barcha vaqtlarni yangilash", callback_data="admin_update_all_times")],
        [InlineKeyboardButton("🕌 Bitta masjid vaqti", callback_data="admin_update_single_time")],
        [InlineKeyboardButton("🔄 Kanal qayta tekshirish", callback_data="admin_recheck_channel")],
        [InlineKeyboardButton("📊 Ma'lumotlar backup", callback_data="admin_backup_data")],
        [InlineKeyboardButton("♻️ Bot restart", callback_data="admin_restart_bot")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot sozlamalari"""
    monitoring_status = "🟢 Faol" if True else "🔴 Faol emas"  # monitoring holati
    
    message = f"""⚙️ *BOT SETTINGS*

🔧 *Hozirgi sozlamalar:*
• Kanal: *@{CHANNEL_USERNAME}*
• Monitoring: {monitoring_status}
• Test mode: *{'✅ Faol' if TEST_MODE else '❌ Faol emas'}*
• OCR: *{'✅ Faol' if OCR_AVAILABLE else '❌ Faol emas'}*
• Admin sessiyalar: *{len(admin_sessions)}*

🛠️ *Sozlamalar:*"""
    
    keyboard = [
        [InlineKeyboardButton("📺 Kanal o'zgartirish", callback_data="admin_change_channel")],
        [InlineKeyboardButton("🔄 Monitoring on/off", callback_data="admin_toggle_monitoring")],
        [InlineKeyboardButton("🧪 Test mode", callback_data="admin_toggle_test")],
        [InlineKeyboardButton("📋 System logs", callback_data="admin_system_logs")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ADMIN CALLBACK HANDLERS
# =======================

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin callback handler"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if not is_admin(user_id):
        return
    
    data = query.data
    
    if data == "admin_back":
        await query.edit_message_text(
            "🔐 *ADMIN PANEL*\n\nQaysi bo'limga kirmoqchisiz?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 User Analytics", callback_data="admin_user_analytics")],
                [InlineKeyboardButton("🕌 Masjid Management", callback_data="admin_masjid_mgmt")],
                [InlineKeyboardButton("📢 Push Notifications", callback_data="admin_push_panel")],
                [InlineKeyboardButton("📈 Statistics", callback_data="admin_statistics")]
            ])
        )
    
    elif data == "admin_test_push":
        await handle_test_push(update, context)
    elif data == "admin_broadcast":
        await handle_broadcast_setup(update, context)
    elif data == "admin_add_masjid":
        await handle_add_masjid_setup(update, context)
    elif data == "admin_update_all_times":
        await handle_update_all_times(update, context)
    # ... boshqa callback handlerlar

async def handle_test_push(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test push notification"""
    query = update.callback_query
    user_id = query.from_user.id
    
    test_message = """🧪 *TEST NOTIFICATION*

Bu test xabari. Agar buni ko'rayotgan bo'lsangiz, push notification tizimi ishlayapti! ✅

📅 Yuborilgan: """ + datetime.now().strftime("%d.%m.%Y %H:%M")
    
    try:
        await bot_app.bot.send_message(
            chat_id=user_id,
            text=test_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        push_notification_stats['test'] += 1
        
        await query.edit_message_text(
            "✅ Test notification muvaffaqiyatli yuborildi!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_push_panel")]
            ])
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ Xatolik: {e}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_push_panel")]
            ])
        )

async def handle_broadcast_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast setup"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    admin_temp_data[user_id] = {'action': 'broadcast_message'}
    
    await query.edit_message_text(
        """📢 *OMMAVIY XABAR YUBORISH*

Keyingi xabaringizni yozing. Bu xabar barcha foydalanuvchilarga yuboriladi.

⚠️ *Diqqat:* Xabar yuborilgandan keyin bekor qilib bo'lmaydi!

Bekor qilish uchun /cancel yozing.""",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_update_all_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha vaqtlarni yangilash"""
    query = update.callback_query
    
    # Hozirgi Qo'qon vaqti
    qoqon_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(qoqon_tz)
    
    # +5 daqiqa qo'shib test vaqtlari yaratish
    test_times = {
        "Bomdod": (now.replace(hour=5, minute=0) + timedelta(minutes=5)).strftime("%H:%M"),
        "Peshin": (now.replace(hour=12, minute=30) + timedelta(minutes=5)).strftime("%H:%M"),
        "Asr": (now.replace(hour=15, minute=45) + timedelta(minutes=5)).strftime("%H:%M"),
        "Shom": (now.replace(hour=18, minute=20) + timedelta(minutes=5)).strftime("%H:%M"),
        "Hufton": (now.replace(hour=20, minute=0) + timedelta(minutes=5)).strftime("%H:%M")
    }
    
    updated_count = 0
    for masjid_key in MASJIDLAR_3_ALIFBO.keys():
        if masjid_key in masjidlar_data:
            masjidlar_data[masjid_key].update(test_times)
            updated_count += 1
    
    # Barcha foydalanuvchilarga push notification yuborish
    notification_message = f"""🔄 *BARCHA MASJID VAQTLARI YANGILANDI*

Admin tomonidan barcha masjidlar vaqti yangilandi:

🌅 Bomdod: *{test_times['Bomdod']}*
☀️ Peshin: *{test_times['Peshin']}*
🌆 Asr: *{test_times['Asr']}*
🌇 Shom: *{test_times['Shom']}*
🌙 Hufton: *{test_times['Hufton']}*

📅 Yangilangan: {now.strftime("%d.%m.%Y %H:%M")}
👨‍💼 Admin tomonidan"""
    
    sent_count = 0
    for user_id in user_settings.keys():
        try:
            await bot_app.bot.send_message(
                chat_id=int(user_id),
                text=notification_message,
                parse_mode=ParseMode.MARKDOWN
            )
            sent_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logger.warning(f"❌ User {user_id}ga xabar yuborilmadi: {e}")
    
    push_notification_stats['admin_update'] += sent_count
    
    await query.edit_message_text(
        f"""✅ *YANGILANISH MUVAFFAQIYATLI*

• Yangilangan masjidlar: *{updated_count}*
• Xabar yuborilgan foydalanuvchilar: *{sent_count}*

🕐 Yangi vaqtlar:
{chr(10).join([f"• {prayer}: {time}" for prayer, time in test_times.items()])}""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
        ])
    )
