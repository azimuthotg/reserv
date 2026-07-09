import json
from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, LineUser, Room


def _next_weekday(from_date):
    d = from_date
    while True:
        d += timedelta(days=1)
        if d.weekday() < 5:
            return d


class BookingRoomPerDayLimitTests(TestCase):
    """คนเดียวจองห้องเดียวกันซ้ำในวันเดียวกันไม่ได้ แต่จองห้องอื่น หรือวันอื่นได้"""

    def setUp(self):
        self.room_a = Room.objects.create(
            name='ห้องทดสอบ A', booking_name='test-room-a',
            location='ชั้น 1', capacity=10,
            open_time='08:30', close_time='16:30',
        )
        self.room_b = Room.objects.create(
            name='ห้องทดสอบ B', booking_name='test-room-b',
            location='ชั้น 1', capacity=10,
            open_time='08:30', close_time='16:30',
        )
        self.user = LineUser.objects.create(
            line_user_id='U_test_001', display_name='Tester',
            user_ldap='tester', user_type='นักศึกษา',
            full_name='Test User', faculty='คณะทดสอบ', is_active=True,
        )
        self.other_user = LineUser.objects.create(
            line_user_id='U_test_002', display_name='Tester2',
            user_ldap='tester2', user_type='นักศึกษา',
            full_name='Test User 2', faculty='คณะทดสอบ', is_active=True,
        )
        self.b_date = _next_weekday(date.today())
        self.client = Client()

    def _post(self, user_id, room, b_date, start, end):
        return self.client.post(
            reverse('create_booking'),
            data=json.dumps({
                'userId': user_id,
                'room': room.booking_name,
                'booking_date': b_date.strftime('%Y-%m-%d'),
                'start_time': start,
                'end_time': end,
                'group_name': 'กลุ่มทดสอบ',
                'attendees': 'ผู้ทดสอบ',
            }),
            content_type='application/json',
        )

    def test_second_booking_same_room_same_day_blocked(self):
        resp1 = self._post(self.user.line_user_id, self.room_a, self.b_date, '09:00', '10:00')
        self.assertEqual(resp1.status_code, 200, resp1.content)

        resp2 = self._post(self.user.line_user_id, self.room_a, self.b_date, '11:00', '12:00')
        self.assertEqual(resp2.status_code, 409, resp2.content)
        self.assertIn('1 ครั้งต่อวัน', resp2.json()['error'])

        self.assertEqual(
            Booking.objects.filter(line_user=self.user, room=self.room_a, booking_date=self.b_date).count(),
            1,
        )

    def test_second_booking_different_room_same_day_allowed(self):
        resp1 = self._post(self.user.line_user_id, self.room_a, self.b_date, '09:00', '10:00')
        self.assertEqual(resp1.status_code, 200, resp1.content)

        resp2 = self._post(self.user.line_user_id, self.room_b, self.b_date, '09:00', '10:00')
        self.assertEqual(resp2.status_code, 200, resp2.content)

    def test_second_booking_same_room_different_day_allowed(self):
        resp1 = self._post(self.user.line_user_id, self.room_a, self.b_date, '09:00', '10:00')
        self.assertEqual(resp1.status_code, 200, resp1.content)

        next_day = _next_weekday(self.b_date)
        resp2 = self._post(self.user.line_user_id, self.room_a, next_day, '09:00', '10:00')
        self.assertEqual(resp2.status_code, 200, resp2.content)

    def test_cancelled_booking_does_not_block_new_booking_same_room_same_day(self):
        resp1 = self._post(self.user.line_user_id, self.room_a, self.b_date, '09:00', '10:00')
        self.assertEqual(resp1.status_code, 200, resp1.content)
        Booking.objects.filter(line_user=self.user, room=self.room_a, booking_date=self.b_date).update(status='cancelled')

        resp2 = self._post(self.user.line_user_id, self.room_a, self.b_date, '11:00', '12:00')
        self.assertEqual(resp2.status_code, 200, resp2.content)

    def test_different_user_same_room_same_day_allowed(self):
        resp1 = self._post(self.user.line_user_id, self.room_a, self.b_date, '09:00', '10:00')
        self.assertEqual(resp1.status_code, 200, resp1.content)

        resp2 = self._post(self.other_user.line_user_id, self.room_a, self.b_date, '11:00', '12:00')
        self.assertEqual(resp2.status_code, 200, resp2.content)


class ManageAnalyticsTests(TestCase):
    """หน้าวิเคราะห์การจอง — no-show, ยกเลิกกระชั้นชิด, KPI พื้นฐาน"""

    def setUp(self):
        self.staff = User.objects.create_user(username='staff1', password='pass12345', is_staff=True)
        self.room = Room.objects.create(
            name='ห้องทดสอบ Analytics', booking_name='test-room-analytics',
            location='ชั้น 1', capacity=10,
            open_time='08:30', close_time='16:30',
        )
        self.user1 = LineUser.objects.create(
            line_user_id='U_ana_001', display_name='Ana1', user_ldap='ana1',
            user_type='นักศึกษา', full_name='Ana One', faculty='คณะ A', is_active=True,
        )
        self.user2 = LineUser.objects.create(
            line_user_id='U_ana_002', display_name='Ana2', user_ldap='ana2',
            user_type='นักศึกษา', full_name='Ana Two', faculty='คณะ B', is_active=True,
        )
        self.client = Client()
        self.client.login(username='staff1', password='pass12345')

        yesterday = date.today() - timedelta(days=1)
        Booking.objects.create(
            room=self.room, line_user=self.user1, faculty='คณะ A', group_name='กลุ่ม',
            booking_date=yesterday, start_time='09:00', end_time='10:00',
            attendees='1', status='confirmed', checked_in=False,
        )
        Booking.objects.create(
            room=self.room, line_user=self.user2, faculty='คณะ B', group_name='กลุ่ม',
            booking_date=yesterday, start_time='11:00', end_time='12:00',
            attendees='1', status='confirmed', checked_in=True,
        )

        today = date.today()
        late_cancel_booking = Booking.objects.create(
            room=self.room, line_user=self.user1, faculty='คณะ A', group_name='กลุ่ม',
            booking_date=today, start_time='23:00', end_time='23:59',
            attendees='1', status='cancelled', cancel_reason='ทดสอบ',
        )
        start_dt = timezone.make_aware(datetime.combine(today, time(23, 0)))
        late_cancel_booking.cancelled_at = start_dt - timedelta(minutes=30)
        late_cancel_booking.save(update_fields=['cancelled_at'])

    def test_analytics_page_loads_and_computes_kpis(self):
        resp = self.client.get(reverse('manage_analytics'), {'period': '30'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_confirmed'], 2)
        self.assertEqual(resp.context['total_cancelled'], 1)
        self.assertEqual(resp.context['no_show_count'], 1)
        self.assertEqual(resp.context['past_confirmed'], 2)
        self.assertEqual(len(resp.context['late_cancels']), 1)
        self.assertEqual(resp.context['late_cancels'][0]['lead_minutes'], 30)

    def test_analytics_requires_staff_login(self):
        anon_client = Client()
        resp = anon_client.get(reverse('manage_analytics'))
        self.assertEqual(resp.status_code, 302)
