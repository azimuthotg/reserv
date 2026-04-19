import json
import requests
from datetime import date, datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Booking, BookingLog, HolidayDate, LineUser, Room

NPU_API_BASE       = 'https://api.npu.ac.th'
REGISTER_URL       = f'{NPU_API_BASE}/reserv/lineoa'
PROFILE_CACHE_DAYS = 30
MAX_ADVANCE_WORKDAYS = 3   # จองล่วงหน้าได้สูงสุดกี่วันทำงาน


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

    # fast path: cache ยังใหม่อยู่
    if (lu and lu.full_name and
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
        'register_url': REGISTER_URL,
        'holidays_json': json.dumps(holiday_strs),
        'max_workdays': MAX_ADVANCE_WORKDAYS,
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

    holidays = _holiday_dates_set()

    # ตรวจว่าวันที่จองเป็นวันหยุดหรือไม่
    if b_date in holidays:
        holiday = HolidayDate.objects.get(date=b_date)
        return JsonResponse({'error': f'ไม่สามารถจองวัน {b_date.strftime("%d/%m/%Y")} ได้ เนื่องจาก: {holiday.description}'}, status=400)

    # ตรวจล่วงหน้าไม่เกิน 3 วันทำงาน
    today = date.today()
    workdays_ahead = _count_workdays_between(today + timedelta(days=1), b_date, holidays)
    if workdays_ahead > MAX_ADVANCE_WORKDAYS:
        return JsonResponse({'error': f'จองล่วงหน้าได้ไม่เกิน {MAX_ADVANCE_WORKDAYS} วันทำงาน'}, status=400)

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
        }
        for b in bookings
    ]
    return JsonResponse({'bookings': data})
