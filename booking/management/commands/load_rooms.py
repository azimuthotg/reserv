from django.core.management.base import BaseCommand
from booking.models import Room


ROOMS = [
    {
        "name": "MINI THEATER",
        "booking_name": "mini",
        "capacity": 12,
        "location": "ชั้น 3 สำนักวิทยบริการ",
        "open_time": "08:30",
        "close_time": "16:30",
        "description": "ห้องมินิเธียเตอร์ รองรับได้ 12 คน",
        "ha_entity_id": "switch.room_mini",
    },
    {
        "name": "Edutainment Zone",
        "booking_name": "netflix",
        "capacity": 4,
        "location": "ชั้น 3 สำนักวิทยบริการ",
        "open_time": "08:30",
        "close_time": "16:30",
        "description": "โซนดูสื่อการเรียนรู้บันเทิง รองรับได้ 4 คน",
        "ha_entity_id": "switch.room_netflix",
    },
    {
        "name": "Canva Pro",
        "booking_name": "canva",
        "capacity": 2,
        "location": "ชั้น 1 สำนักวิทยบริการ",
        "open_time": "08:30",
        "close_time": "16:30",
        "description": "คอมพิวเตอร์ Canva Pro รองรับได้ 2 คน",
        "ha_entity_id": "switch.room_canva",
    },
    {
        "name": "ChatGPT",
        "booking_name": "chat-gpt",
        "capacity": 1,
        "location": "ชั้น 1 สำนักวิทยบริการ",
        "open_time": "08:30",
        "close_time": "16:30",
        "description": "คอมพิวเตอร์ ChatGPT Plus 1 เครื่อง",
        "ha_entity_id": "switch.room_chatgpt",
    },
    {
        "name": "โต๊ะประชุมชั้น 1",
        "booking_name": "meeting_f1",
        "capacity": 13,
        "location": "ชั้น 1 สำนักวิทยบริการ",
        "open_time": "08:00",
        "close_time": "16:30",
        "description": "โต๊ะประชุมชั้น 1 รองรับได้ 13 คน",
        "ha_entity_id": "",
    },
]


class Command(BaseCommand):
    help = 'โหลดข้อมูลห้อง 5 ห้องเริ่มต้น'

    def handle(self, *args, **options):
        created_count = 0
        for room_data in ROOMS:
            room, created = Room.objects.get_or_create(
                booking_name=room_data['booking_name'],
                defaults=room_data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  สร้างห้อง: {room.name}"))
            else:
                self.stdout.write(f"  มีอยู่แล้ว: {room.name}")

        self.stdout.write(self.style.SUCCESS(f"\nเสร็จสิ้น: สร้างใหม่ {created_count} ห้อง"))
