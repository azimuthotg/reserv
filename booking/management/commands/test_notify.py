"""
ทดสอบ LINE notification โดยไม่ต้องรอเวลาจริง

# ส่ง push ทดสอบหา userId ตรงๆ
python manage.py test_notify --user-id Uxxxxxxxx

# ทดสอบ flow จองสำเร็จ (ใช้ booking ล่าสุดใน DB)
python manage.py test_notify --booking-confirmed

# จำลอง reminder 15 นาที (ใช้ booking ล่าสุด)
python manage.py test_notify --reminder-15

# จำลอง reminder 10 นาที (ใช้ booking ล่าสุด)
python manage.py test_notify --reminder-10
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from booking.models import Booking
from booking.views import _notify_booking_confirmed, _push_text

TH_MONTHS = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
             'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']


class Command(BaseCommand):
    help = 'ทดสอบ LINE push notification'

    def add_arguments(self, parser):
        parser.add_argument('--user-id',         help='LINE userId ที่ต้องการส่งทดสอบ')
        parser.add_argument('--booking-id',       type=int, help='Booking ID (ถ้าไม่ระบุใช้ล่าสุด)')
        parser.add_argument('--booking-confirmed', action='store_true', help='ทดสอบแจ้งจองสำเร็จ')
        parser.add_argument('--reminder-15',      action='store_true', help='ทดสอบแจ้งก่อนเริ่ม 15 นาที')
        parser.add_argument('--reminder-10',      action='store_true', help='ทดสอบแจ้งก่อนหมด 10 นาที')

    def handle(self, *args, **options):
        token = settings.LINE_CHANNEL_ACCESS_TOKEN
        self.stdout.write(f'LINE_CHANNEL_ACCESS_TOKEN: {"✅ มี" if token else "❌ ไม่มี — เช็ค .env"}')

        # ── ping ตรงๆ ด้วย userId ────────────────────────────────────────────
        if options['user_id']:
            uid = options['user_id']
            ok = _push_text(uid, '🔔 ทดสอบระบบแจ้งเตือน Library@NPU\nข้อความนี้ส่งจากระบบจองพื้นที่')
            self.stdout.write(f'push to {uid}: {"✅ สำเร็จ" if ok else "❌ ล้มเหลว"}')
            return

        # ── ดึง booking ────────────────────────────────────────────────────────
        qs = Booking.objects.select_related('line_user', 'room')
        if options['booking_id']:
            qs = qs.filter(pk=options['booking_id'])
        else:
            qs = qs.order_by('-created_at')

        b = qs.first()
        if not b:
            self.stdout.write('❌ ไม่พบ Booking ใน DB')
            return

        self.stdout.write(f'ใช้ Booking #{b.id} — {b.room.name} {b.booking_date} {b.start_time:%H:%M}-{b.end_time:%H:%M}')
        self.stdout.write(f'ผู้จอง: {b.line_user.full_name} ({b.line_user.line_user_id})')
        uid = b.line_user.line_user_id

        date_str = f'{b.booking_date.day} {TH_MONTHS[b.booking_date.month]} {b.booking_date.year + 543}'

        if options['booking_confirmed']:
            _notify_booking_confirmed(b)
            self.stdout.write('✅ ส่งแจ้งจองสำเร็จแล้ว')

        elif options['reminder_15']:
            msg = (
                f'⏰ อีก 15 นาทีถึงเวลาใช้พื้นที่\n'
                f'📍 {b.room.name}\n'
                f'📅 {date_str}\n'
                f'🕐 {b.start_time.strftime("%H:%M")} – {b.end_time.strftime("%H:%M")}\n'
                f'👥 {b.group_name}\n'
                f'กรุณามาถึงตรงเวลา'
            )
            ok = _push_text(uid, msg)
            self.stdout.write(f'push 15min reminder: {"✅ สำเร็จ" if ok else "❌ ล้มเหลว"}')

        elif options['reminder_10']:
            msg = (
                f'⚠️ อีก 10 นาทีหมดเวลาใช้พื้นที่\n'
                f'📍 {b.room.name}\n'
                f'🕐 หมดเวลา {b.end_time.strftime("%H:%M")} น.\n'
                f'กรุณาเก็บของและออกจากห้องให้เรียบร้อย'
            )
            ok = _push_text(uid, msg)
            self.stdout.write(f'push 10min reminder: {"✅ สำเร็จ" if ok else "❌ ล้มเหลว"}')

        else:
            self.stdout.write('ระบุ --booking-confirmed, --reminder-15, --reminder-10 หรือ --user-id')
