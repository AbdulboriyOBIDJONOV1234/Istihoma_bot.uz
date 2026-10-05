"""
Namoz & Kunlik reja boti — faqat 2 kishi uchun (Abdulboriy + Mohinur).

Ishga tushirish:
  1) pip install -r requirements.txt
  2) Muhit o'zgaruvchilarini sozlang: BOT_TOKEN, DATABASE_URL (Neon)
  3) config.py'da ism/vazifalarni tekshiring
  4) python bot.py
"""
import logging
from datetime import datetime, timedelta, date, time as dtime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

import config
import storage
from prayer_times import get_prayer_times, PRAYER_LABELS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PENDING_SNOOZE = {}
PENDING_ACTION = {}

ALLOWED_FILTER = filters.User(user_id=list(config.ALLOWED_IDS))


def logical_date(dt: datetime) -> date:
    """Islomiy kun hisobi."""
    today_times = get_prayer_times(dt.date())
    if dt.time() < today_times["fajr"].time():
        return dt.date() - timedelta(days=1)
    return dt.date()


def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🕌 Namoz", callback_data="menu:prayer"),
            InlineKeyboardButton("🙏 Zikr", callback_data="menu:zikr"),
        ],
        [
            InlineKeyboardButton("🌙 Salovat", callback_data="menu:salawat"),
            InlineKeyboardButton("🎯 Maqsad", callback_data="menu:goal"),
        ],
        [
            InlineKeyboardButton("✅ Vazifa", callback_data="menu:task"),
            InlineKeyboardButton("📊 Statistika", callback_data="menu:stats"),
        ],
    ])


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        config.GREETING_TEXT, parse_mode="Markdown", disable_web_page_preview=True
    )
    await update.message.reply_text("Tanlang:", reply_markup=main_menu())


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tanlang:", reply_markup=main_menu())


async def send_wake_message(context: ContextTypes.DEFAULT_TYPE):
    text = config.GREETING_TEXT + "\n\n" + config.WAKE_MOTIVATION
    for user_id in config.USERS:
        try:
            await context.bot.send_message(user_id, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            log.warning(f"Uyg'otish xabari yuborilmadi {user_id}: {e}")


async def send_morning_prompt(context: ContextTypes.DEFAULT_TYPE):
    for user_id in config.USERS:
        try:
            await context.bot.send_message(user_id, config.MORNING_PROMPT)
        except Exception as e:
            log.warning(f"Ertalab maqsad so'rovi yuborilmadi {user_id}: {e}")


async def send_evening_prompt(context: ContextTypes.DEFAULT_TYPE):
    for user_id in config.USERS:
        try:
            await context.bot.send_message(user_id, config.EVENING_PROMPT)
        except Exception as e:
            log.warning(f"Kechki hisobot so'rovi yuborilmadi {user_id}: {e}")


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in config.ALLOWED_IDS:
        return
    await query.answer()
    _, section = query.data.split(":")

    if section == "zikr":
        PENDING_ACTION[user_id] = "add_zikr"
        await query.edit_message_text("Zikr qo'shish. Masalan: `Subhanalloh 33` yoki faqat `Subhanalloh`")
    elif section == "salawat":
        PENDING_ACTION[user_id] = "add_salawat"
        await query.edit_message_text("Salovat qo'shish. Masalan: `Allahumma salli ala Muhammad 1`")
    elif section == "goal":
        PENDING_ACTION[user_id] = "add_goal"
        await query.edit_message_text("Bugun uchun maqsadingiz nima? Iltimos, qisqacha yozing.")
    elif section == "task":
        PENDING_ACTION[user_id] = "add_task"
        await query.edit_message_text("Bugungi vazifani yozing.")
    elif section == "stats":
        end = date.today()
        start = end - timedelta(days=6)
        await query.edit_message_text(format_report(start, end), parse_mode="Markdown")
    else:
        await query.edit_message_text("Tanlang:", reply_markup=main_menu())


# ───────────────────────── NAMOZ ESLATMALARI ─────────────────────────

def prayer_keyboard(prayer_name: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ O'qidim", callback_data=f"pray:done:{prayer_name}"),
            InlineKeyboardButton("⏳ Qazo qilaman", callback_data=f"pray:qazo:{prayer_name}"),
        ],
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
    rows = []
    for i, (name, count) in enumerate(config.DHIKRS):
        rows.append([InlineKeyboardButton(f"{name} — {count}x ✅", callback_data=f"dhikr:{prayer_name}:{i}")])
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
        await query.edit_message_text(
            f"✅ {label} namozi — o'qildi. Zikrlarni ham belgilang:",
            reply_markup=dhikr_keyboard(prayer_name),
        )
    elif action == "qazo":
        storage.set_prayer_status(user_id, today, prayer_name, "qazo")
        await query.edit_message_text(f"⏳ {label} namozi qazo sifatida belgilandi. Imkon bo'lganda qazosini o'qing.")
    elif action == "snooze":
        PENDING_SNOOZE[user_id] = prayer_name
        await query.edit_message_text(f"🔕 Bo'pti. {label} uchun necha daqiqadan keyin eslataymi? (son bilan yozing, masalan: 30)")

async def handle_dhikr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in config.ALLOWED_IDS:
        return
    await query.answer("Belgilandi ✅")
    _, prayer_name, idx = query.data.split(":")
    idx = int(idx)
    dhikr_name, dhikr_count = config.DHIKRS[idx]
    today = logical_date(datetime.now())

    storage.set_dhikr_done(user_id, today, prayer_name)
    storage.add_dhikr_count(user_id, today, dhikr_name, dhikr_count)

    await query.edit_message_text(f"🤲 {PRAYER_LABELS[prayer_name]}dan keyin \"{dhikr_name}\" — {dhikr_count}x qabul bo'lsin!")

async def handle_snooze_minutes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in PENDING_ACTION:
        action = PENDING_ACTION.pop(user_id)
        text = update.message.text.strip()
        today = logical_date(datetime.now())

        if action == "add_zikr":
            parts = text.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                zikr_name = " ".join(parts[:-1])
                count = int(parts[-1])
            else:
                zikr_name = text
                count = 1
            storage.add_custom_zikr(user_id, today, zikr_name, count)
            await update.message.reply_text(f"✅ \"{zikr_name}\" zikri saqlandi ({count}x).")
            return

        if action == "add_salawat":
            parts = text.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                name = " ".join(parts[:-1])
                count = int(parts[-1])
            else:
                name = text
                count = 1
            storage.add_salawat_count(user_id, today, name, count)
            await update.message.reply_text(f"✅ Salovat \"{name}\" saqlandi ({count}x).")
            return

        if action == "add_goal":
            storage.add_goal(user_id, today, text)
            await update.message.reply_text(f"✅ Maqsad saqlandi: {text}")
            return

        if action == "add_task":
            storage.set_task_status(user_id, today, text, "not_done")
            await update.message.reply_text(f"✅ Vazifa saqlandi: {text}")
            return

    if user_id not in PENDING_SNOOZE:
        return
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Iltimos, faqat son yuboring (masalan: 20) — necha daqiqadan keyin eslataymi?")
        return
    minutes = int(text)
    key = PENDING_SNOOZE.pop(user_id)

    if key.startswith("task::"):
        task_text = key.split("::", 1)[1]
        context.job_queue.run_once(
            send_task_reminder, when=timedelta(minutes=minutes),
            data={"user_id": user_id, "task_text": task_text}, name=f"snooze-task-{user_id}"
        )
        await update.message.reply_text(f"✅ {minutes} daqiqadan keyin \"{task_text}\" haqida qayta eslataman.")
    else:
        prayer_name = key
        context.job_queue.run_once(
            send_single_reminder, when=timedelta(minutes=minutes),
            data={"user_id": user_id, "prayer_name": prayer_name}, name=f"snooze-{user_id}-{prayer_name}"
        )
        await update.message.reply_text(f"✅ {minutes} daqiqadan keyin {PRAYER_LABELS[prayer_name]} haqida qayta eslataman.")

async def send_single_reminder(context: ContextTypes.DEFAULT_TYPE):
    d = context.job.data
    label = PRAYER_LABELS[d["prayer_name"]]
    await context.bot.send_message(
        d["user_id"], f"🕌 Eslatma: *{label}* namozini o'qidingizmi?",
        parse_mode="Markdown", reply_markup=prayer_keyboard(d["prayer_name"]),
    )

async def send_task_reminder(context: ContextTypes.DEFAULT_TYPE):
    d = context.job.data
    await context.bot.send_message(
        d["user_id"], f"📋 Eslatma: {d['task_text']}",
        reply_markup=task_keyboard(),
    )


# ───────────────────────── KUNLIK VAZIFALAR ─────────────────────────

def task_keyboard(idx: int = 0):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Qildim", callback_data=f"task:done:{idx}"),
        InlineKeyboardButton("❌ Qilmadim", callback_data=f"task:not_done:{idx}"),
        InlineKeyboardButton("🔕 Keyin", callback_data=f"task:snooze:{idx}"),
    ]])

async def send_daily_tasks(context: ContextTypes.DEFAULT_TYPE):
    for user_id, tasks in config.DAILY_TASKS.items():
        if not tasks:
            continue
        await context.bot.send_message(user_id, "📋 Bugungi rejalaringiz:")
        for i, task_text in enumerate(tasks):
            await context.bot.send_message(user_id, task_text, reply_markup=task_keyboard(i))

async def handle_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in config.ALLOWED_IDS:
        return
    await query.answer()
    _, action, idx = query.data.split(":")
    idx = int(idx)
    today = logical_date(datetime.now())
    tasks = config.DAILY_TASKS.get(user_id, [])
    task_text = tasks[idx] if idx < len(tasks) else query.message.text

    if action == "done":
        storage.set_task_status(user_id, today, task_text, "done")
        await query.edit_message_text(f"✅ {task_text}")
    elif action == "not_done":
        storage.set_task_status(user_id, today, task_text, "not_done")
        await query.edit_message_text(f"❌ {task_text}")
    elif action == "snooze":
        PENDING_SNOOZE[user_id] = f"task::{task_text}"
        await query.edit_message_text(f"🔕 \"{task_text}\" — necha daqiqadan keyin eslataymi? Son yozing.")


# ───────────────────────── HAFTALIK STATISTIKA ─────────────────────────

def format_report(start: date, end: date) -> str:
    lines = [f"📊 Haftalik hisobot ({start.strftime('%d.%m')} – {end.strftime('%d.%m')})\n"]
    for uid, name in config.USERS.items():
        s = storage.weekly_stats(uid, start, end)
        dhikr_line = ", ".join(f"{k}: {v}" for k, v in s["dhikr_sums"].items()) or "—"
        lines.append(
            f"*{name}*:\n"
            f"  Namoz — o'qidi: {s['done']}, qazo: {s['qazo']}, qoldirdi: {s['missed']}\n"
            f"  Vazifa — bajardi: {s['tasks_done']}, bajarmadi: {s['tasks_not_done']}\n"
            f"  Zikrlar — {dhikr_line}\n"
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
    """Har kuni 00:05 da o'sha kunning namoz vaqtlari va tonggi uyg'otish xabarini rejalashtiradi."""
    times = get_prayer_times(date.today())
    now = datetime.now()

    for name, dt in times.items():
        if name == "sunrise":
            continue
        if dt > now:
            context.job_queue.run_once(
                send_prayer_reminder, when=dt, data={"prayer_name": name}, name=f"prayer-{name}-{dt.date()}"
            )

    wake_time = times["fajr"] - timedelta(minutes=config.WAKE_BEFORE_FAJR_MINUTES)
    if wake_time > now:
        context.job_queue.run_once(send_wake_message, when=wake_time, name=f"wake-{wake_time.date()}")

    log.info(f"Bugungi joblar rejalashtirildi: { {k: v.strftime('%H:%M') for k, v in times.items()} }, uyg'otish: {wake_time.strftime('%H:%M')}")


def main():
    storage.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command, filters=ALLOWED_FILTER))
    app.add_handler(CommandHandler("menu", menu_command, filters=ALLOWED_FILTER))
    app.add_handler(CommandHandler("stats", stats_command, filters=ALLOWED_FILTER))
    app.add_handler(CallbackQueryHandler(handle_prayer_callback, pattern=r"^pray:"))
    app.add_handler(CallbackQueryHandler(handle_dhikr_callback, pattern=r"^dhikr:"))
    app.add_handler(CallbackQueryHandler(handle_task_callback, pattern=r"^task:"))
    app.add_handler(CallbackQueryHandler(handle_menu_callback, pattern=r"^menu:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ALLOWED_FILTER, handle_snooze_minutes))

    jq = app.job_queue
    jq.run_daily(schedule_today_jobs, time=dtime(hour=0, minute=5))
    jq.run_once(schedule_today_jobs, when=1)
    jq.run_daily(send_daily_tasks, time=dtime(hour=config.DAILY_TASKS_HOUR, minute=config.DAILY_TASKS_MINUTE))
    jq.run_daily(send_morning_prompt, time=dtime(hour=7, minute=0))
    jq.run_daily(send_evening_prompt, time=dtime(hour=23, minute=0))
    jq.run_daily(weekly_auto_report, time=dtime(hour=22, minute=0), days=(6,))

    log.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()