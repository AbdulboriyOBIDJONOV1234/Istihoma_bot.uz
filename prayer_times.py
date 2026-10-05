"""
Toshkent uchun 5 vaqt namoz vaqtlarini hisoblash (astronomik formula asosida).
Hech qanday internetga ulanish shart emas — har kuni avtomatik to'g'ri hisoblanadi.

Usul: Hanafiy (Asr uchun soya koeffitsienti = 2), Fajr/Isha burchagi = 18 gradus.
Bu rasmiy jadvalga odatda 1-2 daqiqagacha farq qiladi.
"""
import math
from datetime import datetime, timedelta, date

LAT = 41.2995
LON = 69.2401
TZ = 5  # Toshkent UTC+5

FAJR_ANGLE = 18.0
ISHA_ANGLE = 18.0
ASR_FACTOR = 2  # Hanafiy

def _julian_date(d: date) -> float:
    y, m, day = d.year, d.month, d.day
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5

def _sun_position(jd: float):
    d = jd - 2451545.0
    g = math.radians((357.529 + 0.98560028 * d) % 360)
    q = (280.459 + 0.98564736 * d) % 360
    l = math.radians((q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360)
    e = math.radians(23.439 - 0.00000036 * d)
    ra = math.degrees(math.atan2(math.cos(e) * math.sin(l), math.cos(l))) / 15
    decl = math.degrees(math.asin(math.sin(e) * math.sin(l)))
    ra = ra % 24
    eqt = q / 15 - ra
    return decl, eqt

def _hour_angle(lat, decl, angle):
    lat_r, decl_r, ang_r = math.radians(lat), math.radians(decl), math.radians(angle)
    val = (-math.sin(ang_r) - math.sin(lat_r) * math.sin(decl_r)) / (math.cos(lat_r) * math.cos(decl_r))
    val = max(-1, min(1, val))
    return math.degrees(math.acos(val))

def _asr_angle(lat, decl, factor):
    lat_r, decl_r = math.radians(lat), math.radians(decl)
    diff = abs(lat - decl)
    alt = math.degrees(math.atan(1 / (factor + math.tan(math.radians(diff)))))
    alt_r = math.radians(alt)
    val = (math.sin(alt_r) - math.sin(lat_r) * math.sin(decl_r)) / (math.cos(lat_r) * math.cos(decl_r))
    val = max(-1, min(1, val))
    return math.degrees(math.acos(val))

def get_prayer_times(d: date) -> dict:
    """Berilgan sana uchun {'fajr','sunrise','dhuhr','asr','maghrib','isha'} -> datetime qaytaradi."""
    jd = _julian_date(d)
    decl, eqt = _sun_position(jd - TZ / 24 + 0.5)
    dhuhr_h = 12 + TZ - LON / 15 - eqt
    h_fajr = _hour_angle(LAT, decl, FAJR_ANGLE)
    h_isha = _hour_angle(LAT, decl, ISHA_ANGLE)
    h_sun = _hour_angle(LAT, decl, 0.833)
    h_asr = _asr_angle(LAT, decl, ASR_FACTOR)

    hours = {
        "fajr": dhuhr_h - h_fajr / 15,
        "sunrise": dhuhr_h - h_sun / 15,
        "dhuhr": dhuhr_h,
        "asr": dhuhr_h + h_asr / 15,
        "maghrib": dhuhr_h + h_sun / 15,
        "isha": dhuhr_h + h_isha / 15,
    }
    result = {}
    for name, h in hours.items():
        hh = int(h) % 24
        mm = round((h - int(h)) * 60)
        if mm == 60:
            mm = 0
            hh = (hh + 1) % 24
        result[name] = datetime.combine(d, datetime.min.time()) + timedelta(hours=hh, minutes=mm)
    return result

PRAYER_LABELS = {
    "fajr": "Bomdod",
    "dhuhr": "Peshin",
    "asr": "Asr",
    "maghrib": "Shom",
    "isha": "Xufton",
}
