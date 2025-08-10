#!/usr/bin/env python3
"""
Test Helper Script - kanal monitoring funksiyalarini test qilish uchun
"""

import os
import re
from typing import Dict, List, Optional
from difflib import SequenceMatcher

# Test masjidlar ma'lumotlari
TEST_MASJIDLAR = {
    "NORBUTABEK": {
        "full_name": "NORBUTABEK JOME MASJIDI",
        "patterns": {
            "latin": ["norbutabek", "norbu tabek", "norbu-tabek"],
            "cyrillic": ["норбутабек", "норбу табек"],
            "arabic": ["نوربوتابيك"]
        }
    },
    "GISHTLIK": {
        "full_name": "GISHTLIK JOME MASJIDI",
        "patterns": {
            "latin": ["gishtlik", "g'ishtlik", "gʻishtlik"],
            "cyrillic": ["гиштлик", "ғиштлик"],
            "arabic": ["غیشتلیك"]
        }
    }
}

# Test namaz vaqtlari pattern
TEST_PRAYER_PATTERNS = {
    "latin": {
        "bomdod": r'(?:bomdod|fajr|subh|sahar)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "peshin": r'(?:peshin|zuhr|zuhur|öyle)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "asr": r'(?:asr|ikindi|digar)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "shom": r'(?:shom|maghrib|mag\'rib|axshom)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "hufton": r'(?:hufton|isha|xufton|kech)\s*[:]\s*(\d{1,2}[:]\d{2})'
    },
    "cyrillic": {
        "bomdod": r'(?:бомдод|фажр|субх|сахар)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "peshin": r'(?:пешин|зухр|зухур|ойле)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "asr": r'(?:аср|икинди|дигар)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "shom": r'(?:шом|магриб|ағриб|ахшом)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "hufton": r'(?:хуфтон|иша|хуфтон|кеч)\s*[:]\s*(\d{1,2}[:]\d{2})'
    },
    "arabic": {
        "bomdod": r'(?:فجر|صبح|سحر)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "peshin": r'(?:ظهر|زهر)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "asr": r'(?:عصر|عشر)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "shom": r'(?:مغرب|مغریب)\s*[:]\s*(\d{1,2}[:]\d{2})',
        "hufton": r'(?:عشاء|عشا|عیشا)\s*[:]\s*(\d{1,2}[:]\d{2})'
    }
}

def similarity(a, b):
    """String similarity checker"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_mosque_in_text(text: str, threshold: float = 0.7) -> Optional[str]:
    """Masjid nomini matndan topish - 3 alifbo"""
    text = text.lower().strip()
    best_match = None
    best_score = 0
    
    print(f"🔍 Masjid qidirilmoqda: '{text}'")
    
    for mosque_key, mosque_data in TEST_MASJIDLAR.items():
        for script_type, patterns in mosque_data["patterns"].items():
            for pattern in patterns:
                score = similarity(text, pattern)
                print(f"  📊 {mosque_key} ({script_type}): '{pattern}' - {score:.2f}")
                
                if score > threshold and score > best_score:
                    best_score = score
                    best_match = mosque_key
                    
                # Pattern bo'yicha ham tekshirish
                if pattern in text:
                    print(f"  ✅ To'g'ridan-to'g'ri mos keldi: {mosque_key}")
                    return mosque_key
    
    if best_match:
        print(f"  🎯 Eng yaxshi mos kelishi: {best_match} ({best_score:.2f})")
    else:
        print(f"  ❌ Masjid topilmadi (threshold: {threshold})")
    
    return best_match

def extract_prayer_times(text: str) -> Dict[str, str]:
    """Namaz vaqtlarini matndan ajratib olish"""
    prayer_times = {}
    text = text.lower()
    
    print(f"🕐 Namaz vaqtlari qidirilmoqda...")
    
    # Har 3 alifbo uchun pattern check
    for script_type, patterns in TEST_PRAYER_PATTERNS.items():
        print(f"  📝 {script_type.upper()} alifbosida qidirilmoqda...")
        
        for prayer_name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Capitalize qilish
                prayer_key = prayer_name.capitalize()
                prayer_times[prayer_key] = matches[0]
                print(f"    ✅ {prayer_key}: {matches[0]}")
    
    if not prayer_times:
        print("  ❌ Namaz vaqtlari topilmadi")
    
    return prayer_times

def test_text_samples():
    """Test matnlarni tekshirish"""
    
    test_samples = [
        {
            "name": "Lotin alifbosi",
            "text": """NORBUTABEK JOME MASJIDI
Bomdod: 05:00
Peshin: 12:30
Asr: 15:45
Shom: 18:15
Hufton: 20:00"""
        },
        {
            "name": "Kiril alifbosi", 
            "text": """ГИШТЛИК ЖОМЕ МАСЖИДИ
Бомдод: 05:05
Пешин: 12:35
Аср: 15:50
Шом: 18:20
Хуфтон: 20:05"""
        },
        {
            "name": "Arab alifbosi",
            "text": """مسجد نوربوتابيك
فجر: 05:10
ظهر: 12:40
عصر: 15:55
مغرب: 18:25
عشاء: 20:10"""
        },
        {
            "name": "Noto'g'ri yozilgan",
            "text": """norbu tabek masjid
bomdod: 05:15
peshin: 12:45"""
        },
        {
            "name": "Aralash matn",
            "text": """📍 GISHTLIK маsjidi ning bugungi vaqtlari:
🌅 Fajr: 05:20
☀️ Peshin: 12:50
🌆 Asr: 16:00"""
        }
    ]
    
    print("=" * 60)
    print("🧪 TEST NAMUNALARINI TEKSHIRISH")
    print("=" * 60)
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n📋 TEST {i}: {sample['name']}")
        print("-" * 40)
        print(f"Matn:\n{sample['text']}\n")
        
        # Masjid nomini topish
        lines = sample['text'].split('\n')
        mosque_found = None
        
        for line in lines:
            if any(word in line.lower() for word in ['masjid', 'масжид', 'мسجد']):
                mosque_found = find_mosque_in_text(line)
                break
        
        # Namaz vaqtlarini topish
        prayer_times = extract_prayer_times(sample['text'])
        
        # Natija
        print("\n📊 NATIJA:")
        if mosque_found:
            print(f"  🕌 Masjid: {TEST_MASJIDLAR[mosque_found]['full_name']}")
        else:
            print("  ❌ Masjid topilmadi")
            
        if prayer_times:
            print("  🕐 Vaqtlar:")
            for prayer, time in prayer_times.items():
                print(f"    {prayer}: {time}")
        else:
            print("  ❌ Vaqtlar topilmadi")
        
        print("\n" + "="*60)

def test_similarity_threshold():
    """Similarity threshold'ni test qilish"""
    
    print("\n🎯 SIMILARITY THRESHOLD TESTI")
    print("-" * 40)
    
    test_cases = [
        ("norbutabek", "norbu tabek"),
        ("gishtlik", "g'ishtlik"), 
        ("norbutabek", "norbutabek jome masjidi"),
        ("гиштлик", "gishtlik"),
        ("random text", "norbutabek"),
        ("shayxulislom", "shayx ul islom")
    ]
    
    for text1, text2 in test_cases:
        score = similarity(text1, text2)
        status = "✅ MATCH" if score > 0.7 else "❌ NO MATCH"
        print(f"  '{text1}' vs '{text2}': {score:.2f} {status}")

def interactive_test():
    """Interaktiv test rejimi"""
    
    print("\n🎮 INTERAKTIV TEST REJIMI")
    print("-" * 40)
    print("Matn kiriting (chiqish uchun 'exit'):")
    
    while True:
        user_input = input("\n> ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'chiqish']:
            break
            
        if not user_input:
            continue
            
        print(f"\n📥 Tahlil qilinmoqda: '{user_input}'")
        
        # Masjid topish
        mosque = find_mosque_in_text(user_input)
        
        # Vaqt topish  
        times = extract_prayer_times(user_input)
        
        print("\n📊 NATIJA:")
        if mosque:
            print(f"  🕌 Masjid: {TEST_MASJIDLAR[mosque]['full_name']}")
        if times:
            print("  🕐 Vaqtlar:")
            for prayer, time in times.items():
                print(f"    {prayer}: {time}")
        
        if not mosque and not times:
            print("  ❌ Hech narsa topilmadi")

def main():
    """Asosiy test funksiya"""
    
    print("🧪 NAMAZ VAQTI BOT - TEST HELPER")
    print("=" * 60)
    
    # Env check
    if os.path.exists('.env'):
        print("✅ .env fayl mavjud")
    else:
        print("⚠️ .env fayl topilmadi")
    
    print("\nQuyidagi testlardan birini tanlang:")
    print("1. Avtomatik test namunalari")
    print("2. Similarity threshold test")
    print("3. Interaktiv test rejimi")
    print("4. Barcha testlar")
    
    choice = input("\nTanlang (1-4): ").strip()
    
    if choice == "1":
        test_text_samples()
    elif choice == "2":
        test_similarity_threshold()
    elif choice == "3":
        interactive_test()
    elif choice == "4":
        test_text_samples()
        test_similarity_threshold()
        interactive_test()
    else:
        print("❌ Noto'g'ri tanlov")

if __name__ == "__main__":
    main()
