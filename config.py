"""
BOTNI SOZLASH — shu faylni o'zingizga moslab tahrirlang.
"""
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "QO'YING_SHU_YERGA_TOKENINGIZNI")

ADMIN_ID = 8104665298
PARTNER_ID = 8326732787

USERS = {
    ADMIN_ID: "Abdulboriy",
    PARTNER_ID: "Mohinur",
}
ALLOWED_IDS = set(USERS.keys())

# ── SALOM / TONGGI UYG'OTISH ─────────────────────────────────────
GREETING_TEXT = (
    "[Ассаламу алайкум ва раҳматуллоҳи ва барокатуҳ]\n\n"
    "*Bismillahir-Rohmanir-Rohiym*"
)
WAKE_MOTIVATION = (
    "🌅 Bomdod namozi vaqti yaqinlashdi — turing, tahorat qiling va namozga tayyorlaning.\n\n"
    "_Kun g'alabasi tongdan boshlanadi. Bugun ham Allohga birinchi bo'lib Siz yetib boring!_"
)
WAKE_BEFORE_FAJR_MINUTES = 20

# ── KUNLIK VAZIFALAR (standart ro'yxat, har kuni avtomatik yuboriladi) ──
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

# ── ERTALABKI MAQSAD SO'ROVI / KECHKI HISOBOT SO'ROVI ────────────
MORNING_GOAL_HOUR = 6
MORNING_GOAL_MINUTE = 30

EVENING_REPORT_HOUR = 23
EVENING_REPORT_MINUTE = 15

# ── ZIKRLAR (namozdan keyingi tez tugmalar) ───────────────────────
DHIKRS = [
    ("Subhanalloh", 33),
    ("Alhamdulillah", 33),
    ("Allohu akbar", 33),
    ("Astag'firulloh va atubu ilayh", 33),
    ("Allohumma salli 'ala Sayyidina Muhammad", 33),
]

DEFAULT_DHIKR_COUNT = 33  # "Zikr/Salovat qo'shish"da son yozilmasa shu ishlatiladi