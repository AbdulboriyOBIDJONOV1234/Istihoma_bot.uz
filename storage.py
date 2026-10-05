"""
Postgres (Neon) ombori.

Muhit o'zgaruvchisi kerak:
    DATABASE_URL — Neon bergan connection string:
    postgresql://user:password@ep-xxxx.neon.tech/dbname?sslmode=require

Jadvallar: prayer_log, task_log, dhikr_log, salovat_log, goals, reports.
Har biri alohida — namoz, zikr, salovat, maqsad, vazifa, hisobot ma'lumotlari
bir-biridan ajratilgan holda saqlanadi.
"""
import os
import psycopg2
from datetime import date

DATABASE_URL = os.environ.get("DATABASE_URL")

def _conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL muhit o'zgaruvchisi topilmadi. Neon connection string'ni qo'ying."
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS salovat_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                log_date DATE NOT NULL,
                salovat_name TEXT NOT NULL,
                total_count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, log_date, salovat_name)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                goal_date DATE NOT NULL,
                goal_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                report_date DATE NOT NULL,
                report_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

# ── NAMOZ ──
def set_prayer_status(user_id: int, prayer_date: date, prayer_name: str, status: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO prayer_log (user_id, prayer_date, prayer_name, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, prayer_date, prayer_name)
            DO UPDATE SET status = EXCLUDED.status
        """, (user_id, prayer_date, prayer_name, status))

def set_dhikr_done_flag(user_id: int, prayer_date: date, prayer_name: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            UPDATE prayer_log SET dhikr_done = TRUE
            WHERE user_id = %s AND prayer_date = %s AND prayer_name = %s
        """, (user_id, prayer_date, prayer_name))

def get_today_prayers(user_id: int, prayer_date: date) -> dict:
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT prayer_name, status FROM prayer_log
            WHERE user_id=%s AND prayer_date=%s
        """, (user_id, prayer_date))
        return dict(cur.fetchall())

# ── ZIKR / SALOVAT (erkin qo'shish) ──
def add_dhikr_count(user_id: int, log_date: date, dhikr_name: str, amount: int):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO dhikr_log (user_id, log_date, dhikr_name, total_count)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, log_date, dhikr_name)
            DO UPDATE SET total_count = dhikr_log.total_count + EXCLUDED.total_count
        """, (user_id, log_date, dhikr_name, amount))

def add_salovat_count(user_id: int, log_date: date, salovat_name: str, amount: int):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO salovat_log (user_id, log_date, salovat_name, total_count)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, log_date, salovat_name)
            DO UPDATE SET total_count = salovat_log.total_count + EXCLUDED.total_count
        """, (user_id, log_date, salovat_name, amount))

def get_today_dhikrs(user_id: int, log_date: date) -> list:
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT dhikr_name, total_count FROM dhikr_log
            WHERE user_id=%s AND log_date=%s ORDER BY id
        """, (user_id, log_date))
        return cur.fetchall()

def get_today_salovats(user_id: int, log_date: date) -> list:
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT salovat_name, total_count FROM salovat_log
            WHERE user_id=%s AND log_date=%s ORDER BY id
        """, (user_id, log_date))
        return cur.fetchall()

# ── MAQSAD ──
def add_goal(user_id: int, goal_date: date, goal_text: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO goals (user_id, goal_date, goal_text) VALUES (%s, %s, %s)
        """, (user_id, goal_date, goal_text))

def get_today_goals(user_id: int, goal_date: date) -> list:
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT goal_text FROM goals WHERE user_id=%s AND goal_date=%s ORDER BY id
        """, (user_id, goal_date))
        return [r[0] for r in cur.fetchall()]

# ── VAZIFA ──
def add_task(user_id: int, task_date: date, task_text: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO task_log (user_id, task_date, task_text, status)
            VALUES (%s, %s, %s, 'pending')
            ON CONFLICT (user_id, task_date, task_text) DO NOTHING
        """, (user_id, task_date, task_text))

def set_task_status(user_id: int, task_date: date, task_text: str, status: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO task_log (user_id, task_date, task_text, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, task_date, task_text)
            DO UPDATE SET status = EXCLUDED.status
        """, (user_id, task_date, task_text, status))

def get_today_tasks(user_id: int, task_date: date) -> list:
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT task_text, status FROM task_log
            WHERE user_id=%s AND task_date=%s ORDER BY id
        """, (user_id, task_date))
        return cur.fetchall()

# ── HISOBOT ──
def add_report(user_id: int, report_date: date, report_text: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO reports (user_id, report_date, report_text) VALUES (%s, %s, %s)
        """, (user_id, report_date, report_text))

# ── HAFTALIK STATISTIKA ──
def weekly_stats(user_id: int, start_date: date, end_date: date) -> dict:
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT status, COUNT(*) FROM prayer_log
            WHERE user_id=%s AND prayer_date BETWEEN %s AND %s GROUP BY status
        """, (user_id, start_date, end_date))
        prayer_counts = dict(cur.fetchall())

        cur.execute("""
            SELECT status, COUNT(*) FROM task_log
            WHERE user_id=%s AND task_date BETWEEN %s AND %s GROUP BY status
        """, (user_id, start_date, end_date))
        task_counts = dict(cur.fetchall())

        cur.execute("""
            SELECT dhikr_name, SUM(total_count) FROM dhikr_log
            WHERE user_id=%s AND log_date BETWEEN %s AND %s GROUP BY dhikr_name
        """, (user_id, start_date, end_date))
        dhikr_sums = dict(cur.fetchall())

        cur.execute("""
            SELECT salovat_name, SUM(total_count) FROM salovat_log
            WHERE user_id=%s AND log_date BETWEEN %s AND %s GROUP BY salovat_name
        """, (user_id, start_date, end_date))
        salovat_sums = dict(cur.fetchall())

        cur.execute("""
            SELECT COUNT(*) FROM goals WHERE user_id=%s AND goal_date BETWEEN %s AND %s
        """, (user_id, start_date, end_date))
        goal_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM reports WHERE user_id=%s AND report_date BETWEEN %s AND %s
        """, (user_id, start_date, end_date))
        report_count = cur.fetchone()[0]

    return {
        "done": prayer_counts.get("done", 0),
        "qazo": prayer_counts.get("qazo", 0),
        "missed": prayer_counts.get("missed", 0),
        "tasks_done": task_counts.get("done", 0),
        "tasks_not_done": task_counts.get("not_done", 0),
        "dhikr_sums": dhikr_sums,
        "salovat_sums": salovat_sums,
        "goal_count": goal_count,
        "report_count": report_count,
    }