from datetime import time
from datetime import timedelta


WEEKEND_OPEN_TIME = time(9, 0)
WEEKEND_CLOSE_TIME = time(17, 0)


def room_service_hours(room, service_date):
    """คืนเวลาเปิด-ปิดของห้องตามวันที่ให้บริการ"""
    if service_date.weekday() >= 5:
        return WEEKEND_OPEN_TIME, WEEKEND_CLOSE_TIME
    return room.open_time, room.close_time


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
