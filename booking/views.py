import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.urls import reverse

from .models import Room, LineUser, Booking, BookingLog
from .utils import get_npu_user, register_npu_user, get_profile, verify_ldap


# ─── Home ───────────────────────────────────────────────────────────────────────

def home_view(request):
    """หน้าหลัก — แสดงรายการห้องทั้งหมด"""
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'booking/home.html', {'rooms': rooms})


# ─── Register ──────────────────────────────────────────────────────────────────

def register_view(request):
    """ผูกบัญชี LINE กับ LDAP"""
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('home')
    liff_user_id = request.GET.get('userId', '').strip()

    context = {
        'next': next_url,
        'liff_user_id': liff_user_id,
        'error': None,
        'form_data': {},
    }

    if request.method == 'POST':
        user_ldap    = request.POST.get('user_ldap', '').strip()
        pass_ldap    = request.POST.get('pass_ldap', '').strip()
        user_type    = request.POST.get('user_type', '').strip()
        line_user_id = request.POST.get('line_user_id', '').strip()

        context['form_data'] = {'user_ldap': user_ldap, 'user_type': user_type}

        if not all([user_ldap, pass_ldap, user_type]):
            context['error'] = 'กรุณากรอกข้อมูลให้ครบถ้วน'
            return render(request, 'booking/register.html', context)

        if user_type not in ['นักศึกษา', 'บุคลากรภายในมหาวิทยาลัย']:
            context['error'] = 'ประเภทผู้ใช้ไม่ถูกต้อง'
            return render(request, 'booking/register.html', context)

        ok, err = verify_ldap(user_ldap, pass_ldap)
        if not ok:
            context['error'] = err or 'username หรือ password ไม่ถูกต้อง'
            return render(request, 'booking/register.html', context)

        profile = get_profile(user_ldap, user_type)
        full_name = profile['full_name'] if profile else user_ldap

        if line_user_id:
            register_npu_user(line_user_id, user_ldap, user_type)
            LineUser.objects.update_or_create(
                line_user_id=line_user_id,
                defaults={
                    'display_name': full_name,
                    'user_ldap': user_ldap,
                    'user_type': user_type,
                    'is_active': True,
                }
            )

        return redirect(next_url)

    return render(request, 'booking/register.html', context)


# ─── Booking ───────────────────────────────────────────────────────────────────

def booking_view(request):
    """Form จอง — รับ line_id จาก URL parameter"""
    room_key = request.GET.get('room', '') or request.POST.get('room', '')
    if not room_key:
        # LIFF ส่ง ?room=mini มาเป็น liff.state=%3Froom%3Dmini
        import urllib.parse
        liff_state = request.GET.get('liff.state', '')
        if liff_state:
            params = urllib.parse.parse_qs(urllib.parse.unquote(liff_state).lstrip('?'))
            room_key = params.get('room', [''])[0]
    room = Room.objects.filter(booking_name=room_key, is_active=True).first()
    if not room:
        return render(request, 'booking/booking.html', {'room': None})

    # รับ line_id จาก GET หรือ POST
    line_id = request.GET.get('line_id', '').strip() or request.POST.get('line_id', '').strip()

    if not line_id:
        # ไม่มี line_id → ให้ LIFF JS ดึง userId แล้ว redirect กลับมาพร้อม line_id
        return render(request, 'booking/booking.html', {
            'room': room,
            'line_user': None,
            'liff_loading': True,
            'liff_id': settings.LINE_LIFF_ID,
        })

    # ─── หา LineUser
    line_user = LineUser.objects.filter(line_user_id=line_id, is_active=True).first()
    if not line_user:
        npu_data = get_npu_user(line_id)
        if npu_data:
            profile = get_profile(npu_data['userLdap'], npu_data['user_type'])
            full_name = profile['full_name'] if profile else npu_data['userLdap']
            line_user, _ = LineUser.objects.get_or_create(
                line_user_id=line_id,
                defaults={
                    'display_name': full_name,
                    'user_ldap': npu_data['userLdap'],
                    'user_type': npu_data['user_type'],
                }
            )

    if not line_user:
        # ยังไม่ผูกบัญชี → ไปหน้า register
        import urllib.parse
        next_url = request.get_full_path()
        return redirect(
            reverse('register') + '?userId=' + line_id + '&next=' + urllib.parse.quote(next_url)
        )

    # ─── GET: แสดง form
    if request.method == 'GET':
        profile = get_profile(line_user.user_ldap, line_user.user_type)
        return render(request, 'booking/booking.html', {
            'room': room,
            'line_user': line_user,
            'line_id': line_id,
            'profile': profile,
            'today': timezone.localdate().isoformat(),
        })

    # ─── POST: บันทึกการจอง
    group_name   = request.POST.get('group_name', '').strip()
    booking_date = request.POST.get('booking_date', '').strip()
    start_time   = request.POST.get('start_time', '').strip()
    end_time     = request.POST.get('end_time', '').strip()
    attendees    = request.POST.get('attendees', '').strip()

    if not all([group_name, booking_date, start_time, end_time, attendees]):
        messages.error(request, 'กรุณากรอกข้อมูลให้ครบถ้วน')
        return redirect(reverse('booking') + f'?room={room_key}&line_id={line_id}')

    if start_time >= end_time:
        messages.error(request, 'เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น')
        return redirect(reverse('booking') + f'?room={room_key}&line_id={line_id}')

    profile    = get_profile(line_user.user_ldap, line_user.user_type)
    faculty    = profile['faculty'] if profile else ''
    department = profile.get('department', '') if profile else ''

    booking, error = check_and_create_booking(
        room=room,
        date=booking_date,
        start=start_time,
        end=end_time,
        line_user=line_user,
        group_name=group_name,
        attendees=attendees,
        faculty=faculty,
        department=department,
    )

    if error:
        messages.error(request, error)
        return redirect(reverse('booking') + f'?room={room_key}&line_id={line_id}')

    request.session['last_booking_id'] = booking.id
    return redirect('booking_success')


def check_and_create_booking(room, date, start, end, line_user, **kwargs):
    """ตรวจ conflict แล้วสร้าง Booking ด้วย atomic transaction"""
    try:
        with transaction.atomic():
            conflict = Booking.objects.select_for_update().filter(
                room=room,
                booking_date=date,
                status='confirmed',
                start_time__lt=end,
                end_time__gt=start,
            ).exists()

            if conflict:
                return None, 'ช่วงเวลานี้มีการจองอยู่แล้ว กรุณาเลือกเวลาอื่น'

            booking = Booking.objects.create(
                room=room,
                booking_date=date,
                start_time=start,
                end_time=end,
                line_user=line_user,
                **kwargs,
            )
            BookingLog.objects.create(booking=booking, action='created')
            return booking, None
    except Exception as e:
        return None, f'เกิดข้อผิดพลาด: {e}'


def booking_success(request):
    booking_id = request.session.get('last_booking_id')
    booking = None
    if booking_id:
        booking = Booking.objects.filter(id=booking_id).select_related('room', 'line_user').first()
    return render(request, 'booking/success.html', {'booking': booking})


# ─── Calendar ──────────────────────────────────────────────────────────────────

def calendar_view(request):
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'booking/calendar.html', {
        'rooms': rooms,
    })


def calendar_events_api(request):
    """JSON endpoint สำหรับ FullCalendar"""
    start = request.GET.get('start', '')
    end   = request.GET.get('end', '')

    qs = Booking.objects.filter(status='confirmed').select_related('room', 'line_user')
    if start:
        qs = qs.filter(booking_date__gte=start[:10])
    if end:
        qs = qs.filter(booking_date__lte=end[:10])

    ROOM_COLORS = {
        'mini':       '#1a73e8',
        'netflix':    '#e53935',
        'canva':      '#7b1fa2',
        'chat-gpt':   '#00897b',
        'meeting_f1': '#f57c00',
    }

    events = []
    for b in qs:
        color = ROOM_COLORS.get(b.room.booking_name, '#546e7a')
        events.append({
            'id': b.id,
            'title': f"{b.room.name} — {b.group_name}",
            'start': f"{b.booking_date}T{b.start_time}",
            'end':   f"{b.booking_date}T{b.end_time}",
            'color': color,
            'extendedProps': {
                'room':       b.room.name,
                'room_key':   b.room.booking_name,
                'group_name': b.group_name,
                'status':     b.status,
                'booker':     b.line_user.display_name,
            },
        })

    return JsonResponse(events, safe=False)
