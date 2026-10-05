"""
BOTNI SOZLASH — ma'lumotlarni muhit o'zgaruvchilari orqali kiriting.
"""
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Siz — admin, haftalik statistika shunga yuboriladi
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)

# Juftingizning Telegram ID'si
PARTNER_ID = int(os.environ.get("PARTNER_ID", "0") or 0)

USERS = {
    ADMIN_ID: "Abdulboriy",
    PARTNER_ID: "Mohinur",
}

# Faqat shu ikkovi bilan ishlaydi — boshqa hech kimga javob bermaydi
ALLOWED_IDS = set(USERS.keys())

# ── SALOM / TONGGI UYG'OTISH ─────────────────────────────────────
GREETING_TEXT = (
    "[Ассаламу алайкум ва раҳматуллоҳи ва барокатуҳ](https://muslimaat.uz/maqola/847)\n\n"
    "*Bismillahir-Rohmanir-Rohiym*"
)

WAKE_MOTIVATION = (
    "🌅 Bomdod namozi vaqti yaqinlashdi — turing, tahorat qiling va namozga tayyorlaning.\n\n"
    "_Kun g'alabasi tongdan boshlanadi. Bugun ham Allohga birinchi bo'lib Siz yetib boring!_"
)

MORNING_PROMPT = "Bugun uchun maqsadingiz nima? Biror maqsad yozing."
EVENING_PROMPT = "Bugun qildingizmi? Zikr, salovat, vazifa va maqsadlaringizni qisqacha yozib bering."

# Bomdoddan necha daqiqa oldin uyg'otish xabari yuborilsin
WAKE_BEFORE_FAJR_MINUTES = 20

# ── KUNLIK VAZIFALAR ──────────────────────────────────────────────
DAILY_TASKS_HOUR = 6
DAILY_TASKS_MINUTE = 0

DAILY_TASKS = {
    ADMIN_ID: [
        "Sun'iy intellekt (AI) — kunlik mavzu",
        "Ingliz tili — grammatika darsi",
        "Kiberxavfsizlik / boshqa reja",
    ],
    PARTNER_ID: [
        "Suhbat kitobi — 1 ta mavzu",
        "Zoom/speaking — 1 ta mavzu",
        "Ona tili yoki arab tili kursi vazifasi",
        "Qur'on hatm — kuniga 4 bet",
        "Voqea surasi",
        "Mulk surasi",
    ],
}

# ── ZIKRLAR ────────────────────────────────────────────────────────
# Har namozdan keyin: (nomi, bir martalik soni)
# Tugma bosilganda shu "son" kunlik jamlanmaga qo'shib boriladi.
DHIKRS = [
    ("Subhanalloh", 33),
    ("Alhamdulillah", 33),
    ("Allohu akbar", 33),
    ("Astag'firulloh va atubu ilayh", 33),
    ("Allohumma salli 'ala Sayyidina Muhammad", 33),
]

DEFAULT_GOALS = {
    ADMIN_ID: [
        "Qur'on o'qish",
        "Ishga vaqt ajratish",
        "Maqsadga erishish",
    ],
    PARTNER_ID: [
        "Kitob o'qish",
        "Yaxshi reja tuzish",
        "Kun yakuni hisobotini yozish",
    ],
}

MAIN_MENU = [
    ["🕌 Namoz", "🙏 Zikr"],
    ["🌙 Salovat", "🎯 Maqsad"],
    ["✅ Vazifa", "📊 Statistika"],
]