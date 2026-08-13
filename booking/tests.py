import json
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, BookingLog, HolidayDate, HolidaySyncRun, LineUser, Room


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
        """ห้องอื่นในวันเดียวกันจองได้ ตราบใดที่ไม่ทับเวลากัน (ดู BookingUserOverlapTests)"""
        resp1 = self._post(self.user.line_user_id, self.room_a, self.b_date, '09:00', '10:00')
        self.assertEqual(resp1.status_code, 200, resp1.content)

        resp2 = self._post(self.user.line_user_id, self.room_b, self.b_date, '11:00', '12:00')
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


class BookingUserOverlapTests(TestCase):
    """ผู้ใช้คนเดียวห้ามถือ 2 ห้องพร้อมกัน — ยกเว้นห้องที่ allow_overlap=True"""

    def setUp(self):
        self.room_a = Room.objects.create(
            name='ห้องทดสอบ A', booking_name='ovl-room-a',
            location='ชั้น 1', capacity=10,
            open_time='08:30', close_time='16:30',
        )
        self.room_b = Room.objects.create(
            name='ห้องทดสอบ B', booking_name='ovl-room-b',
            location='ชั้น 1', capacity=10,
            open_time='08:30', close_time='16:30',
        )
        self.shared = Room.objects.create(
            name='โต๊ะประชุมทดสอบ', booking_name='ovl-shared',
            location='ชั้น 1', capacity=13,
            open_time='08:30', close_time='16:30',
            allow_overlap=True,
        )
        self.user = LineUser.objects.create(
            line_user_id='U_ovl_001', display_name='Tester',
            user_ldap='ovl-tester', user_type='นักศึกษา',
            full_name='Overlap Tester', faculty='คณะทดสอบ', is_active=True,
        )
        self.b_date = _next_weekday(date.today())
        self.client = Client()

    def _post(self, room, start, end):
        return self.client.post(
            reverse('create_booking'),
            data=json.dumps({
                'userId': self.user.line_user_id,
                'room': room.booking_name,
                'booking_date': self.b_date.strftime('%Y-%m-%d'),
                'start_time': start,
                'end_time': end,
                'group_name': 'กลุ่มทดสอบ',
                'attendees': 'ผู้ทดสอบ',
            }),
            content_type='application/json',
        )

    def test_overlapping_booking_across_rooms_blocked(self):
        self.assertEqual(self._post(self.room_a, '09:00', '10:00').status_code, 200)

        resp = self._post(self.room_b, '09:30', '10:30')
        self.assertEqual(resp.status_code, 409, resp.content)
        error = resp.json()['error']
        self.assertIn('ห้องทดสอบ A', error)      # บอกว่าชนกับรายการไหน
        self.assertIn('09:00', error)
        self.assertEqual(Booking.objects.filter(room=self.room_b).count(), 0)

    def test_back_to_back_booking_allowed(self):
        """ต่อกันพอดี (10:00-11:00 กับ 11:00-12:00) ไม่ถือว่าทับ"""
        self.assertEqual(self._post(self.room_a, '10:00', '11:00').status_code, 200)
        self.assertEqual(self._post(self.room_b, '11:00', '12:00').status_code, 200)

    def test_allow_overlap_room_as_new_booking_is_exempt(self):
        """จองห้องปกติไว้ก่อน แล้วจองโต๊ะประชุมทับได้"""
        self.assertEqual(self._post(self.room_a, '13:00', '15:00').status_code, 200)
        self.assertEqual(self._post(self.shared, '13:30', '14:30').status_code, 200)

    def test_allow_overlap_room_as_existing_booking_is_exempt(self):
        """จองโต๊ะประชุมไว้ก่อน แล้วจองห้องปกติทับได้"""
        self.assertEqual(self._post(self.shared, '13:00', '15:00').status_code, 200)
        self.assertEqual(self._post(self.room_a, '13:30', '14:30').status_code, 200)

    def test_cancelled_booking_does_not_block_overlap(self):
        self.assertEqual(self._post(self.room_a, '09:00', '10:00').status_code, 200)
        Booking.objects.filter(room=self.room_a).update(status='cancelled')

        self.assertEqual(self._post(self.room_b, '09:30', '10:30').status_code, 200)

    def test_other_user_overlap_not_affected(self):
        other = LineUser.objects.create(
            line_user_id='U_ovl_002', display_name='Tester2',
            user_ldap='ovl-tester2', user_type='นักศึกษา',
            full_name='Overlap Tester 2', faculty='คณะทดสอบ', is_active=True,
        )
        self.assertEqual(self._post(self.room_a, '09:00', '10:00').status_code, 200)

        resp = self.client.post(
            reverse('create_booking'),
            data=json.dumps({
                'userId': other.line_user_id,
                'room': self.room_b.booking_name,
                'booking_date': self.b_date.strftime('%Y-%m-%d'),
                'start_time': '09:00', 'end_time': '10:00',
                'group_name': 'กลุ่มทดสอบ', 'attendees': 'ผู้ทดสอบ',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200, resp.content)


class OnlineRoomRoundTests(TestCase):
    """บริการออนไลน์ (is_online) จองได้ 3 รอบ/วัน — เช้ามืด / กลางวัน / กลางคืน"""

    def setUp(self):
        self.online = Room.objects.create(
            name='Canva ทดสอบ', booking_name='rnd-online',
            location='ออนไลน์', capacity=2,
            open_time='00:00', close_time='23:59',
            is_online=True,
        )
        self.onsite = Room.objects.create(
            name='ห้องจริงทดสอบ', booking_name='rnd-onsite',
            location='ชั้น 1', capacity=10,
            open_time='08:30', close_time='16:30',
        )
        self.user = LineUser.objects.create(
            line_user_id='U_rnd_001', display_name='Tester',
            user_ldap='rnd-tester', user_type='นักศึกษา',
            full_name='Round Tester', faculty='คณะทดสอบ', is_active=True,
        )
        self.b_date = _next_weekday(date.today())
        self.client = Client()

    def _post(self, room, start, end, b_date=None):
        return self.client.post(
            reverse('create_booking'),
            data=json.dumps({
                'userId': self.user.line_user_id,
                'room': room.booking_name,
                'booking_date': (b_date or self.b_date).strftime('%Y-%m-%d'),
                'start_time': start,
                'end_time': end,
                'group_name': 'กลุ่มทดสอบ',
                'attendees': 'ผู้ทดสอบ',
            }),
            content_type='application/json',
        )

    def test_three_rounds_same_day_allowed(self):
        """เช้ามืด + กลางวัน + กลางคืน = 3 สิทธิ์แยกกัน"""
        self.assertEqual(self._post(self.online, '05:00', '08:00').status_code, 200)
        self.assertEqual(self._post(self.online, '10:00', '12:00').status_code, 200)
        self.assertEqual(self._post(self.online, '19:00', '21:00').status_code, 200)
        self.assertEqual(Booking.objects.filter(room=self.online, status='confirmed').count(), 3)

    def test_second_booking_same_round_blocked(self):
        self.assertEqual(self._post(self.online, '18:00', '19:00').status_code, 200)

        resp = self._post(self.online, '21:00', '22:00')
        self.assertEqual(resp.status_code, 409, resp.content)
        self.assertIn('1 ครั้งต่อรอบ', resp.json()['error'])

    def test_booking_across_rounds_rejected(self):
        """16:00-18:30 คร่อมรอบกลางวันกับกลางคืน — นับสิทธิ์ไม่ได้ จึงปฏิเสธ"""
        resp = self._post(self.online, '16:00', '18:30')
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn('คร่อมรอบ', resp.json()['error'])

    def test_round_boundary_belongs_to_earlier_round(self):
        """06:00-08:30 อยู่ในรอบเช้ามืด ส่วน 08:30-10:00 อยู่รอบกลางวัน — จองได้ทั้งคู่"""
        self.assertEqual(self._post(self.online, '06:00', '08:30').status_code, 200)
        self.assertEqual(self._post(self.online, '08:30', '10:00').status_code, 200)

    def test_online_room_bookable_on_weekend(self):
        """เสาร์-อาทิตย์ไม่ถูกตัดเวลาตามอาคาร (ปกติระบบบังคับ 09:00-17:00)"""
        saturday = self.b_date
        while saturday.weekday() != 5:
            saturday += timedelta(days=1)

        self.assertEqual(self._post(self.online, '20:00', '22:00', saturday).status_code, 200)

    def test_online_room_bookable_on_holiday(self):
        from .models import HolidayDate
        HolidayDate.objects.create(date=self.b_date, description='วันหยุดทดสอบ', is_active=True)

        self.assertEqual(self._post(self.online, '19:00', '20:00').status_code, 200)

        resp = self._post(self.onsite, '10:00', '11:00')
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn('วันหยุดทดสอบ', resp.json()['error'])

    def test_day_round_disabled_blocks_daytime_only(self):
        """ห้องที่ปิดรอบกลางวัน (Netflix) จองเช้ามืด/กลางคืนได้ แต่กลางวันไม่ได้"""
        self.online.day_round_enabled = False
        self.online.save(update_fields=['day_round_enabled'])

        self.assertEqual(self._post(self.online, '06:00', '08:00').status_code, 200)
        self.assertEqual(self._post(self.online, '19:00', '21:00').status_code, 200)

        resp = self._post(self.online, '10:00', '12:00')
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn('นอกเวลาราชการ', resp.json()['error'])

    def test_onsite_room_night_booking_rejected(self):
        """ห้องจริงยังจองนอกเวลาไม่ได้เหมือนเดิม"""
        resp = self._post(self.onsite, '19:00', '20:00')
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn('ช่วงเปิดบริการ', resp.json()['error'])


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


class ExternalAccessDayTests(TestCase):
    """หน้า day (/external/): บังคับชื่อ-สกุล, เลขบัตรเป็น optional"""

    def test_form_citizen_id_not_required(self):
        resp = self.client.get(reverse('external_access'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'ไม่บังคับ')
        self.assertNotContains(resp, 'placeholder="x-xxxx-xxxxx-xx-x" required')

    def test_issue_without_citizen_id_omits_key(self):
        from unittest.mock import Mock, patch

        fake = Mock(status_code=200)
        fake.json.return_value = {
            'access_code': '1234567890', 'valid_date': '2026-07-16',
            'member': {'first_name': 'สมชาย', 'last_name': 'ใจดี'},
        }
        with patch('booking.views._npu_v2_request', return_value=fake) as mock_req:
            resp = self.client.post(reverse('external_access'), data={
                'first_name': 'สมชาย', 'last_name': 'ใจดี', 'citizen_id': '',
            })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '1234567890')
        sent = mock_req.call_args.kwargs['json']
        self.assertNotIn('citizen_id', sent)
        self.assertEqual(sent['first_name'], 'สมชาย')

    def test_missing_name_rejected_before_api(self):
        from unittest.mock import patch

        with patch('booking.views._npu_v2_request') as mock_req:
            resp = self.client.post(reverse('external_access'), data={
                'first_name': '', 'last_name': 'ใจดี', 'citizen_id': '',
            })
        self.assertContains(resp, 'กรุณากรอกชื่อและนามสกุล')
        mock_req.assert_not_called()

    def test_bad_citizen_id_when_provided_rejected(self):
        from unittest.mock import patch

        with patch('booking.views._npu_v2_request') as mock_req:
            resp = self.client.post(reverse('external_access'), data={
                'first_name': 'สมชาย', 'last_name': 'ใจดี', 'citizen_id': '123',
            })
        self.assertContains(resp, 'ต้องเป็นตัวเลข 13 หลัก')
        mock_req.assert_not_called()


class ManageExternalEditTests(TestCase):
    """หน้าแก้ไขชื่อ-สกุลสมาชิกถาวร /manage/external/<id>/edit/

    reserv ไม่เก็บข้อมูลสมาชิกเอง — view เป็น proxy ไป `/v2/external/permanent/<id>/update/`
    จุดที่ต้องกันพลาดที่สุดคือ **ไม่เลือกไฟล์รูป = ต้องไม่ส่ง files ไปเลย** ไม่งั้นรูปเดิมของสมาชิกถูกทับ
    """

    CID = '1234567890123'

    def setUp(self):
        User.objects.create_user(username='staff1', password='pass12345', is_staff=True)
        self.client = Client()
        self.client.login(username='staff1', password='pass12345')
        self.url = reverse('manage_external_edit', kwargs={'citizen_id': self.CID})

    def _member_resp(self):
        from unittest.mock import Mock

        fake = Mock(status_code=200)
        fake.json.return_value = {
            'citizen_id': self.CID, 'first_name': 'สมชาย',
            'last_name': 'ใจดี', 'has_photo': True,
        }
        return fake

    def test_requires_staff_login(self):
        from unittest.mock import patch

        self.client.logout()
        with patch('booking.manage_views._npu_v2_request') as mock_req:
            resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn(reverse('manage_external_edit', kwargs={'citizen_id': self.CID}),
                         resp['Location'])
        mock_req.assert_not_called()

    def test_get_prefills_current_name_from_api(self):
        from unittest.mock import patch

        with patch('booking.manage_views._npu_v2_request',
                   return_value=self._member_resp()) as mock_req:
            resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'value="สมชาย"')
        self.assertContains(resp, 'value="ใจดี"')
        self.assertContains(resp, 'เว้นว่างไว้ = ใช้รูปเดิม')
        self.assertEqual(mock_req.call_args.args[0], 'GET')

    def test_post_without_photo_does_not_send_files(self):
        from unittest.mock import Mock, patch

        with patch('booking.manage_views._npu_v2_request',
                   return_value=Mock(status_code=200)) as mock_req:
            resp = self.client.post(self.url, data={
                'first_name': 'สมชาย', 'last_name': 'ใจงาม',
            })
        self.assertRedirects(
            resp, reverse('manage_external_detail', kwargs={'citizen_id': self.CID}),
            fetch_redirect_response=False,
        )
        kwargs = mock_req.call_args.kwargs
        self.assertIsNone(kwargs['files'])          # ไม่ส่ง files = api ใช้รูปเดิม
        self.assertEqual(kwargs['data']['last_name'], 'ใจงาม')

    def test_post_with_photo_sends_file_bytes(self):
        from unittest.mock import Mock, patch

        from django.core.files.uploadedfile import SimpleUploadedFile

        photo = SimpleUploadedFile('new.jpg', b'\xff\xd8\xff-fake-jpeg', content_type='image/jpeg')
        with patch('booking.manage_views._npu_v2_request',
                   return_value=Mock(status_code=200)) as mock_req:
            self.client.post(self.url, data={
                'first_name': 'สมชาย', 'last_name': 'ใจดี', 'photo': photo,
            })
        sent = mock_req.call_args.kwargs['files']['photo']
        self.assertEqual(sent[0], 'new.jpg')
        self.assertEqual(sent[1], b'\xff\xd8\xff-fake-jpeg')   # อ่านเป็น bytes เพื่อให้ retry ได้

    def test_post_404_redirects_to_list(self):
        from unittest.mock import Mock, patch

        with patch('booking.manage_views._npu_v2_request', return_value=Mock(status_code=404)):
            resp = self.client.post(self.url, data={
                'first_name': 'สมชาย', 'last_name': 'ใจดี',
            })
        self.assertRedirects(resp, reverse('manage_external_list'),
                             fetch_redirect_response=False)

    def test_post_api_unreachable_redisplays_form_with_input(self):
        from unittest.mock import patch

        with patch('booking.manage_views._npu_v2_request', return_value=None):
            resp = self.client.post(self.url, data={
                'first_name': 'สมชาย', 'last_name': 'ใจงาม',
            })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'เชื่อมต่อ NPU API ไม่ได้')
        self.assertContains(resp, 'value="ใจงาม"')       # ไม่ล้างสิ่งที่ staff พิมพ์ทิ้ง

    def test_get_404_redirects_to_list(self):
        from unittest.mock import Mock, patch

        with patch('booking.manage_views._npu_v2_request', return_value=Mock(status_code=404)):
            resp = self.client.get(self.url)
        self.assertRedirects(resp, reverse('manage_external_list'),
                             fetch_redirect_response=False)


ICS_SAMPLE = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260812
DTEND;VALUE=DATE:20260813
SUMMARY:วันเฉลิมพระชนมพรรษาสมเด็จพระนางเจ้าสิริกิติ์ พระบรมราชินีนาถ
 พระบรมราชชนนีพันปีหลวง
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260214
DTEND;VALUE=DATE:20260215
SUMMARY:วันวาเลนไทน์
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260413
DTEND;VALUE=DATE:20260416
SUMMARY:วันสงกรานต์
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20270101
DTEND;VALUE=DATE:20270102
SUMMARY:วันขึ้นปีใหม่
END:VEVENT
END:VCALENDAR
"""


class HolidayFeedParseTests(TestCase):
    """แกะ iCal — ฟีดจริงมีบรรทัดพับ, event หลายวัน และวันที่ไม่ใช่วันหยุดราชการปนมา"""

    def test_folded_summary_is_joined(self):
        from .holiday_feed import parse_ics

        events = dict(parse_ics(ICS_SAMPLE))
        self.assertIn('พระบรมราชชนนีพันปีหลวง', events[date(2026, 8, 12)])
        self.assertNotIn('\n', events[date(2026, 8, 12)])

    def test_multi_day_event_expands_to_each_day(self):
        from .holiday_feed import parse_ics

        days = [d for d, _ in parse_ics(ICS_SAMPLE)]
        for day in (13, 14, 15):
            self.assertIn(date(2026, 4, day), days)
        self.assertNotIn(date(2026, 4, 16), days)   # DTEND ของ iCal ไม่นับวันสุดท้าย

    def test_observances_are_filtered_out(self):
        from unittest.mock import Mock, patch

        from .holiday_feed import fetch_holidays

        fake = Mock(status_code=200, content=ICS_SAMPLE.encode('utf-8'))
        with patch('booking.holiday_feed.requests.get', return_value=fake):
            got = dict(fetch_holidays(year=2026))
        self.assertIn(date(2026, 8, 12), got)
        self.assertNotIn(date(2026, 2, 14), got)     # วาเลนไทน์ ไม่ใช่วันหยุดราชการ

    def test_year_filter(self):
        from unittest.mock import Mock, patch

        from .holiday_feed import fetch_holidays

        fake = Mock(status_code=200, content=ICS_SAMPLE.encode('utf-8'))
        with patch('booking.holiday_feed.requests.get', return_value=fake):
            got = dict(fetch_holidays(year=2027))
        self.assertEqual(list(got), [date(2027, 1, 1)])

    def test_date_range_filter_keeps_window_within_one_year(self):
        """ค่าเริ่มต้นของ sync_holidays ดึงล่วงหน้าไม่เกิน 1 ปี (ผู้ใช้กำหนด 2026-08-09)"""
        from unittest.mock import Mock, patch

        from .holiday_feed import fetch_holidays

        fake = Mock(status_code=200, content=ICS_SAMPLE.encode('utf-8'))
        with patch('booking.holiday_feed.requests.get', return_value=fake):
            got = dict(fetch_holidays(start=date(2026, 4, 1), end=date(2026, 12, 31)))
        self.assertIn(date(2026, 4, 13), got)
        self.assertIn(date(2026, 8, 12), got)
        self.assertNotIn(date(2027, 1, 1), got)      # เกินหน้าต่าง

    def test_http_error_raises(self):
        from unittest.mock import Mock, patch

        from .holiday_feed import HolidayFeedError, fetch_holidays

        with patch('booking.holiday_feed.requests.get', return_value=Mock(status_code=503)):
            with self.assertRaises(HolidayFeedError):
                fetch_holidays(year=2026)


class HolidaySyncTests(TestCase):
    """ดึงวันหยุดเข้าระบบ — ต้องเป็นฉบับร่างเสมอ และห้ามทับของที่เจ้าหน้าที่กรอกเอง"""

    def setUp(self):
        from unittest.mock import Mock

        self.fake = Mock(status_code=200, content=ICS_SAMPLE.encode('utf-8'))
        User.objects.create_user(username='admin1', password='pass12345',
                                 is_staff=True, is_superuser=True)
        self.client = Client()
        self.client.login(username='admin1', password='pass12345')

    def _sync(self, year=2026):
        from unittest.mock import patch

        with patch('booking.holiday_feed.requests.get', return_value=self.fake):
            return self.client.post(reverse('manage_holidays_sync'), data={'year': year})

    def test_imported_rows_are_inactive_drafts(self):
        self._sync()
        h = HolidayDate.objects.get(date=date(2026, 8, 12))
        self.assertFalse(h.is_active)            # ต้องไม่บล็อกการจองจนกว่าคนจะยืนยัน
        self.assertEqual(h.source, HolidayDate.SOURCE_AUTO)

    def test_manual_row_is_never_overwritten(self):
        HolidayDate.objects.create(date=date(2026, 8, 12), description='ปิดตามมติสำนักฯ',
                                   is_active=True, source=HolidayDate.SOURCE_MANUAL)
        self._sync()
        h = HolidayDate.objects.get(date=date(2026, 8, 12))
        self.assertEqual(h.description, 'ปิดตามมติสำนักฯ')
        self.assertTrue(h.is_active)
        self.assertEqual(h.source, HolidayDate.SOURCE_MANUAL)

    def test_sync_twice_creates_no_duplicates(self):
        self._sync()
        first = HolidayDate.objects.count()
        self._sync()
        self.assertEqual(HolidayDate.objects.count(), first)

    def _book_on(self, holiday_date, key):
        """จองวันที่กำหนด — ใช้วันหยุดที่ยังไม่ถึงและเป็นวันธรรมดา เพื่อไม่ให้ติดกติกาอื่น"""
        room = Room.objects.create(
            name='ห้องทดสอบ', booking_name=key, location='x', capacity=2,
            open_time=time(8, 30), close_time=time(16, 30), is_active=True,
        )
        user = LineUser.objects.create(line_user_id=f'U-{key}', user_ldap=key,
                                       display_name='ทดสอบ', is_active=True)
        return self.client.post(reverse('create_booking'), data=json.dumps({
            'userId': user.line_user_id,
            'room': room.booking_name,
            'booking_date': holiday_date.strftime('%Y-%m-%d'),
            'start_time': '09:00', 'end_time': '10:00',
            'group_name': 'กลุ่มทดสอบ', 'attendees': 'ผู้ทดสอบ',
        }), content_type='application/json')

    def _future_weekday_holiday(self, source, is_active):
        d = _next_weekday(date.today() + timedelta(days=3))
        HolidayDate.objects.update_or_create(
            date=d, defaults={'description': 'วันหยุดทดสอบ',
                              'is_active': is_active, 'source': source})
        return d

    def test_draft_holiday_does_not_block_booking(self):
        """ฉบับร่างต้องไม่มีผลกับการจอง — เป็นหัวใจของการออกแบบนี้"""
        d = self._future_weekday_holiday(HolidayDate.SOURCE_AUTO, is_active=False)
        resp = self._book_on(d, 't1')
        self.assertEqual(resp.status_code, 200, resp.content.decode())

    def test_activated_holiday_blocks_booking(self):
        d = self._future_weekday_holiday(HolidayDate.SOURCE_AUTO, is_active=True)
        resp = self._book_on(d, 't2')
        self.assertEqual(resp.status_code, 400)

    def test_sync_requires_admin(self):
        from unittest.mock import patch

        self.client.logout()
        with patch('booking.holiday_feed.requests.get') as mock_get:
            resp = self.client.post(reverse('manage_holidays_sync'), data={'year': 2026})
        self.assertEqual(resp.status_code, 302)
        mock_get.assert_not_called()

    def test_dashboard_warns_about_pending_holiday_with_bookings(self):
        from unittest.mock import patch

        HolidayDate.objects.create(date=date.today() + timedelta(days=3),
                                   description='วันหยุดทดสอบ', is_active=False,
                                   source=HolidayDate.SOURCE_AUTO)
        with patch('booking.manage_views._npu_v2_request', return_value=None):
            resp = self.client.get(reverse('manage_dashboard'))
        self.assertContains(resp, 'ยังไม่ได้ตรวจ')
        self.assertContains(resp, 'วันหยุดทดสอบ')


class ManageHolidaysPageTests(TestCase):
    """หน้า /manage/holidays/ — เรียงแบบไทม์ไลน์รอบวันนี้ และไฮไลต์วันหยุดถัดไป"""

    def setUp(self):
        User.objects.create_user(username='admin2', password='pass12345',
                                 is_staff=True, is_superuser=True)
        self.client = Client()
        self.client.login(username='admin2', password='pass12345')
        self.today = date.today()

    def _mk(self, delta_days, desc, is_active=True, source=HolidayDate.SOURCE_MANUAL):
        return HolidayDate.objects.create(
            date=self.today + timedelta(days=delta_days), description=desc,
            is_active=is_active, source=source)

    def _page(self):
        return self.client.get(reverse('manage_holidays'), {'year': self.today.year})

    def test_upcoming_on_top_past_below(self):
        self._mk(-20, 'ผ่านมานาน')
        self._mk(-2, 'เพิ่งผ่าน')
        self._mk(5, 'ใกล้ถึง')
        self._mk(40, 'อีกนาน')
        rows = list(self._page().context['holidays'])
        self.assertEqual([h.description for h in rows],
                         ['ใกล้ถึง', 'อีกนาน', 'เพิ่งผ่าน', 'ผ่านมานาน'])

    def test_upcoming_count_marks_the_divider(self):
        self._mk(-1, 'ผ่าน')
        self._mk(3, 'ยังไม่ถึง')
        resp = self._page()
        self.assertEqual(resp.context['upcoming_count'], 1)
        self.assertContains(resp, 'ผ่านมาแล้ว ──')

    def test_next_active_is_highlighted_not_the_draft(self):
        """ฉบับร่างที่ใกล้กว่าไม่ใช่ 'วันหยุดถัดไป' เพราะยังไม่บล็อกการจอง"""
        draft = self._mk(2, 'ฉบับร่างใกล้กว่า', is_active=False,
                         source=HolidayDate.SOURCE_AUTO)
        real = self._mk(9, 'ปิดจริง', is_active=True)
        resp = self._page()
        self.assertEqual(resp.context['next_active'].pk, real.pk)
        flags = {h.pk: h.is_next for h in resp.context['holidays'] if hasattr(h, 'is_next')}
        self.assertTrue(flags[real.pk])
        self.assertFalse(flags[draft.pk])
        self.assertContains(resp, 'หยุดถัดไป · อีก 9 วัน')

    def test_no_upcoming_shows_no_divider(self):
        self._mk(-3, 'ผ่านมาแล้ว')
        resp = self._page()
        self.assertEqual(resp.context['upcoming_count'], 0)
        self.assertNotContains(resp, 'ผ่านมาแล้ว ──')

    def test_next_holiday_in_another_year_is_announced(self):
        """เปิดดูปีนี้แต่วันหยุดถัดไปอยู่ปีหน้า ต้องบอกให้ไปดูแท็บปีนั้น"""
        far = HolidayDate.objects.create(
            date=date(self.today.year + 1, 1, 1), description='วันขึ้นปีใหม่',
            is_active=True, source=HolidayDate.SOURCE_MANUAL)
        resp = self._page()
        self.assertEqual(resp.context['next_active'].pk, far.pk)
        self.assertContains(resp, 'กดแท็บปีนั้นเพื่อดู')


class VmGatewayButtonTests(TestCase):
    """ปุ่ม "เข้าใช้งาน" ของห้องออนไลน์ — ชี้ไป VM Gateway ไม่ใช่หน้าควบคุมอุปกรณ์

    ห้องออนไลน์ไม่มีอุปกรณ์ IoT ผูกอยู่ ปุ่ม "ควบคุมอุปกรณ์" จึงไม่มีความหมาย
    URL ปลายทางเป็นสัญญาข้ามระบบกับทีม VM Gateway ต้องมาจาก settings ไม่ใช่ hardcode
    """

    def setUp(self):
        self.online = Room.objects.create(
            name='Canva Pro ทดสอบ', booking_name='vm-test', location='ออนไลน์', capacity=1,
            open_time=time(0, 0), close_time=time(23, 59), is_active=True, is_online=True,
        )
        self.physical = Room.objects.create(
            name='ห้องจริงทดสอบ', booking_name='phys-test', location='ชั้น 3', capacity=4,
            open_time=time(8, 30), close_time=time(16, 30), is_active=True, is_online=False,
        )
        self.user = LineUser.objects.create(line_user_id='U-vm', user_ldap='vmtest',
                                            display_name='ทดสอบ', is_active=True)

    def _my_bookings(self, room):
        Booking.objects.create(
            room=room, line_user=self.user, booking_date=date.today(),
            start_time=time(10, 0), end_time=time(11, 0),
            group_name='ทดสอบ', attendees='ทดสอบ', status='confirmed',
        )
        resp = self.client.get(reverse('my_bookings'), {'userId': self.user.line_user_id})
        self.assertEqual(resp.status_code, 200)
        return json.loads(resp.content)['bookings'][0]

    def test_api_reports_is_online(self):
        """หน้าแรกเลือกปุ่มจากค่านี้ — ถ้าหายไปปุ่มจะกลายเป็นปุ่มควบคุมอุปกรณ์ทั้งหมด"""
        self.assertTrue(self._my_bookings(self.online)['is_online'])

    def test_api_reports_physical_room_as_not_online(self):
        self.assertFalse(self._my_bookings(self.physical)['is_online'])

    def test_landing_exposes_gateway_settings(self):
        resp = self.client.get(reverse('landing'))
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn(settings.VM_GATEWAY_URL, body)
        self.assertIn(f'const VM_EARLY_MIN       = {settings.VM_GATEWAY_EARLY_MINUTES}', body)

    def test_gateway_url_is_https(self):
        """ช่องทางเดิมเป็น http ซึ่งส่งรหัสผ่านเป็นข้อความธรรมดา — ห้ามถอยกลับไปใช้"""
        self.assertTrue(settings.VM_GATEWAY_URL.startswith('https://'),
                        f'VM_GATEWAY_URL ต้องเป็น https — ได้ {settings.VM_GATEWAY_URL}')

    def test_room_control_link_not_hardcoded_for_online_rooms(self):
        """กันไม่ให้ใครเผลอเอา URL ของ Gateway ไป hardcode ไว้ในเทมเพลต"""
        import os

        path = os.path.join(settings.BASE_DIR, 'booking', 'templates', 'booking', 'landing.html')
        with open(path, encoding='utf-8') as fh:
            source = fh.read()
        self.assertNotIn('arcvm.npu.ac.th', source)
        self.assertIn('{{ vm_gateway_url }}', source)


class TemplateCommentTests(TestCase):
    """กันคอมเมนต์นักพัฒนาหลุดออกไปแสดงบนหน้าเว็บ

    `{# ... #}` ของ Django **ใช้ได้บรรทัดเดียวเท่านั้น** เขียนคร่อมหลายบรรทัดจะไม่ถูกมองว่า
    เป็นคอมเมนต์ แล้วพ่นออกมาเป็นข้อความให้ผู้ใช้เห็น — เกิดขึ้นจริงบน production 2026-08-10
    ทุกหน้า `/room/<key>/` โชว์ข้อความ "เพดานจริงมาจาก service_hours.MAX_BOOKING_MINUTES…"
    อยู่กลางหน้า หลายบรรทัดต้องใช้ `{% comment %}` แทน
    """

    def test_no_multiline_hash_comments_in_templates(self):
        import os
        import re

        from django.conf import settings

        root = os.path.join(settings.BASE_DIR, 'booking', 'templates')
        offenders = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if not name.endswith('.html'):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding='utf-8') as fh:
                    for lineno, line in enumerate(fh, start=1):
                        # เปิด {# แล้วไม่ปิด #} ในบรรทัดเดียวกัน = คอมเมนต์หลายบรรทัด
                        if re.search(r'\{#(?!.*#\})', line):
                            offenders.append(f'{os.path.relpath(path, root)}:{lineno}')

        self.assertEqual(
            offenders, [],
            'พบคอมเมนต์ {# #} ที่คร่อมหลายบรรทัด ซึ่งจะแสดงบนหน้าเว็บจริง '
            'ให้เปลี่ยนเป็น {% comment %}...{% endcomment %} ที่: ' + ', '.join(offenders))

    def test_room_detail_page_has_no_developer_note(self):
        """ตรวจที่หน้าจริงด้วย — ไม่ใช่แค่ไวยากรณ์ในไฟล์"""
        room = Room.objects.create(
            name='ห้องทดสอบคอมเมนต์', booking_name='comment-check', location='x', capacity=1,
            open_time=time(8, 30), close_time=time(16, 30), is_active=True,
        )
        resp = self.client.get(reverse('room_detail', args=[room.booking_name]))
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertNotIn('MAX_BOOKING_MINUTES', body)
        self.assertNotIn('{#', body)


class HolidayFreshnessTests(TestCase):
    """เตือนเมื่อ "ไม่มีใครดึงข้อมูลวันหยุดมานาน"

    แถบเตือนฉบับร่างเดิมขึ้นได้เฉพาะเมื่อมีแถวฉบับร่างอยู่จริง แดชบอร์ดที่เงียบเพราะ
    ตรวจครบแล้ว จึงแยกไม่ออกจากที่เงียบเพราะไม่มีใครดึงข้อมูลมาเลย — ชุดนี้คุมส่วนที่
    ทำให้ "เงียบ = ปลอดภัยจริง"
    """

    def setUp(self):
        from unittest.mock import Mock

        self.fake = Mock(status_code=200, content=ICS_SAMPLE.encode('utf-8'))
        User.objects.create_user(username='admin3', password='pass12345',
                                 is_staff=True, is_superuser=True)
        self.client = Client()
        self.client.login(username='admin3', password='pass12345')
        self.today = date.today()

    def _sync(self, year=2026):
        from unittest.mock import patch

        with patch('booking.holiday_feed.requests.get', return_value=self.fake):
            return self.client.post(reverse('manage_holidays_sync'), data={'year': year})

    def _dashboard(self):
        from unittest.mock import patch

        with patch('booking.manage_views._npu_v2_request', return_value=None):
            return self.client.get(reverse('manage_dashboard'))

    def _age_last_run(self, days):
        """auto_now_add เขียนทับค่าที่ส่งมา ต้องดันเวลาย้อนหลังผ่าน queryset update"""
        HolidaySyncRun.objects.update(synced_at=timezone.now() - timedelta(days=days))

    def _far_horizon(self):
        HolidayDate.objects.create(date=self.today + timedelta(days=200),
                                   description='วันหยุดไกล', is_active=True,
                                   source=HolidayDate.SOURCE_MANUAL)

    # ── บันทึกการดึง ──────────────────────────────────────────────────────────

    def test_button_sync_records_a_run(self):
        self._sync()
        self.assertEqual(HolidaySyncRun.objects.count(), 1)
        self.assertEqual(HolidaySyncRun.objects.first().trigger,
                         HolidaySyncRun.TRIGGER_BUTTON)

    def test_sync_with_no_new_days_still_records_a_run(self):
        """หัวใจของฟีเจอร์ — "ดึงแล้วไม่เจอวันใหม่" ต้องไม่ดูเหมือน "ไม่มีใครดึงเลย" """
        self._sync()
        self._sync()                                   # รอบสองไม่มีวันใหม่แน่นอน
        self.assertEqual(HolidaySyncRun.objects.count(), 2)
        self.assertEqual(HolidaySyncRun.objects.first().created_count, 0)

    def test_failed_fetch_records_nothing(self):
        from unittest.mock import Mock, patch

        with patch('booking.holiday_feed.requests.get',
                   return_value=Mock(status_code=503)):
            self.client.post(reverse('manage_holidays_sync'), data={'year': 2026})
        self.assertEqual(HolidaySyncRun.objects.count(), 0)

    def test_command_records_a_run(self):
        from io import StringIO
        from unittest.mock import patch

        from django.core.management import call_command

        with patch('booking.holiday_feed.requests.get', return_value=self.fake):
            call_command('sync_holidays', '--year', '2026', stdout=StringIO())
        self.assertEqual(HolidaySyncRun.objects.count(), 1)
        self.assertEqual(HolidaySyncRun.objects.first().trigger,
                         HolidaySyncRun.TRIGGER_COMMAND)

    def test_dry_run_records_nothing(self):
        from io import StringIO
        from unittest.mock import patch

        from django.core.management import call_command

        with patch('booking.holiday_feed.requests.get', return_value=self.fake):
            call_command('sync_holidays', '--year', '2026', '--dry-run', stdout=StringIO())
        self.assertEqual(HolidaySyncRun.objects.count(), 0)

    # ── สถานะข้อมูล ───────────────────────────────────────────────────────────

    def test_never_synced_is_stale(self):
        self.assertTrue(HolidaySyncRun.data_status()['is_stale'])

    def test_fresh_sync_with_far_horizon_is_quiet(self):
        self._far_horizon()
        HolidaySyncRun.objects.create()
        status = HolidaySyncRun.data_status()
        self.assertFalse(status['needs_attention'])

    def test_old_sync_is_stale(self):
        self._far_horizon()
        HolidaySyncRun.objects.create()
        self._age_last_run(60)
        status = HolidaySyncRun.data_status()
        self.assertTrue(status['is_stale'])
        self.assertEqual(status['days_since'], 60)

    def test_recent_sync_is_not_stale(self):
        self._far_horizon()
        HolidaySyncRun.objects.create()
        self._age_last_run(20)
        self.assertFalse(HolidaySyncRun.data_status()['is_stale'])

    def test_short_horizon_warns_even_after_fresh_sync(self):
        """ดึงมาสด ๆ แต่ข้อมูลครอบไปข้างหน้าไม่ถึง 2 เดือน ก็ยังต้องเตือน"""
        HolidayDate.objects.create(date=self.today + timedelta(days=10),
                                   description='วันหยุดใกล้', is_active=True,
                                   source=HolidayDate.SOURCE_MANUAL)
        HolidaySyncRun.objects.create()
        status = HolidaySyncRun.data_status()
        self.assertFalse(status['is_stale'])
        self.assertTrue(status['horizon_short'])
        self.assertTrue(status['needs_attention'])

    # ── แถบเตือนบนแดชบอร์ด ────────────────────────────────────────────────────

    def test_dashboard_warns_when_never_synced(self):
        resp = self._dashboard()
        self.assertContains(resp, 'ยังไม่เคยดึงปฏิทินวันหยุดเข้าระบบเลย')

    def test_dashboard_warns_when_sync_is_old(self):
        self._far_horizon()
        HolidaySyncRun.objects.create()
        self._age_last_run(90)
        resp = self._dashboard()
        self.assertContains(resp, 'ข้อมูลวันหยุดอาจไม่เป็นปัจจุบัน')
        self.assertContains(resp, '90 วันที่แล้ว')

    def test_dashboard_quiet_when_data_is_fresh(self):
        """ต้องไม่ขึ้นเตือนตอนทุกอย่างเรียบร้อย ไม่งั้นเจ้าหน้าที่จะเลิกอ่านแถบเตือน"""
        self._far_horizon()
        HolidaySyncRun.objects.create()
        resp = self._dashboard()
        self.assertNotContains(resp, 'ข้อมูลวันหยุดอาจไม่เป็นปัจจุบัน')

    def test_holidays_page_shows_last_sync(self):
        self._far_horizon()
        HolidaySyncRun.objects.create()
        self._age_last_run(3)
        resp = self.client.get(reverse('manage_holidays'))
        self.assertContains(resp, 'ดึงปฏิทินวันหยุดครั้งล่าสุด')
        self.assertContains(resp, '3 วันที่แล้ว')


class ProfileCacheInvalidationTests(TestCase):
    """cache profile ต้องไม่ค้างข้ามเจ้าของบัญชี

    เคสจริง 2026-08-13: นักศึกษาแจ้งว่า "รหัสถูก แต่ชื่อผิด" — เพราะ /api/check-user/
    คืน userLdap สดจาก api แต่คืน full_name จาก LineUser ที่ cache ไว้ 30 วัน
    ลบการผูกที่ api แล้วผูกใหม่ก็ไม่หาย เพราะ cache ฝั่ง reserv ไม่ถูกแตะเลย
    """

    def setUp(self):
        self.lu = LineUser.objects.create(
            line_user_id='Utest-profile-cache',
            display_name='nong',
            user_ldap='650000000001',
            user_type='นักศึกษา',
            full_name='นางสาวชื่อ เดิม',
            faculty='คณะเดิม',
            department='สาขาเดิม',
            profile_updated_at=timezone.now(),
        )

    def _std_profile(self):
        return {
            'prefix_name':     'นาย',
            'student_name':    'ชื่อ',
            'student_surname': 'ใหม่',
            'faculty_name':    'คณะใหม่',
            'program_name':    'สาขาใหม่',
        }

    def test_ldap_change_invalidates_cache(self):
        from unittest.mock import patch

        from .views import _get_or_refresh_line_user

        with patch('booking.views._fetch_npu_profile',
                   return_value=self._std_profile()) as mock_fetch:
            lu = _get_or_refresh_line_user(
                'Utest-profile-cache', 'nong', '650000000002', 'นักศึกษา')

        mock_fetch.assert_called_once_with('650000000002', 'นักศึกษา')
        self.assertEqual(lu.user_ldap, '650000000002')
        self.assertEqual(lu.full_name, 'นายชื่อ ใหม่')
        self.assertEqual(lu.faculty, 'คณะใหม่')

    def test_same_ldap_still_uses_cache(self):
        """ของเดิมต้องไม่ถูกกระทบ — ไม่งั้นทุกครั้งที่เปิดหน้าจะยิง api ใหม่หมด"""
        from unittest.mock import patch

        from .views import _get_or_refresh_line_user

        with patch('booking.views._fetch_npu_profile') as mock_fetch:
            lu = _get_or_refresh_line_user(
                'Utest-profile-cache', 'nong', '650000000001', 'นักศึกษา')

        mock_fetch.assert_not_called()
        self.assertEqual(lu.full_name, 'นางสาวชื่อ เดิม')

    def test_force_refreshes_even_when_ldap_unchanged(self):
        """หน้า register ผูกบัญชีใหม่ → ต้องดึงชื่อสดเสมอ แม้เป็นรหัสเดิม"""
        from unittest.mock import patch

        from .views import _get_or_refresh_line_user

        with patch('booking.views._fetch_npu_profile',
                   return_value=self._std_profile()) as mock_fetch:
            lu = _get_or_refresh_line_user(
                'Utest-profile-cache', 'nong', '650000000001', 'นักศึกษา',
                force=True)

        mock_fetch.assert_called_once()
        self.assertEqual(lu.full_name, 'นายชื่อ ใหม่')

    def test_api_failure_keeps_cached_name(self):
        """api ล่ม + รหัสเดิม → คงชื่อเดิมไว้ อย่าล้างเป็นค่าว่างแล้วเอาไปขึ้นบัตร"""
        from unittest.mock import patch

        from .views import _get_or_refresh_line_user

        old_stamp = self.lu.profile_updated_at
        with patch('booking.views._fetch_npu_profile', return_value=None):
            lu = _get_or_refresh_line_user(
                'Utest-profile-cache', 'nong', '650000000001', 'นักศึกษา',
                force=True)

        self.assertEqual(lu.full_name, 'นางสาวชื่อ เดิม')
        self.assertEqual(lu.profile_updated_at, old_stamp)

    def test_check_user_returns_matching_ldap_and_name(self):
        """เคสที่ผู้ใช้แจ้ง: รหัสกับชื่อต้องเป็นคนเดียวกันเสมอ"""
        from unittest.mock import patch

        with patch('booking.views._fetch_npu_user',
                   return_value={'userLdap': '650000000002',
                                 'user_type': 'นักศึกษา'}), \
             patch('booking.views._fetch_npu_profile',
                   return_value=self._std_profile()):
            resp = self.client.post(
                reverse('check_user'),
                data=json.dumps({'userId': 'Utest-profile-cache',
                                 'displayName': 'nong'}),
                content_type='application/json')

        data = resp.json()
        self.assertEqual(data['userLdap'], '650000000002')
        self.assertEqual(data['full_name'], 'นายชื่อ ใหม่')
