from datetime import time


WEEKEND_OPEN_TIME = time(9, 0)
WEEKEND_CLOSE_TIME = time(17, 0)


def room_service_hours(room, service_date):
    """คืนเวลาเปิด-ปิดของห้องตามวันที่ให้บริการ"""
    if service_date.weekday() >= 5:
        return WEEKEND_OPEN_TIME, WEEKEND_CLOSE_TIME
    return room.open_time, room.close_time
