# Namoz & Kunlik reja boti

Faqat 2 kishi uchun (Abdulboriy + Mohinur): 5 vaqt namoz eslatmasi, tonggi uyg'otish salovati,
5 ta zikr (kunlik jamlanma bilan), kunlik vazifalar va haftalik statistika. Omborga — Neon (Postgres).

## Kerakli muhit o'zgaruvchilari
```bash
export BOT_TOKEN="BotFather'dan olingan token"
export DATABASE_URL="postgresql://user:parol@ep-xxxx.neon.tech/dbname?sslmode=require"
```
`DATABASE_URL` — Neon konsolidan "Connection string" bo'limidan olinadi (pgbouncer yoqilgan "pooled"
variantini oling, ko'proq ulanishga chidamli bo'ladi).

## O'rnatish va ishga tushirish
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```
Birinchi ishga tushishda kerakli jadvallar (`prayer_log`, `task_log`, `dhikr_log`) Neon'da
avtomatik yaratiladi — qo'lda SQL yozish shart emas.

## Kirish cheklovi
Bot faqat `config.py`dagi `ADMIN_ID` va `PARTNER_ID`ga javob beradi. Boshqa har qanday
Telegram foydalanuvchisidan kelgan `/start`, tugma bosish yoki xabarga bot umuman
javob qaytarmaydi (xatolik ham chiqmaydi — jim o'tkazib yuboradi).

## Kun hisobi (muhim nuqta)
Agar kech qolgan (masalan Xufton) namozni yarim tundan keyin, lekin ertangi Bomdoddan oldin
o'qisangiz/belgilasangiz — bot buni "kecha"gi kunga yozadi, yangi bo'sh kun ochib yubormaydi.
Bu `logical_date()` funksiyasi orqali avtomatik hal qilinadi.

## Qanday ishlaydi
- `/start` — Islomiy salom (`Ассаламу алайкум...` havolasi) + Bismillah bilan javob beradi
- Har kuni Bomdoddan `WAKE_BEFORE_FAJR_MINUTES` (standart 20) daqiqa oldin — xuddi shu salom +
  motivatsion uyg'otish xabari ikkalangizga ham avtomatik boradi
- Har namoz vaqti kirganda: ✅ O'qidim / ⏳ Qazo qilaman / 🔕 Hozir yo'q
- "O'qidim" bosilsa — 5 ta zikr tugmasi chiqadi, bosilgan zikrning soni (masalan 33) o'sha kunning
  jamlanmasiga qo'shilib boriladi (bir kunda bir nechta namozdan keyin bossangiz — yig'ilib boradi)
- "Hozir yo'q" — necha daqiqadan keyin eslatishni so'raydi, keyin o'sha vaqtda qayta yuboradi
- Har ertalab kunlik vazifalar — har biriga Qildim/Qilmadim/Keyin tugmasi
- `/stats` — faqat admin uchun, so'nggi 7 kunlik hisobot (namoz, vazifa, zikr jamlanmalari)
- Har yakshanba soat 22:00 da admin'ga avtomatik haftalik hisobot

## Qo'shimcha g'oyalar (xohlasangiz keyin qo'shib beraman)
- Streak (ketma-ket kunlar) — "7 kun ketma-ket to'liq namoz" kabi rag'bat xabarlari
- Juma kuni Kahf surasi eslatmasi
- Ramazon rejimi — Saharlik/Iftor vaqtlari va ro'za nazorati
- Kitob o'qish nazorati — har kuni "nechta bet o'qidingiz" deb so'rab, oylik jamlanma
- Ikkovingiz bir-biringizning haftalik natijangizni ko'ra oladigan umumiy `/bizniknatija` buyrug'i