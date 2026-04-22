"""
python manage.py send_reminders
รันทุก 1 นาทีผ่าน Windows Task Scheduler
ส่งแจ้งเตือน LINE ก่อนเริ่ม 15 นาที และก่อนหมด 10 นาที
"""
from datetime import timedelta

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from booking.models import Booking, BookingLog

LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'
TH_MONTHS = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
             'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']


def _push_text(user_id, text):
    token = settings.LINE_CHANNEL_ACCESS_TOKEN
    if not token or not user_id:
        return False
    try:
        resp = requests.post(
            LINE_PUSH_URL,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type':  'application/json',
            },
            json={'to': user_id, 'messages': [{'type': 'text', 'text': text}]},
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False


class Command(BaseCommand):
    help = 'ส่ง LINE reminder ก่อนเริ่ม 15 นาที และก่อนหมด 10 นาที'

    def handle(self, *args, **options):
        now      = timezone.localtime(timezone.now())
        today    = now.date()
        cur_time = now.time()

        # หน้าต่างเวลา ±1 นาที เพื่อรองรับ Task Scheduler ที่รันไม่ตรงวินาที
        window = timedelta(minutes=1)

        confirmed = Booking.objects.filter(
            booking_date=today,
            status='confirmed',
        ).select_related('line_user', 'room')

        sent_15 = sent_10 = 0

        for b in confirmed:
            user_id  = b.line_user.line_user_id
            date_str = f'{b.booking_date.day} {TH_MONTHS[b.booking_date.month]} {b.booking_date.year + 543}'

            # ── แจ้งก่อนเริ่ม 15 นาที ────────────────────────────────────────
            if not b.notified_15min:
                start_dt = timezone.make_aware(
                    timezone.datetime.combine(today, b.start_time)
                )
                target = start_dt - timedelta(minutes=15)
                if target - window <= now < start_dt:
                    msg = (
                        f'⏰ อีก 15 นาทีถึงเวลาใช้พื้นที่\n'
                        f'📍 {b.room.name}\n'
                        f'📅 {date_str}\n'
                        f'🕐 {b.start_time.strftime("%H:%M")} – {b.end_time.strftime("%H:%M")}\n'
                        f'👥 {b.group_name}\n'
                        f'กรุณามาถึงตรงเวลา'
                    )
                    if _push_text(user_id, msg):
                        b.notified_15min = True
                        b.save(update_fields=['notified_15min'])
                        BookingLog.objects.create(booking=b, action='notified_15min')
                        sent_15 += 1

            # ── แจ้งก่อนหมด 10 นาที ──────────────────────────────────────────
            if not b.notified_10min:
                target = (
                    timezone.make_aware(
                        timezone.datetime.combine(today, b.end_time)
                    ) - timedelta(minutes=10)
                )
                if target - window <= now <= target + window:
                    msg = (
                        f'⚠️ อีก 10 นาทีหมดเวลาใช้พื้นที่\n'
                        f'📍 {b.room.name}\n'
                        f'🕐 หมดเวลา {b.end_time.strftime("%H:%M")} น.\n'
                        f'กรุณาเก็บของและออกจากห้องให้เรียบร้อย'
                    )
                    if _push_text(user_id, msg):
                        b.notified_10min = True
                        b.save(update_fields=['notified_10min'])
                        BookingLog.objects.create(booking=b, action='notified_10min')
                        sent_10 += 1

        self.stdout.write(
            f'[{now.strftime("%H:%M:%S")}] แจ้ง 15min: {sent_15}, แจ้ง 10min: {sent_10}'
        )
