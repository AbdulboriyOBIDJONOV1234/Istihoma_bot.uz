"""
Postgres (Neon) ombori — namoz, zikr va vazifalar tarixini saqlaydi.

Muhit o'zgaruvchisi kerak:
    DATABASE_URL — Neon bergan connection string, masalan:
    postgresql://user:password@ep-xxxx.neon.tech/dbname?sslmode=require
"""
import os
import psycopg2
from datetime import date

DATABASE_URL = os.environ.get("DATABASE_URL")

def _conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL muhit o'zgaruvchisi topilmadi. "
            "Neon'dan olgan connection string'ni DATABASE_URL ga qo'ying."
        )
    return psycopg2.connect(DATABASE_URL)

def init_db():
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prayer_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                prayer_date DATE NOT NULL,
                prayer_name TEXT NOT NULL,
                status TEXT NOT NULL,
                dhikr_done BOOLEAN DEFAULT FALSE,
                UNIQUE(user_id, prayer_date, prayer_name)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS task_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                task_date DATE NOT NULL,
                task_text TEXT NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(user_id, task_date, task_text)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dhikr_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                log_date DATE NOT NULL,
                dhikr_name TEXT NOT NULL,
                total_count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, log_date, dhikr_name)
            )
        """)

def set_prayer_status(user_id: int, prayer_date: date, prayer_name: str, status: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO prayer_log (user_id, prayer_date, prayer_name, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, prayer_date, prayer_name)
            DO UPDATE SET status = EXCLUDED.status
        """, (user_id, prayer_date, prayer_name, status))

def set_dhikr_done(user_id: int, prayer_date: date, prayer_name: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            UPDATE prayer_log SET dhikr_done = TRUE
            WHERE user_id = %s AND prayer_date = %s AND prayer_name = %s
        """, (user_id, prayer_date, prayer_name))

def add_dhikr_count(user_id: int, log_date: date, dhikr_name: str, amount: int):
    """Shu kun uchun dhikr_name sanog'iga 'amount' qo'shadi (kun bo'yi jamlab boradi)."""
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO dhikr_log (user_id, log_date, dhikr_name, total_count)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, log_date, dhikr_name)
            DO UPDATE SET total_count = dhikr_log.total_count + EXCLUDED.total_count
        """, (user_id, log_date, dhikr_name, amount))

def set_task_status(user_id: int, task_date: date, task_text: str, status: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO task_log (user_id, task_date, task_text, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, task_date, task_text)
            DO UPDATE SET status = EXCLUDED.status
        """, (user_id, task_date, task_text, status))

def weekly_stats(user_id: int, start_date: date, end_date: date) -> dict:
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT status, COUNT(*) FROM prayer_log
            WHERE user_id=%s AND prayer_date BETWEEN %s AND %s
            GROUP BY status
        """, (user_id, start_date, end_date))
        prayer_counts = dict(cur.fetchall())

        cur.execute("""
            SELECT status, COUNT(*) FROM task_log
            WHERE user_id=%s AND task_date BETWEEN %s AND %s
            GROUP BY status
        """, (user_id, start_date, end_date))
        task_counts = dict(cur.fetchall())

        cur.execute("""
            SELECT dhikr_name, SUM(total_count) FROM dhikr_log
            WHERE user_id=%s AND log_date BETWEEN %s AND %s
            GROUP BY dhikr_name
        """, (user_id, start_date, end_date))
        dhikr_sums = dict(cur.fetchall())

    return {
        "done": prayer_counts.get("done", 0),
        "qazo": prayer_counts.get("qazo", 0),
        "missed": prayer_counts.get("missed", 0),
        "tasks_done": task_counts.get("done", 0),
        "tasks_not_done": task_counts.get("not_done", 0),
        "dhikr_sums": dhikr_sums,
    }