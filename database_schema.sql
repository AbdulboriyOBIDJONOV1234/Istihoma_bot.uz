-- Namoz bot uchun PostgreSQL / Neon ma'lumotlar bazasi skhemasi
-- Bu fayl botning ishlashi uchun kerak bo'ladigan jadvalar va indekslarni yaratadi.

BEGIN;

CREATE TABLE IF NOT EXISTS prayer_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    prayer_date DATE NOT NULL,
    prayer_name TEXT NOT NULL,
    status TEXT NOT NULL,
    dhikr_done BOOLEAN DEFAULT FALSE,
    UNIQUE (user_id, prayer_date, prayer_name)
);

CREATE TABLE IF NOT EXISTS task_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_date DATE NOT NULL,
    task_text TEXT NOT NULL,
    status TEXT NOT NULL,
    UNIQUE (user_id, task_date, task_text)
);

CREATE TABLE IF NOT EXISTS dhikr_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    log_date DATE NOT NULL,
    dhikr_name TEXT NOT NULL,
    total_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (user_id, log_date, dhikr_name)
);

CREATE INDEX IF NOT EXISTS idx_prayer_log_user_date
    ON prayer_log (user_id, prayer_date);

CREATE INDEX IF NOT EXISTS idx_task_log_user_date
    ON task_log (user_id, task_date);

CREATE INDEX IF NOT EXISTS idx_dhikr_log_user_date
    ON dhikr_log (user_id, log_date);

COMMIT;

-- Qo'shimcha izohlar:
-- prayer_log:
--   - user_id: Telegram foydalanuvchi ID
--   - prayer_date: namoz qaysi kunga tegishli ekanligi
--   - prayer_name: fajr, dhuhr, asr, maghrib, isha
--   - status: done / qazo
--   - dhikr_done: namozdan keyin zikrlar bajarildi-mi
--
-- task_log:
--   - user_id: foydalanuvchi ID
--   - task_date: vazifa qaysi kun uchun
--   - task_text: vazifa matni
--   - status: done / not_done
--
-- dhikr_log:
--   - user_id: foydalanuvchi ID
--   - log_date: qaysi kun uchun
--   - dhikr_name: Subhanalloh, Alhamdulillah, Allohu akbar, ...
--   - total_count: jami keltirilgan son (masalan 33x)
