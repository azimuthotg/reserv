"""เตรียมห้อง chat-gpt ให้เป็นบริการเครื่องเสมือน 24 ชม. (ตามใบแจ้งทีม VM 9 ส.ค. 2569)

⚠️ .env ชี้ฐาน production — สคริปต์นี้เขียนลงของจริง
**ยังไม่เปิดห้อง** (`is_active` คงเป็น 0) เพื่อให้ผู้ใช้ตรวจเนื้อหาก่อน
และยังไม่ปิด netflix1_vm — สองอย่างนั้นทำพร้อมกันตอนสลับบริการจริง

idempotent: รันซ้ำได้ ผลลัพธ์เหมือนเดิม
"""
import os
from datetime import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reserv.settings")
django.setup()

from django.conf import settings  # noqa: E402

from booking.models import Room  # noqa: E402

print("DB:", settings.DATABASES["default"]["HOST"], "/",
      settings.DATABASES["default"]["NAME"], "\n")

NEW = {
    "description": "เครื่องคอมพิวเตอร์เสมือนสำหรับใช้งาน ChatGPT (1 บัญชี) "
                   "ใช้งานผ่านเว็บ ไม่ต้องเข้าอาคาร",
    "location": "ออนไลน์ (เครื่องเสมือน ใช้งานผ่านเว็บ)",
    "eligible_users": "นักศึกษา คณาจารย์ และบุคลากร มหาวิทยาลัยนครพนม",
    "facilities": "เครื่องคอมพิวเตอร์เสมือน + บัญชี ChatGPT (1 บัญชี เฉพาะเครื่องนี้)",
    "rules": "\n".join([
        "- ต้องเข้าใช้บริการตามวันเวลาที่จองเท่านั้น",
        "- จองได้รอบละ 1 ครั้ง (เช้ามืด / กลางวัน / กลางคืน)",
        "- ห้ามใช้บัญชีร่วมกับผู้อื่นหรือเปลี่ยนรหัสผ่านของบัญชีที่ให้บริการ",
        "- เป็นบัญชีที่ใช้ร่วมกันหลายคน ไม่ควรพิมพ์ข้อมูลส่วนบุคคลหรือข้อมูลลับ "
        "ลงในบทสนทนา และควรลบประวัติการสนทนาก่อนเลิกใช้งาน",
        "- หากมีปัญหาใดกรุณาติดต่อเจ้าหน้าที่",
    ]),
    "how_to_use": "\n".join([
        "- เข้าจองผ่าน Line OA : ARC NPU",
        "- เลือกวัน เวลา ที่ต้องการใช้บริการ (จองได้รอบละ 1 ครั้ง)",
        "- เมื่อถึงเวลาที่จอง เข้าใช้งานเครื่องคอมพิวเตอร์เสมือนผ่านเว็บของสำนักวิทยบริการ",
        "- ใช้งาน ChatGPT ผ่านเบราว์เซอร์บนเครื่องเสมือนได้ตลอดช่วงเวลาที่จอง",
        "- หากเข้าใช้งานไม่ได้ กรุณาติดต่อเจ้าหน้าที่",
    ]),
    # ตามใบแจ้ง — ยกเว้น is_active ที่ยังไม่เปิด
    "is_online": True,
    "open_time": time(0, 0),
    "close_time": time(23, 59),
}

room = Room.objects.get(booking_name="chat-gpt")

for field, new_val in NEW.items():
    old = getattr(room, field)
    if old == new_val:
        print(f"[คงเดิม] {field}")
        continue
    setattr(room, field, new_val)
    print(f"[แก้]    {field}")
    print(f"         เดิม: {str(old)[:110]}")
    print(f"         ใหม่: {str(new_val)[:110]}")

room.save(update_fields=list(NEW.keys()))

room.refresh_from_db()
print("\n=== สถานะห้อง chat-gpt หลังแก้ ===")
print(f"  is_active        = {room.is_active}   <-- ยังปิดอยู่ รอผู้ใช้ตรวจก่อน")
print(f"  is_online        = {room.is_online}")
print(f"  open-close       = {room.open_time}–{room.close_time}")
print(f"  capacity         = {room.capacity}")
print(f"  day_round_enabled= {room.day_round_enabled}")
print(f"  allow_overlap    = {room.allow_overlap}")
