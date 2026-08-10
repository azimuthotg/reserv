"""อัปเดตวิธีเข้าใช้งาน/กฎระเบียบของห้องบริการออนไลน์ ให้ตรงกับ VM Gateway ตัวใหม่

อ้างอิงหนังสือทีมพัฒนา LRS ARC VM Gateway ลงวันที่ 10 ส.ค. 2569 ข้อ 4 และ 7
(C:\\projects\\vm\\doc\\notify_new_url_2026-08-10.md) — ข้อความ "วิธีเข้าใช้บริการ"
และ "ข้อควรรู้" คัดมาจากเอกสารนั้นโดยตรง ตรวจ URL กับของจริงแล้วเมื่อ 10 ส.ค. 2569

เดิมเนื้อหาเขียนไว้ตอนที่ยังไม่มี Gateway ("เข้าใช้งานเครื่องคอมพิวเตอร์เสมือนผ่านเว็บ
ของสำนักวิทยบริการ") ซึ่งบอกไม่ได้ว่าต้องเข้าที่ไหนและต้องกดออกจากระบบ

    python doc/prep_vm_rooms_gateway.py            # ดูอย่างเดียว
    python doc/prep_vm_rooms_gateway.py --apply    # เขียนจริง

⚠️ เขียนลงฐาน production โดยตรง (.env เครื่อง dev ชี้ฐานเดียวกัน — ดู MEM.md)

**เลือกห้องจาก `Room.is_online` ไม่ใช่รายชื่อ booking_name** ตามกติกาในโปรเจกต์
ห้องออนไลน์ที่เพิ่มมาทีหลังจะได้เนื้อหาชุดเดียวกันอัตโนมัติ
"""
import os
import re
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reserv.settings")
django.setup()

from django.conf import settings  # noqa: E402

from booking.models import Room  # noqa: E402

GATEWAY = settings.VM_GATEWAY_URL
EARLY   = settings.VM_GATEWAY_EARLY_MINUTES

HOW_TO_USE = """\
- เข้าจองผ่าน Line OA : ARC NPU หรือเว็บของสำนักวิทยบริการ
- เลือกวัน เวลา ที่ต้องการใช้บริการ (จองได้รอบละ 1 ครั้ง)
- เมื่อถึงเวลาที่จอง กดปุ่ม "เข้าใช้งาน" ที่รายการจองของท่าน หรือเปิดเว็บ {gateway}
- เข้าสู่ระบบด้วยบัญชีอินเทอร์เน็ตของมหาวิทยาลัย (บัญชีเดียวกับที่ใช้เข้าระบบอื่นของ มนพ.)
- ระบบจะตรวจสอบการจองของท่านให้อัตโนมัติ แล้วพาเข้าเครื่องทันที ไม่ต้องเลือกเครื่องเอง
- ใช้งาน {app} บนหน้าจอเครื่องเสมือนที่ปรากฏได้ตามปกติ
- เมื่อเลิกใช้งาน ให้กดปุ่ม "ออกจากระบบ" ทุกครั้ง ห้ามปิดแท็บทิ้งเฉย ๆ
- แนะนำให้ใช้บนคอมพิวเตอร์ (โน้ตบุ๊ก/พีซี) ใช้บนมือถือได้แต่จะไม่สะดวก
- หากเข้าใช้งานไม่ได้ กรุณาติดต่อเจ้าหน้าที่"""

# กฎที่ต้องมีทุกห้องออนไลน์ — เพิ่มต่อจากกฎเดิมของแต่ละห้อง โดยไม่ทับของเดิม
GATEWAY_RULES = [
    "- เข้าใช้งานได้ตั้งแต่ {early} นาทีก่อนเวลาที่จอง และระบบจะตัดการเชื่อมต่อเมื่อหมดเวลาจอง",
    "- หนึ่งบัญชีเข้าใช้งานได้ครั้งละ 1 เครื่องเท่านั้น",
    "- ต้องกด \"ออกจากระบบ\" ทุกครั้งเมื่อเลิกใช้ การปิดแท็บทิ้งจะทำให้ผู้ที่จองรอบถัดไปเข้าใช้งานไม่ได้",
]


def app_label(room):
    """ชื่อโปรแกรมสำหรับใส่ในข้อความ — ตัดเลขลำดับเครื่องออกจากชื่อห้อง

    "Canva Pro 1" -> "Canva Pro" · "ChatGPT" -> "ChatGPT"
    """
    return re.sub(r"\s*\d+$", "", room.name).strip()


def merged_rules(room):
    """ต่อกฎของ Gateway เข้ากับกฎเดิม โดยไม่เพิ่มซ้ำถ้ารันหลายรอบ"""
    lines = [ln for ln in room.rules.splitlines() if ln.strip()]
    tail  = [ln for ln in lines if "ติดต่อเจ้าหน้าที่" in ln]
    head  = [ln for ln in lines if ln not in tail]

    for template in GATEWAY_RULES:
        rule = template.format(early=EARLY)
        key = rule[:28]
        if not any(key in ln for ln in head):
            head.append(rule)
    return "\n".join(head + tail)


def main():
    apply = "--apply" in sys.argv
    rooms = Room.objects.filter(is_online=True, is_active=True).order_by("booking_name")
    if not rooms:
        sys.exit("ไม่พบห้องออนไลน์ที่เปิดใช้งาน — ตรวจ Room.is_online")

    print(f"Gateway : {GATEWAY}")
    print(f"เข้าก่อนเวลาได้ : {EARLY} นาที")
    print(f"ห้องออนไลน์ที่จะแก้ : {rooms.count()} ห้อง\n")

    for room in rooms:
        how = HOW_TO_USE.format(gateway=GATEWAY, app=app_label(room))
        rules = merged_rules(room)

        print("=" * 72)
        print(f"{room.booking_name} | {room.name}")
        if room.how_to_use == how and room.rules == rules:
            print("  ตรงอยู่แล้ว ไม่ต้องแก้")
            continue
        print("--- how_to_use (ใหม่) ---")
        print(how)
        print("--- rules (ใหม่) ---")
        print(rules)

        if apply:
            room.how_to_use = how
            room.rules = rules
            room.save(update_fields=["how_to_use", "rules"])
            print("  >> บันทึกแล้ว")

    print()
    if apply:
        print("เขียนลงฐานเรียบร้อย — ตรวจที่ /room/<key>/ ได้เลย")
    else:
        print("โหมดดูอย่างเดียว — ใส่ --apply เพื่อเขียนจริง")


if __name__ == "__main__":
    main()
