import json
import requests
from datetime import date, datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Booking, BookingLog, HolidayDate, LineUser, Room, RoomDevice

NPU_API_BASE       = 'https://api.npu.ac.th'
PROFILE_CACHE_DAYS = 30
MAX_ADVANCE_DAYS = 5   # จองล่วงหน้าได้สูงสุดกี่วัน (นับทุกวัน)


# ── LINE Messaging API ────────────────────────────────────────────────────────

LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'


def _push_line(user_id, messages):
    """
    ส่ง push message ไปหา LINE userId
    messages: list of message object (text, flex ฯลฯ)
    """
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
            json={'to': user_id, 'messages': messages},
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False


def _push_text(user_id, text):
    return _push_line(user_id, [{'type': 'text', 'text': text}])


# ── Holiday / working-day helpers ─────────────────────────────────────────────

def _holiday_dates_set():
    """คืน set ของวันหยุดที่ active ทั้งหมด"""
    return set(HolidayDate.objects.filter(is_active=True).values_list('date', flat=True))


def _is_workday(d, holidays):
    """วันทำงาน = จันทร์–ศุกร์ และไม่ใช่วันหยุด"""
    return d.weekday() < 5 and d not in holidays


def _count_workdays_between(start, end_inclusive, holidays):
    """นับจำนวนวันทำงานระหว่าง start ถึง end_inclusive"""
    count = 0
    cur = start
    while cur <= end_inclusive:
        if _is_workday(cur, holidays):
            count += 1
        cur += timedelta(days=1)
    return count


# ── NPU API helpers ───────────────────────────────────────────────────────────

def _verify_ldap(username, password):
    """POST /auth-ldap/auth_ldap/ → True/False"""
    try:
        resp = requests.post(
            f'{NPU_API_BASE}/auth-ldap/auth_ldap/',
            json={'username': username, 'password': password},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return bool(
                data.get('status') in ('success', 'ok') or
                data.get('authenticated') is True or
                data.get('result') is True or
                data.get('success') is True
            )
    except requests.RequestException:
        pass
    return False


def _register_npu_user(user_id, user_ldap, user_type):
    """POST /api/ ผูก LINE userId กับ LDAP → True/False"""
    try:
        resp = requests.post(
            f'{NPU_API_BASE}/api/',
            json={'userId': user_id, 'userLdap': user_ldap, 'user_type': user_type},
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except requests.RequestException:
        pass
    return False


def _fetch_npu_user(user_id):
    """GET /api/{userId}/ → { id, userId, userLdap, user_type } หรือ None"""
    try:
        resp = requests.get(f'{NPU_API_BASE}/api/{user_id}/', timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None


def _fetch_npu_profile(user_ldap, user_type):
    """GET /std-info/ หรือ /staff-info/ → ชื่อจริง, คณะ, สาขา"""
    if user_type == 'นักศึกษา':
        url = f'{NPU_API_BASE}/std-info/{user_ldap}/'
    else:
        url = f'{NPU_API_BASE}/staff-info/{user_ldap}/'
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None


def _parse_profile(profile):
    """แกะ field ชื่อ/คณะ/สาขา จาก NPU profile response"""
    if not profile:
        return '', '', ''

    # ── บุคลากร: staffname / staffsurname / departmentname ───────────────────
    if 'staffname' in profile:
        prefix   = profile.get('prefixfullname', '')
        fname    = profile.get('staffname', '')
        lname    = profile.get('staffsurname', '')
        full_name = f'{prefix}{fname} {lname}'.strip()
        faculty   = profile.get('departmentname', '')
        department = profile.get('posnameth', '')
        return full_name, faculty, department

    # ── นักศึกษา: student_name / student_surname / faculty_name / program_name ─
    if 'student_name' in profile:
        prefix    = profile.get('prefix_name', '')
        fname     = profile.get('student_name', '')
        lname     = profile.get('student_surname', '')
        full_name = f'{prefix}{fname} {lname}'.strip()
        faculty   = profile.get('faculty_name', '')
        department = profile.get('program_name', '')
        return full_name, faculty, department

    # ── fallback ──────────────────────────────────────────────────────────────
    full_name = (
        profile.get('fullname') or
        profile.get('full_name') or
        (profile.get('fname', '') + ' ' + profile.get('lname', '')).strip() or ''
    )
    faculty    = profile.get('faculty') or profile.get('department_name') or ''
    department = profile.get('branch') or profile.get('major') or ''
    return str(full_name).strip(), str(faculty).strip(), str(department).strip()


def _get_or_refresh_line_user(line_user_id, display_name, user_ldap, user_type):
    """
    ดึง LineUser จาก DB
    - ถ้ามีและ profile_updated_at < 30 วัน → คืนเลย (fast path)
    - ถ้าไม่มี หรือ profile เก่า → ดึง NPU API → cache → คืน
    """
    now          = timezone.now()
    cache_cutoff = now - timedelta(days=PROFILE_CACHE_DAYS)

    lu = LineUser.objects.filter(line_user_id=line_user_id).first()

    # fast path: cache ยังใหม่อยู่ และมีข้อมูล faculty แล้ว
    if (lu and lu.full_name and lu.faculty and
            lu.profile_updated_at and lu.profile_updated_at > cache_cutoff):
        return lu

    # ดึง profile ใหม่
    raw_profile              = _fetch_npu_profile(user_ldap, user_type)
    full_name, faculty, dept = _parse_profile(raw_profile)

    if lu:
        lu.display_name      = display_name
        lu.user_ldap         = user_ldap
        lu.user_type         = user_type
        lu.full_name         = full_name
        lu.faculty           = faculty
        lu.department        = dept
        lu.profile_updated_at = now
        lu.save()
    else:
        lu = LineUser.objects.create(
            line_user_id     = line_user_id,
            display_name     = display_name,
            user_ldap        = user_ldap,
            user_type        = user_type,
            full_name        = full_name,
            faculty          = faculty,
            department       = dept,
            profile_updated_at = now,
        )
    return lu


# ── Views ─────────────────────────────────────────────────────────────────────

def landing_page(request):
    """หน้าแรก — แสดงห้องทั้งหมด, ต้อง login LINE ผ่าน LIFF ก่อน"""
    rooms = Room.objects.filter(is_active=True).order_by('name')
    rooms_json = json.dumps([
        {
            'name':         r.name,
            'booking_name': r.booking_name,
            'capacity':     r.capacity,
            'location':     r.location or '',
            'open_time':    r.open_time.strftime('%H:%M'),
            'close_time':   r.close_time.strftime('%H:%M'),
        }
        for r in rooms
    ])
    return render(request, 'booking/landing.html', {
        'liff_id':         settings.LINE_LIFF_ID,
        'rooms_json':      rooms_json,
        'check_url':       request.build_absolute_uri(reverse('check_user')),
        'register_url':    request.build_absolute_uri(reverse('register')),
        'my_bookings_url':    request.build_absolute_uri(reverse('my_bookings')),
        'cancel_booking_url': request.build_absolute_uri(reverse('cancel_booking')),
        'checkin_url':        request.build_absolute_uri(reverse('checkin_booking')),
    })


def register_page(request):
    """หน้าผูกบัญชี LINE + LDAP"""
    user_id      = request.GET.get('userId', '') or request.POST.get('userId', '')
    display_name = request.GET.get('displayName', '') or request.POST.get('displayName', '')
    picture_url  = request.GET.get('pictureUrl', '') or request.POST.get('pictureUrl', '')
    next_url     = request.GET.get('page', '') or request.POST.get('page', '')

    if not next_url:
        next_url = request.build_absolute_uri(reverse('landing'))

    error = ''
    if request.method == 'POST':
        user_ldap = request.POST.get('user_ldap', '').strip()
        password  = request.POST.get('password', '')
        user_type = request.POST.get('user_type', '')

        if not user_id:
            error = 'ไม่พบข้อมูล LINE userId กรุณาเข้าใช้งานผ่าน LINE ใหม่อีกครั้ง'
        elif not all([user_ldap, password, user_type]):
            error = 'กรุณากรอกข้อมูลให้ครบทุกช่อง'
        elif not _verify_ldap(user_ldap, password):
            error = 'รหัสผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'
        else:
            _register_npu_user(user_id, user_ldap, user_type)
            _get_or_refresh_line_user(user_id, display_name, user_ldap, user_type)
            return redirect(next_url)

    return render(request, 'booking/register.html', {
        'user_id':      user_id,
        'display_name': display_name,
        'picture_url':  picture_url,
        'next_url':     next_url,
        'error':        error,
        'liff_id':      settings.LINE_LIFF_ID,
    })


def booking_page(request):
    """หน้า LIFF — render form จอง"""
    room_key = request.GET.get('room') or request.GET.get('booking_name') or ''
    room     = Room.objects.filter(booking_name=room_key, is_active=True).first()

    room_data = None
    if room:
        room_data = {
            'name':       room.name,
            'booking_name': room.booking_name,
            'capacity':   room.capacity,
            'location':   room.location,
            'open_time':  room.open_time.strftime('%H:%M'),
            'close_time': room.close_time.strftime('%H:%M'),
        }

    # วันหยุดในอีก 60 วันข้างหน้า สำหรับ disable ใน date picker
    today = date.today()
    holiday_list = list(
        HolidayDate.objects.filter(
            is_active=True,
            date__gte=today,
            date__lte=today + timedelta(days=60),
        ).values_list('date', flat=True)
    )
    holiday_strs = [d.strftime('%Y-%m-%d') for d in holiday_list]

    context = {
        'liff_id':      settings.LINE_LIFF_ID,
        'room_json':    json.dumps(room_data),
        'register_url': request.build_absolute_uri(reverse('register')),
        'holidays_json': json.dumps(holiday_strs),
        'max_advance_days': MAX_ADVANCE_DAYS,
    }
    return render(request, 'booking/booking.html', context)


def booking_success(request):
    """หน้าจองสำเร็จ"""
    booking_id = request.GET.get('id')
    booking    = None
    if booking_id:
        try:
            booking = Booking.objects.select_related('room', 'line_user').get(id=booking_id)
        except Booking.DoesNotExist:
            pass
    return render(request, 'booking/success.html', {
        'booking':  booking,
        'liff_id':  settings.LINE_LIFF_ID,
    })


# ── APIs ──────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def check_user(request):
    """
    POST { userId, displayName }
    → ตรวจกับ NPU API → cache ใน LineUser
    → คืน { registered, userLdap, user_type, full_name, faculty, department }
    """
    try:
        body         = json.loads(request.body)
        user_id      = body.get('userId', '').strip()
        display_name = body.get('displayName', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'invalid request'}, status=400)

    if not user_id:
        return JsonResponse({'error': 'userId required'}, status=400)

    npu_data = _fetch_npu_user(user_id)
    if not npu_data:
        return JsonResponse({'registered': False})

    user_ldap = npu_data.get('userLdap', '')
    user_type = npu_data.get('user_type', '')

    lu = _get_or_refresh_line_user(user_id, display_name, user_ldap, user_type)

    return JsonResponse({
        'registered':  True,
        'userLdap':    user_ldap,
        'user_type':   user_type,
        'full_name':   lu.full_name if lu else '',
        'faculty':     lu.faculty   if lu else '',
        'department':  lu.department if lu else '',
    })


@csrf_exempt
@require_http_methods(['POST'])
def create_booking(request):
    """
    POST { userId, room, booking_date, start_time, end_time, group_name, attendees }
    → conflict check → บันทึก Booking → คืน { success, booking_id }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)

    required = ['userId', 'room', 'booking_date', 'start_time', 'end_time', 'group_name', 'attendees']
    for f in required:
        if not body.get(f, '').strip() if isinstance(body.get(f), str) else not body.get(f):
            return JsonResponse({'error': f'กรุณากรอก {f}'}, status=400)

    user_id      = body['userId']
    room_key     = body['room']
    group_name   = body['group_name'].strip()
    attendees    = body['attendees'].strip()

    # parse date / time
    try:
        b_date = datetime.strptime(body['booking_date'], '%Y-%m-%d').date()
        s_time = datetime.strptime(body['start_time'],   '%H:%M').time()
        e_time = datetime.strptime(body['end_time'],     '%H:%M').time()
    except ValueError:
        return JsonResponse({'error': 'รูปแบบวันที่หรือเวลาไม่ถูกต้อง'}, status=400)

    if s_time >= e_time:
        return JsonResponse({'error': 'เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด'}, status=400)

    duration_min = (datetime.combine(date.today(), e_time) - datetime.combine(date.today(), s_time)).seconds // 60
    if duration_min > 210:
        return JsonResponse({'error': 'จองได้สูงสุด 3.5 ชั่วโมงต่อครั้ง'}, status=400)

    if b_date < date.today():
        return JsonResponse({'error': 'ไม่สามารถจองย้อนหลังได้'}, status=400)

    if b_date == date.today() and s_time <= timezone.localtime(timezone.now()).time():
        return JsonResponse({'error': 'ไม่สามารถจองสล็อตที่เริ่มแล้วหรือผ่านไปแล้ว'}, status=400)

    holidays = _holiday_dates_set()

    # ตรวจว่าวันที่จองเป็นวันหยุดหรือไม่
    if b_date in holidays:
        holiday = HolidayDate.objects.get(date=b_date)
        return JsonResponse({'error': f'ไม่สามารถจองวัน {b_date.strftime("%d/%m/%Y")} ได้ เนื่องจาก: {holiday.description}'}, status=400)

    # ตรวจล่วงหน้าไม่เกิน 5 วัน (นับทุกวัน)
    today = date.today()
    if b_date > today + timedelta(days=MAX_ADVANCE_DAYS):
        return JsonResponse({'error': f'จองล่วงหน้าได้ไม่เกิน {MAX_ADVANCE_DAYS} วัน'}, status=400)

    try:
        room = Room.objects.get(booking_name=room_key, is_active=True)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบข้อมูลห้อง'}, status=404)

    try:
        lu = LineUser.objects.get(line_user_id=user_id)
    except LineUser.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบข้อมูลผู้ใช้ กรุณาลองใหม่'}, status=404)

    with transaction.atomic():
        conflict = Booking.objects.select_for_update().filter(
            room         = room,
            booking_date = b_date,
            status       = 'confirmed',
            start_time__lt = e_time,
            end_time__gt   = s_time,
        ).exists()

        if conflict:
            return JsonResponse({'error': 'ช่วงเวลานี้มีการจองแล้ว กรุณาเลือกเวลาอื่น'}, status=409)

        booking = Booking.objects.create(
            room         = room,
            line_user    = lu,
            faculty      = lu.faculty,
            department   = lu.department,
            group_name   = group_name,
            booking_date = b_date,
            start_time   = s_time,
            end_time     = e_time,
            attendees    = attendees,
        )
        BookingLog.objects.create(booking=booking, action='created')

    # แจ้งเตือนจองสำเร็จทันที (นอก transaction เพื่อไม่ให้ block)
    _notify_booking_confirmed(booking)

    return JsonResponse({'success': True, 'booking_id': booking.id})


def _notify_booking_cancelled(booking, by_user=False):
    """Push แจ้งเตือนยกเลิกการจองไปหาผู้จอง"""
    b = booking
    th_months = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    date_str = f'{b.booking_date.day} {th_months[b.booking_date.month]} {b.booking_date.year + 543}'
    if by_user:
        msg = (
            f'❌ ยกเลิกการจองแล้ว\n'
            f'📍 {b.room.name}\n'
            f'📅 {date_str}\n'
            f'🕐 {b.start_time.strftime("%H:%M")} – {b.end_time.strftime("%H:%M")}\n'
            f'เลขที่การจอง: #{b.id}'
        )
    else:
        msg = (
            f'❌ การจองของคุณถูกยกเลิกโดยเจ้าหน้าที่\n'
            f'📍 {b.room.name}\n'
            f'📅 {date_str}\n'
            f'🕐 {b.start_time.strftime("%H:%M")} – {b.end_time.strftime("%H:%M")}\n'
        )
        if b.cancel_reason:
            msg += f'เหตุผล: {b.cancel_reason}\n'
        msg += 'หากมีข้อสงสัยกรุณาติดต่อเจ้าหน้าที่'
    _push_text(b.line_user.line_user_id, msg)


def _notify_booking_confirmed(booking):
    """Push แจ้งเตือนจองสำเร็จไปหาผู้จอง"""
    b = booking
    th_months = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    date_str = f'{b.booking_date.day} {th_months[b.booking_date.month]} {b.booking_date.year + 543}'
    msg = (
        f'✅ จองพื้นที่สำเร็จ\n'
        f'📍 {b.room.name}\n'
        f'📅 {date_str}\n'
        f'🕐 {b.start_time.strftime("%H:%M")} – {b.end_time.strftime("%H:%M")}\n'
        f'👥 {b.group_name}\n'
        f'เลขที่การจอง: #{b.id}'
    )
    if _push_text(b.line_user.line_user_id, msg):
        Booking.objects.filter(pk=b.pk).update(notified_start=True)


@require_http_methods(['GET'])
def bookings_by_date(request):
    """
    GET /api/bookings-by-date/?room=<key>&date=<YYYY-MM-DD>
    คืน list การจอง confirmed ในวันและห้องที่ระบุ
    """
    room_key   = request.GET.get('room', '')
    date_str   = request.GET.get('date', '')

    if not room_key or not date_str:
        return JsonResponse({'error': 'room and date required'}, status=400)

    try:
        b_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'invalid date'}, status=400)

    try:
        room = Room.objects.get(booking_name=room_key, is_active=True)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'room not found'}, status=404)

    bookings = Booking.objects.filter(
        room=room, booking_date=b_date, status='confirmed'
    ).order_by('start_time')

    data = [
        {
            'group_name': b.group_name,
            'start_time': b.start_time.strftime('%H:%M'),
            'end_time':   b.end_time.strftime('%H:%M'),
            'booker':     b.line_user.full_name or b.line_user.display_name,
        }
        for b in bookings
    ]
    return JsonResponse({'bookings': data})


# ── Cancel Booking (by user) ───────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def cancel_booking(request):
    """POST { userId, bookingId } → ผู้ใช้ยกเลิกการจองของตัวเอง"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid request'}, status=400)

    user_id    = body.get('userId', '').strip()
    booking_id = body.get('bookingId')

    if not user_id or not booking_id:
        return JsonResponse({'error': 'ข้อมูลไม่ครบ'}, status=400)

    try:
        booking = Booking.objects.select_related('line_user', 'room').get(pk=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบการจอง'}, status=404)

    if booking.line_user.line_user_id != user_id:
        return JsonResponse({'error': 'ไม่มีสิทธิ์ยกเลิกการจองนี้'}, status=403)

    if booking.status != 'confirmed':
        return JsonResponse({'error': 'การจองนี้ถูกยกเลิกไปแล้ว'}, status=400)

    now          = timezone.localtime(timezone.now())
    today        = now.date()
    current_time = now.time()
    if booking.booking_date < today or (
        booking.booking_date == today and booking.start_time <= current_time
    ):
        return JsonResponse({'error': 'ไม่สามารถยกเลิกการจองที่เริ่มแล้วหรือผ่านมาแล้ว'}, status=400)

    booking.status        = 'cancelled'
    booking.cancelled_at  = timezone.now()
    booking.cancel_reason = 'ยกเลิกโดยผู้จอง'
    booking.save()
    BookingLog.objects.create(booking=booking, action='cancelled', note='ยกเลิกโดยผู้จอง')
    _notify_booking_cancelled(booking, by_user=True)

    return JsonResponse({'success': True})


# ── My Bookings ────────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def my_bookings(request):
    """
    GET /api/my-bookings/?userId=...
    คืนการจอง confirmed ของผู้ใช้นี้ ตั้งแต่วันนี้เป็นต้นไป
    """
    user_id = request.GET.get('userId', '').strip()
    if not user_id:
        return JsonResponse({'error': 'userId required'}, status=400)

    today = date.today()
    bookings = (
        Booking.objects
        .select_related('room')
        .filter(
            line_user__line_user_id=user_id,
            booking_date__gte=today,
            status__in=['confirmed', 'cancelled'],
        )
        .order_by('booking_date', 'start_time')
    )

    data = [
        {
            'id':            b.pk,
            'full_name':     b.line_user.full_name or b.line_user.display_name,
            'room_name':     b.room.name,
            'room_key':      b.room.booking_name,
            'room_location': b.room.location or '',
            'booking_date':  b.booking_date.strftime('%Y-%m-%d'),
            'start_time':    b.start_time.strftime('%H:%M'),
            'end_time':      b.end_time.strftime('%H:%M'),
            'group_name':    b.group_name,
            'faculty':       b.faculty or '',
            'attendees':     b.attendees or '',
            'status':        b.status,
            'checked_in':    b.checked_in,
        }
        for b in bookings
    ]
    return JsonResponse({'bookings': data})


# ── Check-in ───────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def checkin_booking(request):
    """
    POST { userId, bookingId }
    → ทำ check-in การจอง (ถ้ายังอยู่ใน window -15min ถึง +15min ของ start_time)
    → คืน { success, already_checked_in }
    """
    try:
        body       = json.loads(request.body)
        user_id    = body.get('userId', '').strip()
        booking_id = body.get('bookingId')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'invalid request'}, status=400)

    if not user_id or not booking_id:
        return JsonResponse({'error': 'userId และ bookingId จำเป็น'}, status=400)

    try:
        booking = Booking.objects.select_related('line_user').get(pk=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบการจอง'}, status=404)

    if booking.line_user.line_user_id != user_id:
        return JsonResponse({'error': 'ไม่มีสิทธิ์'}, status=403)

    if booking.status != 'confirmed':
        return JsonResponse({'error': 'การจองนี้ไม่ได้อยู่ในสถานะ confirmed'}, status=400)

    if booking.checked_in:
        return JsonResponse({'success': True, 'already_checked_in': True})

    now      = timezone.localtime(timezone.now())
    today    = now.date()
    if booking.booking_date != today:
        return JsonResponse({'error': 'ไม่สามารถ check-in ล่วงหน้าได้'}, status=400)

    start_dt = timezone.make_aware(
        timezone.datetime.combine(today, booking.start_time)
    )
    checkin_open  = start_dt - timedelta(minutes=15)
    checkin_close = start_dt + timedelta(minutes=15)

    if now < checkin_open:
        return JsonResponse({'error': 'ยังไม่ถึงเวลา check-in (เปิดก่อนเริ่ม 15 นาที)'}, status=400)
    if now >= checkin_close:
        return JsonResponse({'error': 'หมดเวลา check-in แล้ว'}, status=400)

    booking.checked_in    = True
    booking.checked_in_at = timezone.now()
    booking.save(update_fields=['checked_in', 'checked_in_at'])
    BookingLog.objects.create(booking=booking, action='checked_in')

    return JsonResponse({'success': True, 'already_checked_in': False})


# ── Room Control ───────────────────────────────────────────────────────────────

def room_control_page(request):
    """หน้าควบคุมอุปกรณ์ IoT — เปิดจาก LINE หรือ LIFF"""
    return render(request, 'booking/room_control.html', {
        'liff_id':           settings.LINE_LIFF_ID,
        'room_status_url':   request.build_absolute_uri(reverse('room_status')),
        'device_toggle_url': request.build_absolute_uri(reverse('device_toggle')),
        'checkin_url':       request.build_absolute_uri(reverse('checkin_booking')),
        'landing_url':       request.build_absolute_uri(reverse('landing')),
    })


# ── Calendar ───────────────────────────────────────────────────────────────────

def card_page(request):
    """หน้า Virtual Card — แสดงบัตรสมาชิกดิจิทัล"""
    return render(request, 'booking/card.html', {
        'liff_id':    settings.LINE_LIFF_ID,
        'check_url':  request.build_absolute_uri(reverse('check_user')),
        'walai_url':  request.build_absolute_uri(reverse('walai_card')),
        'register_url': request.build_absolute_uri(reverse('register')),
    })


@csrf_exempt
@require_http_methods(['POST'])
def walai_card(request):
    """
    POST { userId, userLdap }
    → เช็ค Walai API → คืน { is_member, barcode, inform_date, ciract_name }
    """
    try:
        body      = json.loads(request.body)
        user_id   = body.get('userId', '').strip()
        user_ldap = body.get('userLdap', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'invalid request'}, status=400)

    if not user_ldap:
        return JsonResponse({'error': 'userLdap required'}, status=400)

    try:
        resp = requests.get(
            f'{NPU_API_BASE}/walai/check_user_walai/{user_ldap}/',
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Walai คืน array — ถ้ามีข้อมูล = สมาชิก
            if isinstance(data, list) and len(data) > 0:
                w = data[0]
                return JsonResponse({
                    'is_member':   True,
                    'barcode':     w.get('BARCODE', ''),
                    'inform_date': w.get('INFORMDATE', ''),
                    'ciract_name': w.get('CIRACTNAME', ''),
                })
            return JsonResponse({'is_member': False})
    except requests.RequestException:
        pass

    return JsonResponse({'is_member': False, 'error': 'ไม่สามารถตรวจสอบ Walai ได้'})


# ── Home Assistant helpers ─────────────────────────────────────────────────────

def _ha_url(path):
    return f'http://{settings.HA_IP}:{settings.HA_PORT}{path}'

def _ha_headers():
    return {'Authorization': f'Bearer {settings.HA_TOKEN}', 'Content-Type': 'application/json'}

def _ha_get_state(entity_id):
    """คืน (state, error) — state: 'on'/'off'/'unknown'/None, error: str|None"""
    try:
        r = requests.get(_ha_url(f'/api/states/{entity_id}'), headers=_ha_headers(), timeout=5)
        if r.status_code == 200:
            return r.json().get('state', 'unknown'), None
        return None, f'HA HTTP {r.status_code}'
    except requests.RequestException as e:
        return None, str(e)

def _ha_call_service(service, entity_id):
    """service: 'turn_on' | 'turn_off' | 'toggle'"""
    try:
        r = requests.post(
            _ha_url(f'/api/services/switch/{service}'),
            headers=_ha_headers(),
            json={'entity_id': entity_id},
            timeout=5,
        )
        return r.status_code in (200, 201)
    except requests.RequestException:
        return False

def _get_active_booking(user_id, room_key):
    """คืน Booking ที่กำลัง active อยู่ หรือ None"""
    now   = timezone.localtime(timezone.now())
    today = now.date()
    cur   = now.time()
    return (
        Booking.objects
        .select_related('room')
        .filter(
            line_user__line_user_id=user_id,
            room__booking_name=room_key,
            booking_date=today,
            status='confirmed',
            start_time__lte=cur,
            end_time__gt=cur,
        )
        .first()
    )


@csrf_exempt
@require_http_methods(['GET'])
def room_status(request):
    """
    GET /api/room-status/?userId=X&room_key=Y
    → ตรวจสิทธิ์ → คืนรายการอุปกรณ์ + สถานะปัจจุบันจาก HA
    """
    user_id  = request.GET.get('userId', '').strip()
    room_key = request.GET.get('room_key', '').strip()
    if not user_id or not room_key:
        return JsonResponse({'error': 'userId and room_key required'}, status=400)

    booking = _get_active_booking(user_id, room_key)
    if not booking:
        return JsonResponse({'access': False, 'error': 'ไม่มีสิทธิ์เข้าห้องในขณะนี้'})

    devices = RoomDevice.objects.filter(room=booking.room)
    result  = []
    ha_errors = []
    for d in devices:
        state, err = _ha_get_state(d.entity_id)
        if err:
            ha_errors.append(f'{d.entity_id}: {err}')
        result.append({
            'id':          d.pk,
            'device_name': d.device_name,
            'entity_id':   d.entity_id,
            'state':       state or 'unknown',
        })

    return JsonResponse({
        'access':    True,
        'room_name': booking.room.name,
        'end_time':  booking.end_time.strftime('%H:%M'),
        'devices':   result,
        'ha_url':    _ha_url(''),
        'ha_errors': ha_errors,
    })


@csrf_exempt
@require_http_methods(['POST'])
def device_toggle(request):
    """
    POST { userId, room_key, entity_id }
    → ตรวจสิทธิ์ → toggle อุปกรณ์ผ่าน HA → คืนสถานะใหม่
    """
    try:
        body      = json.loads(request.body)
        user_id   = body.get('userId', '').strip()
        room_key  = body.get('room_key', '').strip()
        entity_id = body.get('entity_id', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'invalid request'}, status=400)

    if not all([user_id, room_key, entity_id]):
        return JsonResponse({'error': 'userId, room_key, entity_id required'}, status=400)

    booking = _get_active_booking(user_id, room_key)
    if not booking:
        return JsonResponse({'success': False, 'error': 'ไม่มีสิทธิ์ควบคุมอุปกรณ์'})

    # ตรวจว่า entity_id นี้เป็นของห้องนี้จริง
    if not RoomDevice.objects.filter(room=booking.room, entity_id=entity_id).exists():
        return JsonResponse({'success': False, 'error': 'ไม่พบอุปกรณ์'})

    ok = _ha_call_service('toggle', entity_id)
    if not ok:
        return JsonResponse({'success': False, 'error': 'ไม่สามารถติดต่อ Home Assistant ได้'})

    new_state = _ha_get_state(entity_id)
    return JsonResponse({'success': True, 'state': new_state or 'unknown'})


def calendar_page(request):
    """ปฏิทินรวมการจองทุกห้อง (public — ไม่ต้อง login)"""
    rooms = Room.objects.filter(is_active=True).order_by('name')
    return render(request, 'booking/calendar.html', {
        'rooms': rooms,
        'events_url': request.build_absolute_uri(reverse('calendar_events')),
    })


def room_detail(request, booking_name):
    """หน้ารายละเอียดห้อง (public — ไม่ต้อง login)"""
    from django.shortcuts import get_object_or_404
    room = get_object_or_404(Room, booking_name=booking_name, is_active=True)

    # สีของห้องโดยใช้ index เดียวกับ landing page
    accent_colors = ['#06C755', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4']
    all_rooms     = list(Room.objects.filter(is_active=True).order_by('name').values_list('booking_name', flat=True))
    idx           = all_rooms.index(booking_name) if booking_name in all_rooms else 0
    room_color    = accent_colors[idx % len(accent_colors)]

    facilities = [f.strip() for f in room.facilities.splitlines() if f.strip()]
    rules      = [r.strip() for r in room.rules.splitlines() if r.strip()]
    how_to_use = [s.strip() for s in room.how_to_use.splitlines() if s.strip()]
    eligible   = [e.strip() for e in room.eligible_users.splitlines() if e.strip()]
    return render(request, 'booking/room_detail.html', {
        'room':       room,
        'room_color': room_color,
        'facilities': facilities,
        'rules':      rules,
        'how_to_use': how_to_use,
        'eligible':   eligible,
    })


@require_http_methods(['GET'])
def calendar_events(request):
    """
    GET /api/calendar-events/?start=YYYY-MM-DD&end=YYYY-MM-DD&room=<key>
    คืน FullCalendar events format
    """
    start_str = request.GET.get('start', '')
    end_str   = request.GET.get('end', '')
    room_key  = request.GET.get('room', '')

    qs = Booking.objects.select_related('room', 'line_user').filter(status='confirmed')

    if start_str:
        try:
            qs = qs.filter(booking_date__gte=datetime.strptime(start_str[:10], '%Y-%m-%d').date())
        except ValueError:
            pass
    if end_str:
        try:
            qs = qs.filter(booking_date__lte=datetime.strptime(end_str[:10], '%Y-%m-%d').date())
        except ValueError:
            pass
    if room_key:
        qs = qs.filter(room__booking_name=room_key)

    events = []
    for b in qs:
        events.append({
            'id':    b.pk,
            'title': f'{b.room.name} — {b.group_name}',
            'start': f'{b.booking_date}T{b.start_time.strftime("%H:%M:%S")}',
            'end':   f'{b.booking_date}T{b.end_time.strftime("%H:%M:%S")}',
            'extendedProps': {
                'room_key':   b.room.booking_name,
                'room':       b.room.name,
                'group_name': b.group_name,
                'booker':     b.line_user.full_name or b.line_user.display_name,
                'faculty':    b.faculty,
                'start_time': b.start_time.strftime('%H:%M'),
                'end_time':   b.end_time.strftime('%H:%M'),
            },
        })

    return JsonResponse(events, safe=False)
