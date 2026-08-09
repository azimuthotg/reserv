"""สลับบริการเครื่องเสมือน: ปิด Netflix Pro → เปิด ChatGPT
(ตามใบแจ้งทีม LRS ARC VM Gateway 9 ส.ค. 2569)

⚠️ .env ชี้ฐาน production — เขียนลงของจริง
แก้เฉพาะ `is_active` ของ 2 ห้อง · ไม่ลบห้อง ไม่ลบประวัติการจอง
เนื้อหาห้อง chat-gpt เตรียมไว้แล้วด้วย doc/prep_chatgpt_room.py

idempotent: รันซ้ำได้
"""
import os
import sys
from datetime import date

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reserv.settings")
django.setup()

from django.db import transaction  # noqa: E402

from booking.models import Booking, Room  # noqa: E402

TARGETS = {"netflix1_vm": False, "chat-gpt": True}
today = date.today()

# กันพลาด: ห้ามปิดห้องที่ยังมีคนจองไว้ล่วงหน้า
for key, active in TARGETS.items():
    if active:
        continue
    future = Booking.objects.filter(
        room__booking_name=key, status="confirmed", booking_date__gte=today).count()
    if future:
        raise SystemExit(f"หยุด: {key} ยังมีการจอง confirmed ตั้งแต่วันนี้ {future} รายการ")
    print(f"ตรวจแล้ว: {key} ไม่มีการจองล่วงหน้า (confirmed ตั้งแต่ {today}) — ปิดได้")

with transaction.atomic():
    for key, active in TARGETS.items():
        room = Room.objects.select_for_update().get(booking_name=key)
        if room.is_active == active:
            print(f"[คงเดิม] {key:14s} is_active={room.is_active}")
            continue
        before = room.is_active
        room.is_active = active
        room.save(update_fields=["is_active"])
        print(f"[แก้]    {key:14s} is_active {before} -> {room.is_active}")

print("\n=== ห้องที่เปิดให้บริการหลังสลับ ===")
for r in Room.objects.filter(is_active=True).order_by("id"):
    kind = "VM 24 ชม." if r.is_online else "ห้องจริง"
    print(f"  {r.id:>2} {r.booking_name:14s} {r.name:18s} "
          f"{r.open_time.strftime('%H:%M')}–{r.close_time.strftime('%H:%M')}  {kind}")

print("\n=== ห้องที่ปิด (เก็บประวัติไว้) ===")
for r in Room.objects.filter(is_active=False).order_by("id"):
    n = Booking.objects.filter(room=r).count()
    print(f"  {r.id:>2} {r.booking_name:14s} {r.name:18s} ประวัติ {n} รายการ")
