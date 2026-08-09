from datetime import time
from datetime import timedelta


WEEKEND_OPEN_TIME = time(9, 0)
WEEKEND_CLOSE_TIME = time(17, 0)

# ── เพดานเวลาจองต่อครั้ง ──────────────────────────────────────────────────────
# ค่ากลางของทั้งระบบ ใช้เหมือนกันทุกห้อง ทั้ง backend guard, ฟอร์มจอง และหน้ารายละเอียด
# **ห้ามใช้ `Room.max_booking_hours`** — ฟิลด์นั้นไม่เคยถูกบังคับใช้จริง (เป็น IntegerField
# เก็บ 3.5 ไม่ได้) หน้ารายละเอียดเคยแสดงค่าจากฟิลด์นั้นจึงขัดกับที่จองได้จริงทุกห้อง
# แก้เพดานทั้งระบบให้แก้ที่บรรทัดเดียวนี้
MAX_BOOKING_MINUTES = 210
MAX_BOOKING_HOURS_TEXT = '3.5'      # ข้อความที่แสดงให้ผู้ใช้เห็น (ตัดศูนย์ท้ายออกแล้ว)

# ── รอบการให้บริการ (ใช้แยกโควตา "1 สิทธิ์ต่อห้อง ต่อรอบ") ────────────────────
# ห้องจริงเปิดแค่ช่วงกลางวัน การจองทั้งหมดจึงตกอยู่ในรอบ 'day' เสมอ
# ส่วนบริการออนไลน์ (Room.is_online) จองได้ทั้ง 3 รอบเพราะเครื่องแม่เปิด 24 ชม.
ROUND_EARLY = 'early'
ROUND_DAY   = 'day'
ROUND_NIGHT = 'night'

DAY_START   = time(8, 30)    # เช้ามืดจบ / กลางวันเริ่ม
NIGHT_START = time(17, 0)    # กลางวันจบ / กลางคืนเริ่ม

ROUND_BOUNDS = {
    ROUND_EARLY: (time(0, 0),  DAY_START),
    ROUND_DAY:   (DAY_START,   NIGHT_START),
    ROUND_NIGHT: (NIGHT_START, time(23, 59)),
}

ROUND_LABELS = {
    ROUND_EARLY: 'เช้ามืด (00:00–08:30)',
    ROUND_DAY:   'กลางวัน (08:30–17:00)',
    ROUND_NIGHT: 'กลางคืน (17:00–23:59)',
}


def room_service_hours(room, service_date):
    """คืนเวลาเปิด-ปิดของห้องตามวันที่ให้บริการ

    บริการออนไลน์ (is_online) ไม่ผูกกับเวลาเปิด-ปิดอาคาร ใช้ open_time/close_time
    ของห้องทุกวันรวมเสาร์-อาทิตย์
    """
    if getattr(room, 'is_online', False):
        return room.open_time, room.close_time
    if service_date.weekday() >= 5:
        return WEEKEND_OPEN_TIME, WEEKEND_CLOSE_TIME
    return room.open_time, room.close_time


def booking_round(start_time):
    """คืนรอบของการจองจากเวลาเริ่ม"""
    if start_time < DAY_START:
        return ROUND_EARLY
    if start_time < NIGHT_START:
        return ROUND_DAY
    return ROUND_NIGHT


def round_of_range(start_time, end_time):
    """คืนรอบของช่วงเวลา หรือ None ถ้าคร่อมรอบ (นับสิทธิ์ไม่ได้)

    ขอบรอบถือแบบปิดท้าย เช่น 08:30 เป็นจุดจบของรอบเช้ามืดและจุดเริ่มของรอบกลางวัน
    การจอง 06:00–08:30 จึงอยู่ในรอบเช้ามืด ส่วน 08:30–10:00 อยู่ในรอบกลางวัน
    """
    r = booking_round(start_time)
    _, bound_end = ROUND_BOUNDS[r]
    if end_time > bound_end:
        return None
    return r


def round_start_filter(round_name):
    """คืน filter kwargs ของ Booking.start_time สำหรับรอบที่ระบุ (ใช้นับโควตารายรอบ)"""
    if round_name == ROUND_EARLY:
        return {'start_time__lt': DAY_START}
    if round_name == ROUND_DAY:
        return {'start_time__gte': DAY_START, 'start_time__lt': NIGHT_START}
    return {'start_time__gte': NIGHT_START}


def max_advance_service_date(start_date, holiday_dates, advance_days):
    """คืนวันเปิดบริการลำดับที่ advance_days หลัง start_date โดยข้ามวันปิดทั้งสำนัก"""
    current = start_date
    counted = 0
    while counted < advance_days:
        current += timedelta(days=1)
        if current in holiday_dates:
            continue
        counted += 1
    return current
