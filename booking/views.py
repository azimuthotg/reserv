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

from .models import Booking, BookingLog, LineUser, Room

NPU_API_BASE     = 'https://api.npu.ac.th'
REGISTER_URL     = f'{NPU_API_BASE}/reserv/lineoa'
PROFILE_CACHE_DAYS = 30


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

    context = {
        'liff_id':    settings.LINE_LIFF_ID,
        'room_json':  json.dumps(room_data),
        'register_url': REGISTER_URL,
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
    return render(request, 'booking/success.html', {'booking': booking})


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

    if b_date < date.today():
        return JsonResponse({'error': 'ไม่สามารถจองย้อนหลังได้'}, status=400)

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

    return JsonResponse({'success': True, 'booking_id': booking.id})
