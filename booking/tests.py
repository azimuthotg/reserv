import json
from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, BookingLog, LineUser, Room


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

        # no-show จริง = booking ที่ถูก auto-cancel (ไม่ check-in) + มี BookingLog
        no_show_booking = Booking.objects.create(
            room=self.room, line_user=self.user2, faculty='คณะ B', group_name='กลุ่ม',
            booking_date=yesterday, start_time='13:00', end_time='14:00',
            attendees='1', status='cancelled',
            cancel_reason='ไม่ check-in ภายในเวลาที่กำหนด (auto-cancel)',
        )
        no_show_start = timezone.make_aware(datetime.combine(yesterday, time(13, 0)))
        no_show_booking.cancelled_at = no_show_start + timedelta(minutes=15)
        no_show_booking.save(update_fields=['cancelled_at'])
        BookingLog.objects.create(booking=no_show_booking, action='auto_cancelled')

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
        self.assertEqual(resp.context['total_cancelled'], 2)   # auto-cancel + late-cancel
        self.assertEqual(resp.context['no_show_count'], 1)     # นับจาก auto_cancelled log
        self.assertEqual(resp.context['no_show_denom'], 3)     # past_confirmed(2) + no_show(1)
        self.assertEqual(resp.context['user_cancelled'], 1)    # total_cancelled − no_show
        self.assertEqual(len(resp.context['late_cancels']), 1)  # auto-cancel ไม่ถูกนับ
        self.assertEqual(resp.context['late_cancels'][0]['lead_minutes'], 30)

    def test_analytics_requires_staff_login(self):
        anon_client = Client()
        resp = anon_client.get(reverse('manage_analytics'))
        self.assertEqual(resp.status_code, 302)


class ThIsoDatetimeFilterTests(TestCase):
    """ฟิลเตอร์ th_iso_datetime — แปลง ISO string จาก API เป็นเวลาไทย พ.ศ."""

    def _fmt(self, value):
        from booking.templatetags.th_filters import th_iso_datetime
        return th_iso_datetime(value)

    def test_utc_z_string_converts_to_thai_time(self):
        # 07:30 UTC = 14:30 เวลาไทย, ปี 2026 = พ.ศ. 2569
        self.assertEqual(self._fmt('2026-06-21T07:30:00Z'), '21 มิถุนายน 2569 14:30')

    def test_offset_string_keeps_local_time(self):
        self.assertEqual(self._fmt('2026-06-21T14:30:00+07:00'), '21 มิถุนายน 2569 14:30')

    def test_empty_returns_dash(self):
        self.assertEqual(self._fmt(''), '—')
        self.assertEqual(self._fmt(None), '—')

    def test_unparseable_string_returned_raw(self):
        self.assertEqual(self._fmt('ไม่ใช่วันที่'), 'ไม่ใช่วันที่')


class ManageExternalRegisterTests(TestCase):
    """ลงทะเบียนสมาชิกถาวรโดยไม่ใส่เลขบัตร — redirect ตาม citizen_id ที่ api gen ให้ (ขึ้นต้น V)"""

    def setUp(self):
        User.objects.create_user(username='staff1', password='pass12345', is_staff=True)
        self.client = Client()
        self.client.login(username='staff1', password='pass12345')

    def test_form_shows_optional_citizen_id(self):
        resp = self.client.get(reverse('manage_external_register'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'ไม่บังคับ')
        self.assertNotContains(resp, 'name="citizen_id" class="form-control" value="" required')

    def test_register_without_citizen_id_redirects_to_generated_id(self):
        from unittest.mock import Mock, patch

        fake = Mock(status_code=201)
        fake.json.return_value = {'success': True, 'member': {'citizen_id': 'V000000000001'}}
        with patch('booking.manage_views._npu_v2_request', return_value=fake):
            resp = self.client.post(reverse('manage_external_register'), data={
                'citizen_id': '', 'first_name': 'นายก', 'last_name': 'สภามหาวิทยาลัย',
            })
        self.assertRedirects(
            resp, reverse('manage_external_detail', kwargs={'citizen_id': 'V000000000001'}),
            fetch_redirect_response=False,
        )
