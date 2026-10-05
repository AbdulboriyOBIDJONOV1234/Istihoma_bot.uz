"""
Namoz & Kunlik reja boti — faqat 2 kishi uchun (Abdulboriy + Mohinur).

Ishga tushirish:
  1) pip install -r requirements.txt
  2) Muhit o'zgaruvchilari: BOT_TOKEN, DATABASE_URL (Neon)
  3) config.py'da ism/vazifalarni tekshiring
  4) python bot.py
"""
import logging
from datetime import datetime, timedelta, date, time as dtime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

import config
import storage
from prayer_times import get_prayer_times, PRAYER_LABELS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ALLOWED_FILTER = filters.User(user_id=list(config.ALLOWED_IDS))

# user_id -> "kind" — keyingi oddiy matn xabari shu maqsadda ishlatiladi
# kind: 'zikr_add' | 'salovat_add' | 'maqsad_add' | 'vazifa_add' | 'report_add'
#       | ('snooze_prayer', prayer_name) | ('snooze_task', task_text)
AWAITING = {}

MENU_NAMOZ = "🕌 Namoz"
MENU_ZIKR = "📿 Zikr"
MENU_SALOVAT = "🤲 Salovat"
MENU_MAQSAD = "🎯 Maqsad"
MENU_VAZIFA = "📋 Vazifa"
MENU_STATS = "📊 Statistika"

MAIN_MENU = ReplyKeyboardMarkup(
    [[KeyboardButton(MENU_NAMOZ), KeyboardButton(MENU_ZIKR)],
     [KeyboardButton(MENU_SALOVAT), KeyboardButton(MENU_MAQSAD)],
     [KeyboardButton(MENU_VAZIFA), KeyboardButton(MENU_STATS)]],
    resize_keyboard=True,
)


def logical_date(dt: datetime) -> date:
    """Yarim tundan keyin, lekin bugungi Bomdoddan oldingi vaqt — o'tgan kunga tegishli."""
    today_times = get_prayer_times(dt.date())
    if dt.time() < today_times["fajr"].time():
        return dt.date() - timedelta(days=1)
    return dt.date()

def parse_name_count(text: str, default: int):
    """'Subhanalloh 33' -> ('Subhanalloh', 33). 'Subhanalloh' -> ('Subhanalloh', default)."""
    parts = text.strip().rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0].strip(), int(parts[1])
    return text.strip(), default


# ───────────────────────── /start, SALOM, UYG'OTISH ─────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        config.GREETING_TEXT, parse_mode="Markdown", disable_web_page_preview=True,
        reply_markup=MAIN_MENU,
    )

async def send_wake_message(context: ContextTypes.DEFAULT_TYPE):
    text = config.GREETING_TEXT + "\n\n" + config.WAKE_MOTIVATION
    for user_id in config.USERS:
        try:
            await context.bot.send_message(user_id, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            log.warning(f"Uyg'otish xabari yuborilmadi {user_id}: {e}")


# ───────────────────────── NAMOZ ─────────────────────────

def prayer_keyboard(prayer_name: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ O'qidim", callback_data=f"pray:done:{prayer_name}"),
         InlineKeyboardButton("⏳ Qazo qilaman", callback_data=f"pray:qazo:{prayer_name}")],
        [InlineKeyboardButton("🔕 Hozir yo'q, keyin eslat", callback_data=f"pray:snooze:{prayer_name}")],
    ])

async def send_prayer_reminder(context: ContextTypes.DEFAULT_TYPE):
    prayer_name = context.job.data["prayer_name"]
    label = PRAYER_LABELS[prayer_name]
    for user_id in config.USERS:
        try:
            await context.bot.send_message(
                user_id, f"🕌 *{label}* namozi vaqti bo'ldi.",
                parse_mode="Markdown", reply_markup=prayer_keyboard(prayer_name),
            )
        except Exception as e:
            log.warning(f"Yuborib bo'lmadi {user_id}: {e}")

def dhikr_keyboard(prayer_name: str):
    rows = [[InlineKeyboardButton(f"{name} — {count}x ✅", callback_data=f"dhikr:{prayer_name}:{i}")]
            for i, (name, count) in enumerate(config.DHIKRS)]
    return InlineKeyboardMarkup(rows)

async def handle_prayer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in config.ALLOWED_IDS:
        return
    await query.answer()
    _, action, prayer_name = query.data.split(":")
    today = logical_date(datetime.now())
    label = PRAYER_LABELS[prayer_name]

    if action == "done":
        storage.set_prayer_status(user_id, today, prayer_name, "done")
        await query.edit_message_text(f"✅ {label} namozi — o'qildi. Zikrlarni ham belgilang:",
                                       reply_markup=dhikr_keyboard(prayer_name))
    elif action == "qazo":
        storage.set_prayer_status(user_id, today, prayer_name, "qazo")
        await query.edit_message_text(f"⏳ {label} namozi qazo sifatida belgilandi.")
    elif action == "snooze":
        AWAITING[user_id] = ("snooze_prayer", prayer_name)
        await query.edit_message_text(f"🔕 {label} uchun necha daqiqadan keyin eslataymi? (son yozing)")

async def handle_dhikr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in config.ALLOWED_IDS:
        return
    await query.answer("Belgilandi ✅")
    _, prayer_name, idx = query.data.split(":")
    dhikr_name, dhikr_count = config.DHIKRS[int(idx)]
    today = logical_date(datetime.now())
    storage.set_dhikr_done_flag(user_id, today, prayer_name)
    storage.add_dhikr_count(user_id, today, dhikr_name, dhikr_count)
    await query.edit_message_text(f"🤲 {PRAYER_LABELS[prayer_name]}dan keyin \"{dhikr_name}\" — {dhikr_count}x qabul bo'lsin!")

async def send_single_prayer_reminder(context: ContextTypes.DEFAULT_TYPE):
    d = context.job.data
    label = PRAYER_LABELS[d["prayer_name"]]
    await context.bot.send_message(d["user_id"], f"🕌 Eslatma: *{label}* namozini o'qidingizmi?",
                                    parse_mode="Markdown", reply_markup=prayer_keyboard(d["prayer_name"]))


# ───────────────────────── MENYU: NAMOZ ─────────────────────────

async def menu_namoz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = logical_date(datetime.now())
    times = get_prayer_times(date.today())
    statuses = storage.get_today_prayers(user_id, today)
    status_icon = {"done": "✅", "qazo": "⏳", "missed": "❌"}

    lines = ["🕌 *Bugungi namozlar:*\n"]
    for name, label in PRAYER_LABELS.items():
        t = times[name].strftime("%H:%M")
        st = statuses.get(name)
        icon = status_icon.get(st, "⬜️")
        lines.append(f"{icon} {label} — {t}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ───────────────────────── MENYU: ZIKR / SALOVAT ─────────────────────────

def add_inline(kind_label: str, callback: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"➕ {kind_label} qo'shish", callback_data=callback)]])

async def menu_zikr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = logical_date(datetime.now())
    rows = storage.get_today_dhikrs(user_id, today)
    text = "📿 *Bugungi zikrlaringiz:*\n\n"
    text += "\n".join(f"• {name} — {cnt}x" for name, cnt in rows) if rows else "Hali hech narsa qo'shilmagan."
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=add_inline("Zikr", "addmenu:zikr"))

async def menu_salovat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = logical_date(datetime.now())
    rows = storage.get_today_salovats(user_id, today)
    text = "🤲 *Bugungi salovatlaringiz:*\n\n"
    text += "\n".join(f"• {name} — {cnt}x" for name, cnt in rows) if rows else "Hali hech narsa qo'shilmagan."
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=add_inline("Salovat", "addmenu:salovat"))

async def menu_maqsad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = logical_date(datetime.now())
    goals = storage.get_today_goals(user_id, today)
    text = "🎯 *Bugungi maqsadlaringiz:*\n\n"
    text += "\n".join(f"• {g}" for g in goals) if goals else "Hali maqsad qo'shilmagan."
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=add_inline("Maqsad", "addmenu:maqsad"))

async def menu_vazifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = logical_date(datetime.now())
    tasks = storage.get_today_tasks(user_id, today)
    icon = {"done": "✅", "not_done": "❌", "pending": "⬜️"}
    text = "📋 *Bugungi vazifalaringiz:*\n\n"
    text += "\n".join(f"{icon.get(s,'⬜️')} {t}" for t, s in tasks) if tasks else "Hali vazifa qo'shilmagan."
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=add_inline("Vazifa", "addmenu:vazifa"))

async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    end = date.today()
    start = end - timedelta(days=6)
    await update.message.reply_text(format_report(start, end), parse_mode="Markdown")


async def handle_addmenu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in config.ALLOWED_IDS:
        return
    await query.answer()
    kind = query.data.split(":")[1]
    prompts = {
        "zikr": "📿 Zikr nomini yozing. Xohlasangiz songini ham qo'shing.\nMasalan: `Subhanalloh 33` yoki faqat `Subhanalloh`",
        "salovat": "🤲 Salovat nomini yozing. Xohlasangiz songini ham qo'shing.\nMasalan: `Allohumma salli 'ala Muhammad 100`",
        "maqsad": "🎯 Bugungi maqsadingizni yozing.",
        "vazifa": "📋 Qo'shmoqchi bo'lgan vazifangizni yozing.",
    }
    AWAITING[user_id] = f"{kind}_add"
    await query.edit_message_text(prompts[kind], parse_mode="Markdown")


# ───────────────────────── KUNLIK VAZIFALAR (standart ro'yxat) ─────────────────────────

def task_keyboard(task_text: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Qildim", callback_data=f"task:done"),
        InlineKeyboardButton("❌ Qilmadim", callback_data=f"task:not_done"),
        InlineKeyboardButton("🔕 Keyin", callback_data=f"task:snooze"),
    ]])

async def send_daily_tasks(context: ContextTypes.DEFAULT_TYPE):
    today = logical_date(datetime.now())
    for user_id, tasks in config.DAILY_TASKS.items():
        if not tasks:
            continue
        await context.bot.send_message(user_id, "📋 Bugungi standart rejalaringiz:")
        for task_text in tasks:
            storage.add_task(user_id, today, task_text)
            await context.bot.send_message(user_id, task_text, reply_markup=task_keyboard(task_text))

async def handle_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in config.ALLOWED_IDS:
        return
    await query.answer()
    action = query.data.split(":")[1]
    today = logical_date(datetime.now())
    task_text = query.message.text

    if action == "done":
        storage.set_task_status(user_id, today, task_text, "done")
        await query.edit_message_text(f"✅ {task_text}")
    elif action == "not_done":
        storage.set_task_status(user_id, today, task_text, "not_done")
        await query.edit_message_text(f"❌ {task_text}")
    elif action == "snooze":
        AWAITING[user_id] = ("snooze_task", task_text)
        await query.edit_message_text(f"🔕 \"{task_text}\" — necha daqiqadan keyin eslataymi? Son yozing.")

async def send_task_reminder(context: ContextTypes.DEFAULT_TYPE):
    d = context.job.data
    await context.bot.send_message(d["user_id"], f"📋 Eslatma: {d['task_text']}", reply_markup=task_keyboard(d["task_text"]))


# ───────────────────────── ERTALABKI MAQSAD / KECHKI HISOBOT SO'ROVI ─────────────────────────

async def morning_goal_request(context: ContextTypes.DEFAULT_TYPE):
    for user_id in config.USERS:
        AWAITING[user_id] = "maqsad_add"
        try:
            await context.bot.send_message(user_id, "🎯 Hayrli tong! Bugungi maqsadingiz nima? Yozib yuboring.")
        except Exception as e:
            log.warning(f"Maqsad so'rovi yuborilmadi {user_id}: {e}")

async def evening_report_request(context: ContextTypes.DEFAULT_TYPE):
    for user_id in config.USERS:
        AWAITING[user_id] = "report_add"
        try:
            await context.bot.send_message(
                user_id,
                "📊 Kechki hisobot vaqti. Bugungi maqsad va vazifalaringizga qanchalik erishdingiz? "
                "Qisqacha yozib bering."
            )
        except Exception as e:
            log.warning(f"Hisobot so'rovi yuborilmadi {user_id}: {e}")


# ───────────────────────── ODDIY MATN XABARLARNI YO'NALTIRISH ─────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Menyu tugmalari
    if text == MENU_NAMOZ:
        return await menu_namoz(update, context)
    if text == MENU_ZIKR:
        return await menu_zikr(update, context)
    if text == MENU_SALOVAT:
        return await menu_salovat(update, context)
    if text == MENU_MAQSAD:
        return await menu_maqsad(update, context)
    if text == MENU_VAZIFA:
        return await menu_vazifa(update, context)
    if text == MENU_STATS:
        return await menu_stats(update, context)

    awaiting = AWAITING.get(user_id)
    if not awaiting:
        return  # kutilmagan oddiy xabar — e'tiborsiz qoldiramiz

    today = logical_date(datetime.now())

    if awaiting == "zikr_add":
        name, count = parse_name_count(text, config.DEFAULT_DHIKR_COUNT)
        storage.add_dhikr_count(user_id, today, name, count)
        AWAITING.pop(user_id, None)
        await update.message.reply_text(f"✅ \"{name}\" — {count}x qo'shildi.", reply_markup=MAIN_MENU)

    elif awaiting == "salovat_add":
        name, count = parse_name_count(text, config.DEFAULT_DHIKR_COUNT)
        storage.add_salovat_count(user_id, today, name, count)
        AWAITING.pop(user_id, None)
        await update.message.reply_text(f"✅ \"{name}\" — {count}x qo'shildi.", reply_markup=MAIN_MENU)

    elif awaiting == "maqsad_add":
        storage.add_goal(user_id, today, text)
        AWAITING.pop(user_id, None)
        await update.message.reply_text("✅ Maqsad saqlandi. Omad!", reply_markup=MAIN_MENU)

    elif awaiting == "vazifa_add":
        storage.add_task(user_id, today, text)
        AWAITING.pop(user_id, None)
        await update.message.reply_text(f"✅ Vazifa qo'shildi: {text}", reply_markup=task_keyboard(text))

    elif awaiting == "report_add":
        storage.add_report(user_id, today, text)
        AWAITING.pop(user_id, None)
        await update.message.reply_text("✅ Hisobot saqlandi. Ertaga yangi kun, davom eting!", reply_markup=MAIN_MENU)

    elif isinstance(awaiting, tuple) and awaiting[0] == "snooze_prayer":
        if not text.isdigit():
            await update.message.reply_text("Iltimos, faqat son yuboring (masalan: 20).")
            return
        minutes, prayer_name = int(text), awaiting[1]
        AWAITING.pop(user_id, None)
        context.job_queue.run_once(send_single_prayer_reminder, when=timedelta(minutes=minutes),
                                    data={"user_id": user_id, "prayer_name": prayer_name})
        await update.message.reply_text(f"✅ {minutes} daqiqadan keyin {PRAYER_LABELS[prayer_name]} haqida qayta eslataman.")

    elif isinstance(awaiting, tuple) and awaiting[0] == "snooze_task":
        if not text.isdigit():
            await update.message.reply_text("Iltimos, faqat son yuboring (masalan: 20).")
            return
        minutes, task_text = int(text), awaiting[1]
        AWAITING.pop(user_id, None)
        context.job_queue.run_once(send_task_reminder, when=timedelta(minutes=minutes),
                                    data={"user_id": user_id, "task_text": task_text})
        await update.message.reply_text(f"✅ {minutes} daqiqadan keyin \"{task_text}\" haqida qayta eslataman.")


# ───────────────────────── HAFTALIK STATISTIKA ─────────────────────────

def format_report(start: date, end: date) -> str:
    lines = [f"📊 Haftalik hisobot ({start.strftime('%d.%m')} – {end.strftime('%d.%m')})\n"]
    for uid, name in config.USERS.items():
        s = storage.weekly_stats(uid, start, end)
        dhikr_line = ", ".join(f"{k}: {v}" for k, v in s["dhikr_sums"].items()) or "—"
        salovat_line = ", ".join(f"{k}: {v}" for k, v in s["salovat_sums"].items()) or "—"
        lines.append(
            f"*{name}*:\n"
            f"  Namoz — o'qidi: {s['done']}, qazo: {s['qazo']}, qoldirdi: {s['missed']}\n"
            f"  Vazifa — bajardi: {s['tasks_done']}, bajarmadi: {s['tasks_not_done']}\n"
            f"  Zikrlar — {dhikr_line}\n"
            f"  Salovatlar — {salovat_line}\n"
            f"  Maqsadlar yozilgan: {s['goal_count']}, Hisobotlar yuborilgan: {s['report_count']}\n"
        )
    return "\n".join(lines)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    end = date.today()
    start = end - timedelta(days=6)
    await update.message.reply_text(format_report(start, end), parse_mode="Markdown")

async def weekly_auto_report(context: ContextTypes.DEFAULT_TYPE):
    end = date.today()
    start = end - timedelta(days=6)
    await context.bot.send_message(config.ADMIN_ID, format_report(start, end), parse_mode="Markdown")


# ───────────────────────── KUN BOSHIDA JOBLARNI REJALASHTIRISH ─────────────────────────

async def schedule_today_jobs(context: ContextTypes.DEFAULT_TYPE):
    times = get_prayer_times(date.today())
    now = datetime.now()

    for name, dt in times.items():
        if name == "sunrise":
            continue
        if dt > now:
            context.job_queue.run_once(send_prayer_reminder, when=dt, data={"prayer_name": name},
                                        name=f"prayer-{name}-{dt.date()}")

    wake_time = times["fajr"] - timedelta(minutes=config.WAKE_BEFORE_FAJR_MINUTES)
    if wake_time > now:
        context.job_queue.run_once(send_wake_message, when=wake_time, name=f"wake-{wake_time.date()}")

    log.info(f"Bugungi joblar rejalashtirildi: { {k: v.strftime('%H:%M') for k, v in times.items()} }")


def main():
    storage.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command, filters=ALLOWED_FILTER))
    app.add_handler(CommandHandler("stats", stats_command, filters=ALLOWED_FILTER))
    app.add_handler(CallbackQueryHandler(handle_prayer_callback, pattern=r"^pray:"))
    app.add_handler(CallbackQueryHandler(handle_dhikr_callback, pattern=r"^dhikr:"))
    app.add_handler(CallbackQueryHandler(handle_task_callback, pattern=r"^task:"))
    app.add_handler(CallbackQueryHandler(handle_addmenu_callback, pattern=r"^addmenu:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ALLOWED_FILTER, handle_text))

    jq = app.job_queue
    jq.run_daily(schedule_today_jobs, time=dtime(hour=0, minute=5))
    jq.run_once(schedule_today_jobs, when=1)
    jq.run_daily(send_daily_tasks, time=dtime(hour=config.DAILY_TASKS_HOUR, minute=config.DAILY_TASKS_MINUTE))
    jq.run_daily(morning_goal_request, time=dtime(hour=config.MORNING_GOAL_HOUR, minute=config.MORNING_GOAL_MINUTE))
    jq.run_daily(evening_report_request, time=dtime(hour=config.EVENING_REPORT_HOUR, minute=config.EVENING_REPORT_MINUTE))
    jq.run_daily(weekly_auto_report, time=dtime(hour=22, minute=0), days=(6,))

    log.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()