# Namoz & Kunlik reja boti

Faqat 2 kishi uchun (Abdulboriy + Mohinur). To'liq menyuli bot: Namoz, Zikr, Salovat,
Maqsad, Vazifa, Statistika. Ombor — Neon (Postgres), har bir tur alohida jadvalda saqlanadi.

## Loyiha tuzilishi
```
namoz_bot/
├── bot.py             # asosiy bot — menyu, handlerlar, scheduler
├── config.py           # ID'lar, ismlar, vazifalar, vaqtlar — shu yerda sozlanadi
├── storage.py           # Postgres (Neon) bilan ishlash funksiyalari
├── prayer_times.py      # Toshkent uchun namoz vaqtlarini hisoblash
└── requirements.txt
```

## DB jadvallar (Neon'da avtomatik yaratiladi)
| Jadval | Nima saqlaydi |
|---|---|
| `prayer_log` | har kunlik 5 namoz holati (done/qazo/missed) + zikr belgisi |
| `dhikr_log` | erkin qo'shilgan zikrlar, kunlik jamlanma |
| `salovat_log` | erkin qo'shilgan salovatlar, kunlik jamlanma |
| `goals` | ertalabki/erkin yozilgan kunlik maqsadlar |
| `task_log` | standart + qo'lda qo'shilgan vazifalar, holati |
| `reports` | kechki erkin hisobot matnlari |

## Bot funksiyalari
- `/start` — salom (Islomiy ibora + Bismillah) va asosiy menyu (pastki tugmalar) chiqadi:
  **🕌 Namoz · 📿 Zikr · 🤲 Salovat · 🎯 Maqsad · 📋 Vazifa · 📊 Statistika**
- **Namoz** — bugungi 5 namozning vaqti va holatini ko'rsatadi
- **Zikr / Salovat** — bugun qo'shilganlarni ko'rsatadi + "➕ qo'shish" tugmasi.
  Bosilgach, erkin matn yuboriladi: `Subhanalloh 33` yoki faqat `Subhanalloh` (son
  yozilmasa standart 33 olinadi) — darhol kunlik jamlanmaga qo'shiladi
- **Maqsad** — bugungi yozilgan maqsadlarni ko'rsatadi + qo'shish
- **Vazifa** — bugungi vazifalar va holati (✅/❌/⬜️) + qo'shish; qo'shilgan vazifaga
  darhol Qildim/Qilmadim/Keyin tugmasi biriktiriladi
- **Statistika** — so'nggi 7 kunlik umumiy hisobot (ikkovingiz uchun ham)
- Har namoz vaqtida avtomatik eslatma (O'qidim/Qazo/Keyin eslat tugmalari bilan)
- Har kuni Bomdoddan oldin — Islomiy salom + uyg'otish xabari
- Har ertalab (standart 06:30) — "Bugungi maqsadingiz nima?" so'rovi
- Har kuni kechqurun (standart 23:15) — kechki hisobot so'rovi
- Har yakshanba 22:00 da admin'ga avtomatik haftalik hisobot, `/stats` orqali ham
  xohlagan vaqt so'rab olish mumkin (faqat admin)
- Faqat `config.py`dagi 2 ta ID bilan ishlaydi — boshqa hech kimga javob bermaydi

## Kerakli muhit o'zgaruvchilari
```bash
export BOT_TOKEN="BotFather'dan olingan token"
export DATABASE_URL="postgresql://user:parol@ep-xxxx.neon.tech/dbname?sslmode=require"
```
`DATABASE_URL`ni Neon konsolidan "Connection string" bo'limidan oling (pooled/pgbouncer
variantini tanlang — ko'proq ulanishga chidamli).

## O'rnatish va lokal sinov
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## GitHub'ga yuklash
```bash
cd namoz_bot
git init
echo "venv/
__pycache__/
*.pyc
.env" > .gitignore
git add .
git commit -m "Namoz bot: menyu, zikr/salovat/maqsad/vazifa, Neon DB"
git branch -M main
git remote add origin <GITHUB_REPO_URL>
git push -u origin main
```
**Muhim:** `BOT_TOKEN` va `DATABASE_URL`ni hech qachon kodga yozmang va GitHub'ga
yuklamang — ular faqat muhit o'zgaruvchisi (yoki serveringizdagi `.env`, `.gitignore`ga
qo'shilgan holda) orqali beriladi.

## Serverga yangilanish qo'yish (sizning serveringizda)
```bash
cd /path/to/namoz_bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt   # yangi kutubxona qo'shilgan bo'lsa
# botni qayta ishga tushiring (systemd/screen/pm2 — qanday ishlatayotganingizga qarab)
```
Agar `systemd` orqali fon jarayon sifatida ishlatayotgan bo'lsangiz:
```bash
sudo systemctl restart namoz-bot.service
```

## Kun hisobi
Yarim tundan keyin, lekin ertangi Bomdoddan oldin qazo namozni belgilasangiz — bot buni
avtomatik **kechagi kunga** yozadi (`logical_date()` funksiyasi).

## Qo'shimcha g'oyalar
- Streak (ketma-ket kunlar) hisoblagichi
- Juma kuni Kahf surasi eslatmasi
- Ramazon rejimi — Saharlik/Iftor va ro'za nazorati
- Kitob o'qish nazorati — kunlik sahifa hisoblagichi
- Ikkovingiz bir-biringizning haftalik natijangizni ko'ra oladigan umumiy buyruq