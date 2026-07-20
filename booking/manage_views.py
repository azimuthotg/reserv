import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from functools import wraps

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import HolidayDateForm, RoomClosureForm, RoomForm, StaffAddForm, StaffEditForm
from .models import Booking, BookingLog, HolidayDate, LineUser, Room, RoomClosure, RoomDevice
from .service_hours import room_service_hours
from .views import _notify_booking_cancelled, _npu_v2_request, _push_text


# ── Permission decorators ──────────────────────────────────────────────────────

def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('manage_login')
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('manage_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('manage_login')
        if not request.user.is_superuser:
            return render(request, 'booking/manage/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Auth ───────────────────────────────────────────────────────────────────────

def manage_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('manage_dashboard')

    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser) and user.is_active:
            login(request, user)
            return redirect(request.GET.get('next', 'manage_dashboard'))
        error = 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง หรือไม่มีสิทธิ์เข้าใช้'
    return render(request, 'booking/manage/login.html', {'error': error})


def manage_logout(request):
    logout(request)
    return redirect('manage_login')


# ── Dashboard ──────────────────────────────────────────────────────────────────

@staff_required
def manage_dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    stats = {
        'today':    Booking.objects.filter(booking_date=today, status='confirmed').count(),
        'upcoming': Booking.objects.filter(booking_date__gte=today, status='confirmed').count(),
        'month':    Booking.objects.filter(booking_date__gte=month_start, status='confirmed').count(),
        'users':    LineUser.objects.filter(is_active=True).count(),
        'rooms':    Room.objects.filter(is_active=True).count(),
    }
    recent_bookings = (
        Booking.objects.select_related('room', 'line_user')
        .filter(status='confirmed').order_by('-created_at')[:10]
    )
    upcoming_holidays = (
        HolidayDate.objects.filter(is_active=True, date__gte=today, date__lte=today + timedelta(days=30))
        .order_by('date')
    )
    return render(request, 'booking/manage/dashboard.html', {
        'stats': stats,
        'recent_bookings': recent_bookings,
        'upcoming_holidays': upcoming_holidays,
        'today': today,
    })


@staff_required
def manage_analytics(request):
    """
    หน้าวิเคราะห์การจอง — อัตราการใช้ห้อง, แนวโน้มตามช่วงเวลา, พฤติกรรมผู้ใช้, no-show/ยกเลิกกระชั้นชิด
    หมายเหตุ: อัตราการใช้ห้องคำนวณจากเวลาเปิดบริการเท่านั้น ไม่หักช่วง RoomClosure (ปิดชั่วคราว)
    """
    today = date.today()
    now_local = timezone.localtime(timezone.now())

    try:
        days = int(request.GET.get('period', '30'))
    except ValueError:
        days = 30
    if days not in (7, 30, 90):
        days = 30

    range_start = today - timedelta(days=days - 1)

    period_qs = Booking.objects.filter(booking_date__gte=range_start, booking_date__lte=today)
    confirmed = list(
        period_qs.filter(status='confirmed')
        .select_related('room', 'line_user')
        .order_by('booking_date')
    )
    cancelled = list(
        period_qs.filter(status='cancelled')
        .select_related('room', 'line_user')
    )

    total_confirmed = len(confirmed)
    total_cancelled = len(cancelled)
    total_made = total_confirmed + total_cancelled

    # ── No-show ดึงจาก auto-cancel (ไม่ใช่ confirmed ที่ไม่ check-in) ──────────
    # ระบบ auto-cancel booking ที่ไม่ check-in ภายใน 15 นาทีหลังเริ่ม (send_reminders.py)
    # → no-show จริงกลายเป็น status='cancelled' + BookingLog action='auto_cancelled'
    # ถ้านับจาก confirmed ที่ไม่ check-in จะได้ ~0 เสมอ เพราะโดน auto-cancel ไปหมดแล้ว
    no_show_logs = list(
        BookingLog.objects
        .filter(action='auto_cancelled',
                booking__booking_date__gte=range_start,
                booking__booking_date__lte=today)
        .select_related('booking__line_user')
    )
    no_show_count = len({log.booking_id for log in no_show_logs})

    # ยกเลิกโดยผู้ใช้ = cancelled ทั้งหมด − no-show (auto-cancel)
    user_cancelled = max(0, total_cancelled - no_show_count)
    user_cancel_rate = round(user_cancelled / total_made * 100, 1) if total_made else 0

    # ── เวลาที่ถูกจอง (นาที) + แนวโน้มรายวัน ──────────────────────────────────
    total_booked_minutes = 0
    trend_by_day = defaultdict(int)
    for b in confirmed:
        total_booked_minutes += (
            (b.end_time.hour * 60 + b.end_time.minute)
            - (b.start_time.hour * 60 + b.start_time.minute)
        )
        trend_by_day[b.booking_date] += 1

    trend_labels, trend_counts = [], []
    d = range_start
    while d <= today:
        trend_labels.append(d.strftime('%d/%m'))
        trend_counts.append(trend_by_day.get(d, 0))
        d += timedelta(days=1)

    # ── No-show rate = no-show ÷ (มาจริง + no-show) ────────────────────────────
    # "มาจริง" = booking ที่ผ่านเวลาจบแล้วและยัง confirmed อยู่ (ไม่ถูก auto-cancel)
    past_confirmed = 0
    for b in confirmed:
        booking_end = datetime.combine(b.booking_date, b.end_time)
        if booking_end < datetime.combine(today, now_local.time()):
            past_confirmed += 1
    no_show_denom = past_confirmed + no_show_count
    no_show_rate = round(no_show_count / no_show_denom * 100, 1) if no_show_denom else 0

    # ── อัตราการใช้ห้อง (utilization) ──────────────────────────────────────────
    rooms = list(Room.objects.filter(is_active=True).order_by('name'))
    booked_minutes_by_room = defaultdict(int)
    for b in confirmed:
        booked_minutes_by_room[b.room_id] += (
            (b.end_time.hour * 60 + b.end_time.minute)
            - (b.start_time.hour * 60 + b.start_time.minute)
        )

    available_minutes_by_room = defaultdict(int)
    d = range_start
    while d <= today:
        for room in rooms:
            open_t, close_t = room_service_hours(room, d)
            available_minutes_by_room[room.id] += (
                (close_t.hour * 60 + close_t.minute) - (open_t.hour * 60 + open_t.minute)
            )
        d += timedelta(days=1)

    room_stats = []
    for room in rooms:
        available = available_minutes_by_room[room.id]
        booked = booked_minutes_by_room[room.id]
        room_stats.append({
            'room': room,
            'booked_hours': round(booked / 60, 1),
            'utilization': round(booked / available * 100, 1) if available else 0,
        })
    room_stats.sort(key=lambda r: r['utilization'], reverse=True)

    total_available_minutes = sum(available_minutes_by_room.values())
    overall_utilization = (
        round(total_booked_minutes / total_available_minutes * 100, 1) if total_available_minutes else 0
    )

    # ── พฤติกรรมผู้ใช้ + ผู้ใช้จองถี่ ──────────────────────────────────────────
    user_stats = defaultdict(lambda: {'user': None, 'count': 0, 'no_show': 0, 'late_cancel': 0})
    for b in confirmed:
        entry = user_stats[b.line_user_id]
        entry['user']  = b.line_user
        entry['count'] += 1
    # no-show ต่อผู้ใช้ นับจาก auto-cancel log (ตั้ง user object ให้ด้วยเผื่อผู้ใช้ไม่มี confirmed)
    for log in no_show_logs:
        entry = user_stats[log.booking.line_user_id]
        entry['user'] = log.booking.line_user
        entry['no_show'] += 1

    # ยกเลิกกระชั้นชิด (ภายใน 60 นาทีก่อนเวลาเริ่ม) — สัญญาณที่ควรตรวจสอบเพิ่มเติม ไม่ใช่ข้อสรุปว่าเป็นพฤติกรรมมิชอบ
    late_cancels = []
    for b in cancelled:
        if not b.cancelled_at:
            continue
        if 'auto-cancel' in (b.cancel_reason or ''):
            continue  # no-show ที่ระบบยกเลิกเอง ไม่นับเป็นยกเลิกกระชั้นชิดของผู้ใช้
        start_dt = timezone.make_aware(datetime.combine(b.booking_date, b.start_time))
        lead_minutes = (start_dt - b.cancelled_at).total_seconds() / 60
        if 0 <= lead_minutes <= 60:
            late_cancels.append({'booking': b, 'lead_minutes': round(lead_minutes)})
            entry = user_stats[b.line_user_id]
            entry['user'] = b.line_user
            entry['late_cancel'] += 1
    late_cancels.sort(key=lambda x: x['booking'].cancelled_at, reverse=True)

    heavy_threshold = max(3, round(days * 0.5))  # จองอย่างน้อยครึ่งหนึ่งของจำนวนวันในช่วง = จองถี่ผิดปกติ
    top_users = sorted(user_stats.values(), key=lambda e: e['count'], reverse=True)[:10]
    for entry in top_users:
        entry['heavy'] = entry['count'] >= heavy_threshold

    return render(request, 'booking/manage/analytics.html', {
        'days': days,
        'range_start': range_start,
        'range_end': today,
        'total_confirmed': total_confirmed,
        'total_cancelled': total_cancelled,
        'user_cancelled': user_cancelled,
        'user_cancel_rate': user_cancel_rate,
        'total_booked_hours': round(total_booked_minutes / 60, 1),
        'overall_utilization': overall_utilization,
        'no_show_rate': no_show_rate,
        'no_show_count': no_show_count,
        'no_show_denom': no_show_denom,
        'room_stats': room_stats,
        'trend_labels': trend_labels,
        'trend_counts': trend_counts,
        'top_users': top_users,
        'late_cancels': late_cancels[:20],
    })


# ── Bookings ───────────────────────────────────────────────────────────────────

@staff_required
def manage_daily_schedule(request):
    """ตารางการจองรายวัน — แสดงทุกห้องในวันที่เลือก"""
    date_str = request.GET.get('date', '')
    try:
        view_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        view_date = date.today()

    today = date.today()
    rooms = list(Room.objects.filter(is_active=True).order_by('name'))
    service_hours_by_room = {
        room.id: room_service_hours(room, view_date)
        for room in rooms
    }
    if service_hours_by_room:
        TLINE_START = min(t.hour * 60 + t.minute for t, _ in service_hours_by_room.values())
        tline_end   = max(t.hour * 60 + t.minute for _, t in service_hours_by_room.values())
    else:
        TLINE_START = 510
        tline_end   = 990
    TLINE_RANGE = max(1, tline_end - TLINE_START)
    bookings_qs = (
        Booking.objects
        .filter(booking_date=view_date, status='confirmed')
        .select_related('room', 'line_user')
        .order_by('start_time', 'room__name')
    )

    # วันหยุดและการปิดห้องในวันนี้
    holiday  = HolidayDate.objects.filter(date=view_date, is_active=True).first()
    closures = RoomClosure.objects.filter(date=view_date, is_active=True).select_related('room')
    closure_by_room = {}
    for c in closures:
        closure_by_room.setdefault(c.room_id, []).append(c)

    # จัดกลุ่ม booking ตามห้อง
    by_room = {r.id: [] for r in rooms}
    for b in bookings_qs:
        if b.room_id in by_room:
            s = b.start_time.hour * 60 + b.start_time.minute
            e = b.end_time.hour * 60 + b.end_time.minute
            by_room[b.room_id].append({
                'obj':       b,
                'start_min': s,
                'end_min':   e,
                'left_pct':  round(max(0, (s - TLINE_START) / TLINE_RANGE * 100), 2),
                'width_pct': round(min(100, (e - s) / TLINE_RANGE * 100), 2),
            })

    room_data = []
    for room in rooms:
        open_time, close_time = service_hours_by_room[room.id]
        om = open_time.hour * 60 + open_time.minute
        cm = close_time.hour * 60 + close_time.minute
        room_data.append({
            'room':           room,
            'open_time':      open_time,
            'close_time':     close_time,
            'bookings':       by_room.get(room.id, []),
            'open_left_pct':  round(max(0, (om - TLINE_START) / TLINE_RANGE * 100), 2),
            'open_width_pct': round(min(100, (cm - om) / TLINE_RANGE * 100), 2),
            'closures':       closure_by_room.get(room.id, []),
        })

    # hour markers สำหรับ timeline ตามช่วงเปิดบริการของวันที่เลือก
    hour_markers = [
        {'h': h, 'pct': round((h * 60 - TLINE_START) / TLINE_RANGE * 100, 2)}
        for h in range((TLINE_START + 59) // 60, tline_end // 60 + 1)
    ]

    # JSON สำหรับ JS real-time status
    bookings_json = json.dumps([
        {
            'id':        b.id,
            'start_min': b.start_time.hour * 60 + b.start_time.minute,
            'end_min':   b.end_time.hour * 60 + b.end_time.minute,
        }
        for b in bookings_qs
    ])

    return render(request, 'booking/manage/daily_schedule.html', {
        'view_date':     view_date,
        'is_today':      view_date == today,
        'room_data':     room_data,
        'all_bookings':  list(bookings_qs),
        'total':         bookings_qs.count(),
        'prev_date':     (view_date - timedelta(days=1)).isoformat(),
        'next_date':     (view_date + timedelta(days=1)).isoformat(),
        'hour_markers':  hour_markers,
        'bookings_json': bookings_json,
        'holiday':       holiday,
        'closures':      list(closures),
        'tline_start':   TLINE_START,
        'tline_range':   TLINE_RANGE,
    })


@staff_required
def manage_bookings(request):
    qs = Booking.objects.select_related('room', 'line_user').order_by('-booking_date', '-start_time')

    room_filter   = request.GET.get('room', '')
    date_filter   = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')
    search        = request.GET.get('search', '').strip()

    if room_filter:
        qs = qs.filter(room__booking_name=room_filter)
    if date_filter:
        qs = qs.filter(booking_date=date_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(
            Q(group_name__icontains=search) |
            Q(line_user__full_name__icontains=search) |
            Q(line_user__user_ldap__icontains=search) |
            Q(faculty__icontains=search)
        )

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    rooms     = Room.objects.filter(is_active=True).order_by('name')

    return render(request, 'booking/manage/bookings.html', {
        'page_obj':     page_obj,
        'rooms':        rooms,
        'room_filter':  room_filter,
        'date_filter':  date_filter,
        'status_filter': status_filter,
        'search':       search,
    })


@staff_required
@require_POST
def manage_booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if booking.status == 'confirmed':
        reason = request.POST.get('cancel_reason', '').strip()
        booking.status        = 'cancelled'
        booking.cancelled_at  = timezone.now()
        booking.cancel_reason = reason
        booking.save()
        BookingLog.objects.create(booking=booking, action='cancelled', note=reason)
        _notify_booking_cancelled(booking, by_user=False)
    return redirect('manage_bookings')


# ── Holidays ───────────────────────────────────────────────────────────────────

@staff_required
def manage_holidays(request):
    year = int(request.GET.get('year', date.today().year))
    holidays = HolidayDate.objects.filter(date__year=year).order_by('date')
    years = list(range(date.today().year, date.today().year + 3))
    return render(request, 'booking/manage/holidays.html', {
        'holidays': holidays,
        'year':     year,
        'years':    years,
    })


@staff_required
def manage_holiday_add(request):
    form = HolidayDateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_holidays')
    return render(request, 'booking/manage/holiday_form.html', {'form': form, 'title': 'เพิ่มวันหยุด'})


@staff_required
def manage_holiday_edit(request, pk):
    holiday = get_object_or_404(HolidayDate, pk=pk)
    form = HolidayDateForm(request.POST or None, instance=holiday)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_holidays')
    return render(request, 'booking/manage/holiday_form.html', {'form': form, 'title': 'แก้ไขวันหยุด'})


@staff_required
@require_POST
def manage_holiday_delete(request, pk):
    get_object_or_404(HolidayDate, pk=pk).delete()
    return redirect('manage_holidays')


@staff_required
@require_POST
def manage_holiday_toggle(request, pk):
    holiday = get_object_or_404(HolidayDate, pk=pk)
    holiday.is_active = not holiday.is_active
    holiday.save()
    return redirect('manage_holidays')


# ── Room Closures ──────────────────────────────────────────────────────────────

@staff_required
def manage_closures(request):
    year     = int(request.GET.get('year', date.today().year))
    room_key = request.GET.get('room', '')
    closures = RoomClosure.objects.select_related('room').filter(date__year=year).order_by('date', 'room')
    if room_key:
        closures = closures.filter(room__booking_name=room_key)
    rooms = Room.objects.filter(is_active=True).order_by('name')
    years = list(range(date.today().year, date.today().year + 3))
    return render(request, 'booking/manage/closures.html', {
        'closures': closures,
        'rooms':    rooms,
        'year':     year,
        'years':    years,
        'room_key': room_key,
    })


@staff_required
def manage_closure_add(request):
    form = RoomClosureForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_closures')
    return render(request, 'booking/manage/closure_form.html', {'form': form, 'title': 'เพิ่มการปิดห้องชั่วคราว'})


@staff_required
def manage_closure_edit(request, pk):
    closure = get_object_or_404(RoomClosure, pk=pk)
    form    = RoomClosureForm(request.POST or None, instance=closure)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_closures')
    return render(request, 'booking/manage/closure_form.html', {'form': form, 'title': 'แก้ไขการปิดห้องชั่วคราว'})


@staff_required
@require_POST
def manage_closure_delete(request, pk):
    get_object_or_404(RoomClosure, pk=pk).delete()
    return redirect('manage_closures')


@staff_required
@require_POST
def manage_closure_toggle(request, pk):
    closure           = get_object_or_404(RoomClosure, pk=pk)
    closure.is_active = not closure.is_active
    closure.save()
    return redirect('manage_closures')


# ── LINE Users ─────────────────────────────────────────────────────────────────

@staff_required
@require_POST
def manage_line_user_toggle(request, pk):
    lu = get_object_or_404(LineUser, pk=pk)
    lu.is_active = not lu.is_active
    lu.save()
    return redirect('manage_line_users')


@staff_required
def manage_line_user_detail(request, pk):
    lu = get_object_or_404(LineUser, pk=pk)
    bookings = (
        Booking.objects.select_related('room')
        .filter(line_user=lu)
        .order_by('-booking_date', '-start_time')
    )
    total      = bookings.count()
    confirmed  = bookings.filter(status='confirmed').count()
    cancelled  = bookings.filter(status='cancelled').count()
    cancel_rate = round(cancelled / total * 100) if total else 0
    return render(request, 'booking/manage/line_user_detail.html', {
        'line_user':       lu,
        'bookings':        bookings,
        'total_bookings':  total,
        'confirmed_count': confirmed,
        'cancelled_count': cancelled,
        'cancel_rate':     cancel_rate,
    })


@staff_required
def manage_booking_logs(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room', 'line_user'), pk=pk
    )
    logs = booking.logs.order_by('timestamp')
    return render(request, 'booking/manage/booking_logs.html', {
        'booking': booking,
        'logs':    logs,
    })


@staff_required
def manage_line_users(request):
    qs = LineUser.objects.order_by('-created_at')
    search    = request.GET.get('search', '').strip()
    user_type = request.GET.get('user_type', '')

    if search:
        qs = qs.filter(
            Q(full_name__icontains=search) |
            Q(user_ldap__icontains=search) |
            Q(faculty__icontains=search)
        )
    if user_type:
        qs = qs.filter(user_type=user_type)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    user_types = LineUser.objects.values_list('user_type', flat=True).distinct()

    return render(request, 'booking/manage/line_users.html', {
        'page_obj':   page_obj,
        'search':     search,
        'user_type':  user_type,
        'user_types': user_types,
    })


# ── Rooms (admin only) ─────────────────────────────────────────────────────────

@admin_required
def manage_rooms(request):
    rooms = Room.objects.order_by('name')
    return render(request, 'booking/manage/rooms.html', {'rooms': rooms})


@admin_required
def manage_room_add(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_rooms')
    return render(request, 'booking/manage/room_form.html', {'form': form, 'title': 'เพิ่มห้อง'})


@admin_required
def manage_room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    form = RoomForm(request.POST or None, instance=room)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_rooms')
    return render(request, 'booking/manage/room_form.html', {'form': form, 'title': 'แก้ไขห้อง'})


@admin_required
@require_POST
def manage_room_toggle(request, pk):
    room = get_object_or_404(Room, pk=pk)
    room.is_active = not room.is_active
    room.save()
    return redirect('manage_rooms')


# ── Room Devices (admin only) ──────────────────────────────────────────────────

@admin_required
def manage_room_devices(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        device_name = request.POST.get('device_name', '').strip()
        entity_id   = request.POST.get('entity_id', '').strip()
        order       = request.POST.get('order', '0').strip()
        if device_name and entity_id:
            RoomDevice.objects.create(
                room=room,
                device_name=device_name,
                entity_id=entity_id,
                order=int(order) if order.isdigit() else 0,
            )
        return redirect('manage_room_devices', pk=pk)
    devices = room.devices.all()
    return render(request, 'booking/manage/room_devices.html', {'room': room, 'devices': devices})


@admin_required
@require_POST
def manage_room_device_delete(request, pk):
    device = get_object_or_404(RoomDevice, pk=pk)
    room_pk = device.room_id
    device.delete()
    if room_pk is None:      # อุปกรณ์กลุ่มที่ไม่สังกัดห้อง ไม่มีหน้าห้องให้กลับไป
        return redirect('manage_iot_monitor')
    return redirect('manage_room_devices', pk=room_pk)


# ── IoT Monitor (staff) ────────────────────────────────────────────────────────

def _iot_cards():
    """คืนการ์ดทั้งหมดของหน้า IoT Monitor เรียงห้องที่เปิดใช้งานก่อน
    แล้วตามด้วยกลุ่มอุปกรณ์หลังบ้านที่ไม่สังกัดห้อง (room=None) จับกลุ่มตาม group_name
    """
    cards = []
    for room in Room.objects.filter(is_active=True).prefetch_related('devices'):
        cards.append({
            'key':     f'room-{room.booking_name}',
            'name':    room.name,
            'devices': list(room.devices.all()),
        })

    groups = {}
    for d in RoomDevice.objects.filter(room__isnull=True).order_by('group_name', 'order', 'id'):
        groups.setdefault(d.group_name or 'ไม่ระบุกลุ่ม', []).append(d)
    for name, devices in groups.items():
        # ใช้ hash ของชื่อกลุ่มเป็น key เพราะ slugify ตัดสระ/วรรณยุกต์ไทยทิ้ง
        # ทำให้ชื่อที่ต่างกันเหลือ slug เดียวกันได้ ส่วน key นี้ใช้เป็น id ใน DOM เท่านั้น
        digest = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
        cards.append({
            'key':     f'group-{digest}',
            'name':    name,
            'devices': devices,
        })
    return cards


def _ha_get_state_manage(entity_id):
    """ดึงสถานะ HA สำหรับหน้า monitor คืน dict {state, error}"""
    if not getattr(settings, 'HA_IP', '') or not getattr(settings, 'HA_TOKEN', ''):
        return {'state': None, 'error': 'HA ยังไม่ได้ตั้งค่า'}
    try:
        r = requests.get(
            f'http://{settings.HA_IP}:{settings.HA_PORT}/api/states/{entity_id}',
            headers={'Authorization': f'Bearer {settings.HA_TOKEN}', 'Content-Type': 'application/json'},
            timeout=5,
        )
        if r.status_code == 200:
            return {'state': r.json().get('state', 'unknown'), 'error': None}
        return {'state': None, 'error': f'HA HTTP {r.status_code}'}
    except requests.RequestException as e:
        return {'state': None, 'error': str(e)}


def _ha_call_service(entity_id, action):
    """สั่ง HA service (turn_on / turn_off) สำหรับ entity_id หนึ่งตัว
    คืน {'success': bool, 'error': str|None}
    """
    if not getattr(settings, 'HA_IP', '') or not getattr(settings, 'HA_TOKEN', ''):
        return {'success': False, 'error': 'HA ยังไม่ได้ตั้งค่า'}
    domain = entity_id.split('.')[0]  # "switch", "light", ฯลฯ
    try:
        r = requests.post(
            f'http://{settings.HA_IP}:{settings.HA_PORT}/api/services/{domain}/{action}',
            headers={'Authorization': f'Bearer {settings.HA_TOKEN}', 'Content-Type': 'application/json'},
            json={'entity_id': entity_id},
            timeout=5,
        )
        if r.status_code in (200, 201):
            return {'success': True, 'error': None}
        return {'success': False, 'error': f'HA HTTP {r.status_code}'}
    except requests.RequestException as e:
        return {'success': False, 'error': str(e)}


@staff_required
@require_POST
def manage_iot_device_control(request, pk):
    """POST /manage/iot-monitor/control/<pk>/
    body (form): action = on | off
    คืน JSON {success, state, error}
    """
    from django.http import JsonResponse
    device = get_object_or_404(RoomDevice, pk=pk)
    action_raw = request.POST.get('action', '')
    if action_raw not in ('on', 'off'):
        return JsonResponse({'success': False, 'error': 'action ต้องเป็น on หรือ off'}, status=400)

    ha_action = f'turn_{action_raw}'
    result = _ha_call_service(device.entity_id, ha_action)

    # ดึงสถานะล่าสุดหลังสั่งงาน
    new_state = None
    if result['success']:
        import time; time.sleep(0.8)  # รอ HA อัปเดต state
        info = _ha_get_state_manage(device.entity_id)
        new_state = info['state']

    return JsonResponse({
        'success': result['success'],
        'state':   new_state,
        'error':   result['error'],
    })


@staff_required
def manage_iot_monitor(request):
    """หน้า IoT Monitor — แสดงสถานะอุปกรณ์ทุกห้อง + กลุ่มอุปกรณ์หลังบ้าน"""
    return render(request, 'booking/manage/iot_monitor.html', {
        'cards':            _iot_cards(),
        'ha_configured':    bool(getattr(settings, 'HA_IP', '') and getattr(settings, 'HA_TOKEN', '')),
        'group_configured': bool(getattr(settings, 'LINE_GROUP_ID', '')),
    })


@staff_required
def manage_iot_notify_group(request):
    """
    POST /manage/iot-monitor/notify/
    ดึงสถานะ IoT ทั้งหมด แล้วส่งไปกลุ่ม LINE (manual trigger)
    """
    from django.http import JsonResponse
    from django.utils import timezone

    all_ok = True
    total_online = total_offline = total_unknown = 0
    room_lines = []

    for card in _iot_cards():
        devices = card['devices']
        if not devices:
            continue
        room_ok = True
        device_lines = []
        for d in devices:
            info = _ha_get_state_manage(d.entity_id)
            state = info['state']
            if state is None:
                icon, label = '❓', 'ไม่ทราบ'
                total_unknown += 1
                room_ok = False
            elif state in ('on', 'off'):
                icon  = '🟢' if state == 'on' else '⚫'
                label = 'Online' if state == 'on' else 'Standby'
                total_online += 1
            else:
                icon, label = '🔴', f'Offline ({state})'
                total_offline += 1
                room_ok = False
            device_lines.append(f'  {icon} {d.device_name}: {label}')
        if not room_ok:
            all_ok = False
        status_icon = '✅' if room_ok else '⚠️'
        room_lines.append(f'{status_icon} {card["name"]}')
        room_lines.extend(device_lines)

    now      = timezone.localtime(timezone.now())
    date_str = f'{now.day:02d}/{now.month:02d}/{now.year + 543} {now.hour:02d}:{now.minute:02d}'
    header   = f'✅ IoT ปกติทุกอุปกรณ์ — {date_str}' if all_ok else f'⚠️ พบอุปกรณ์ผิดปกติ — {date_str}'
    summary  = f'Online: {total_online}  Offline: {total_offline}  ไม่ทราบ: {total_unknown}'
    lines    = [header, '', summary, ''] + room_lines
    if not all_ok:
        lines += ['', 'กรุณาตรวจสอบและดำเนินการแก้ไข']
    text = '\n'.join(lines)

    group_id = getattr(settings, 'LINE_GROUP_ID', '')
    token    = settings.LINE_CHANNEL_ACCESS_TOKEN
    ok = False
    if group_id and token:
        try:
            resp = requests.post(
                'https://api.line.me/v2/bot/message/push',
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                json={'to': group_id, 'messages': [{'type': 'text', 'text': text}]},
                timeout=10,
            )
            ok = resp.status_code == 200
        except requests.RequestException:
            pass

    if ok:
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'ส่งไม่สำเร็จ ตรวจสอบ LINE_GROUP_ID'})


@staff_required
def manage_iot_refresh(request):
    """
    GET /manage/iot-monitor/refresh/
    คืน JSON สถานะอุปกรณ์ทุกการ์ด (เรียกจาก JS ปุ่ม Refresh)
    """
    from django.http import JsonResponse
    result = []
    for card in _iot_cards():
        devices = []
        for d in card['devices']:
            info = _ha_get_state_manage(d.entity_id)
            devices.append({
                'id':          d.pk,
                'device_name': d.device_name,
                'entity_id':   d.entity_id,
                'state':       info['state'],
                'error':       info['error'],
            })
        result.append({'name': card['name'], 'key': card['key'], 'devices': devices})
    return JsonResponse({'cards': result})


# ── Staff (admin only) ─────────────────────────────────────────────────────────

@admin_required
def manage_staff_list(request):
    users = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True)
    ).order_by('username')
    return render(request, 'booking/manage/staff.html', {'users': users})


@admin_required
def manage_staff_add(request):
    form = StaffAddForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        user = User.objects.create_user(
            username   = cd['username'],
            password   = cd['password1'],
            first_name = cd.get('first_name', ''),
            last_name  = cd.get('last_name', ''),
            email      = cd.get('email', ''),
        )
        user.is_superuser = cd.get('is_superuser', False)
        user.is_staff     = True
        user.save()
        return redirect('manage_staff_list')
    return render(request, 'booking/manage/staff_form.html', {'form': form, 'title': 'เพิ่มเจ้าหน้าที่'})


@admin_required
def manage_staff_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    initial = {
        'first_name':   user.first_name,
        'last_name':    user.last_name,
        'email':        user.email,
        'is_superuser': user.is_superuser,
    }
    form = StaffEditForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        user.first_name   = cd.get('first_name', '')
        user.last_name    = cd.get('last_name', '')
        user.email        = cd.get('email', '')
        user.is_superuser = cd.get('is_superuser', False)
        if cd.get('password1'):
            user.set_password(cd['password1'])
        user.save()
        return redirect('manage_staff_list')
    return render(request, 'booking/manage/staff_form.html', {
        'form': form, 'title': 'แก้ไขเจ้าหน้าที่', 'edit_user': user,
    })


@admin_required
@require_POST
def manage_staff_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk != request.user.pk:
        user.is_active = not user.is_active
        user.save()
    return redirect('manage_staff_list')


# ── Calendar ───────────────────────────────────────────────────────────────────

@staff_required
def manage_calendar(request):
    rooms = Room.objects.filter(is_active=True).order_by('name')
    return render(request, 'booking/manage/calendar.html', {
        'rooms': rooms,
        'events_url': request.build_absolute_uri('/reserv/api/calendar-events/'),
    })


# ── LINE Messaging ─────────────────────────────────────────────────────────────

@staff_required
@require_POST
def manage_send_line_message(request, pk):
    """ส่งข้อความ LINE ถึงผู้ใช้คนเดียว"""
    lu = get_object_or_404(LineUser, pk=pk)
    message = request.POST.get('message', '').strip()
    if message and lu.is_active:
        _push_text(lu.line_user_id, message)
    return redirect('manage_line_user_detail', pk=pk)


@staff_required
@require_POST
def manage_broadcast_line(request):
    """ส่งข้อความ LINE ไปยังผู้ใช้ที่ active ทุกคน"""
    message = request.POST.get('message', '').strip()
    if message:
        users = LineUser.objects.filter(is_active=True)
        for lu in users:
            _push_text(lu.line_user_id, message)
    return redirect('manage_line_users')


# ── External members (บุคคลภายนอกถาวร — ผ่าน NPU API v2) ────────────────────────
# reserv ไม่เก็บข้อมูลสมาชิกถาวรเอง — เป็น proxy ไปยัง api (source of truth)
# รูปดึงผ่าน manage_external_photo (reserv ถือ JWT → stream ให้ browser, ไม่เปิด api สาธารณะ)

@staff_required
def manage_external_list(request):
    """รายการสมาชิกถาวร (filter ตามสถานะ)"""
    status_f = request.GET.get('status', '')
    path = '/v2/external/permanent/'
    if status_f:
        path += f'?status={status_f}'
    resp = _npu_v2_request('GET', path)

    members, error = [], None
    if resp is None:
        error = 'เชื่อมต่อ NPU API ไม่ได้'
    elif resp.status_code == 200:
        members = resp.json().get('results', [])
    else:
        error = f'NPU API ตอบกลับ {resp.status_code}'

    return render(request, 'booking/manage/external_list.html', {
        'members': members,
        'status':  status_f,
        'error':   error,
    })


@staff_required
def manage_external_register(request):
    """ลงทะเบียนสมาชิกถาวร (อัปโหลดรูป) → api สร้างสถานะ pending"""
    if request.method == 'POST':
        citizen_id = request.POST.get('citizen_id', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        photo      = request.FILES.get('photo')

        files = None
        if photo:
            # อ่านเป็น bytes เพื่อให้ retry (กรณี 401) ส่งซ้ำได้
            files = {'photo': (photo.name, photo.read(), photo.content_type)}

        resp = _npu_v2_request(
            'POST', '/v2/external/permanent/register/',
            data={'citizen_id': citizen_id, 'first_name': first_name, 'last_name': last_name},
            files=files,
        )

        if resp is None:
            messages.error(request, 'เชื่อมต่อ NPU API ไม่ได้')
        elif resp.status_code == 201:
            messages.success(request, 'ลงทะเบียนสมาชิกถาวรแล้ว — รอผู้ดูแลอนุมัติ')
            # ใช้ citizen_id จาก api — กรณีเว้นว่าง (บุคคลสำคัญ) api ออกรหัสอ้างอิงขึ้นต้น V ให้
            try:
                citizen_id = resp.json()['member']['citizen_id'] or citizen_id
            except (ValueError, KeyError):
                pass
            return redirect('manage_external_detail', citizen_id=citizen_id)
        elif resp.status_code == 400:
            messages.error(request, 'ข้อมูลไม่ถูกต้อง — ตรวจเลขบัตรประชาชน 13 หลัก และชื่อ-สกุล')
        elif resp.status_code == 409:
            messages.warning(request, 'เลขบัตรนี้เป็นสมาชิกถาวรที่อนุมัติแล้ว')
            return redirect('manage_external_detail', citizen_id=citizen_id)
        else:
            messages.error(request, f'ลงทะเบียนไม่สำเร็จ (NPU API {resp.status_code})')

        return render(request, 'booking/manage/external_form.html', {
            'form': {'citizen_id': citizen_id, 'first_name': first_name, 'last_name': last_name},
        })

    return render(request, 'booking/manage/external_form.html', {'form': {}})


@staff_required
def manage_external_detail(request, citizen_id):
    """รายละเอียด + บัตรสมาชิกถาวร (รูป + QR จาก permanent_code)"""
    resp = _npu_v2_request('GET', f'/v2/external/permanent/{citizen_id}/')
    member, error = None, None
    if resp is None:
        error = 'เชื่อมต่อ NPU API ไม่ได้'
    elif resp.status_code == 200:
        member = resp.json()
    elif resp.status_code == 404:
        error = 'ไม่พบสมาชิกถาวรรายนี้'
    else:
        error = f'NPU API ตอบกลับ {resp.status_code}'

    return render(request, 'booking/manage/external_detail.html', {
        'member':     member,
        'error':      error,
        'citizen_id': citizen_id,
    })


@staff_required
def manage_external_edit(request, citizen_id):
    """แก้ไขชื่อ-สกุล (และรูป ถ้าเลือกไฟล์ใหม่) — ไม่แตะสถานะ/รหัสถาวรที่ api"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        photo      = request.FILES.get('photo')

        files = None
        if photo:
            # อ่านเป็น bytes เพื่อให้ retry (กรณี 401) ส่งซ้ำได้
            files = {'photo': (photo.name, photo.read(), photo.content_type)}

        resp = _npu_v2_request(
            'POST', f'/v2/external/permanent/{citizen_id}/update/',
            data={'first_name': first_name, 'last_name': last_name},
            files=files,
        )

        if resp is None:
            messages.error(request, 'เชื่อมต่อ NPU API ไม่ได้')
        elif resp.status_code == 200:
            messages.success(request, 'แก้ไขข้อมูลสมาชิกแล้ว')
            return redirect('manage_external_detail', citizen_id=citizen_id)
        elif resp.status_code == 400:
            messages.error(request, 'ข้อมูลไม่ถูกต้อง — ต้องกรอกทั้งชื่อและนามสกุล')
        elif resp.status_code == 404:
            messages.error(request, 'ไม่พบสมาชิกถาวรรายนี้')
            return redirect('manage_external_list')
        else:
            messages.error(request, f'แก้ไขไม่สำเร็จ (NPU API {resp.status_code})')

        return render(request, 'booking/manage/external_edit.html', {
            'form': {'first_name': first_name, 'last_name': last_name},
            'citizen_id': citizen_id,
        })

    # GET → ดึงข้อมูลปัจจุบันมาเติมในฟอร์ม
    resp = _npu_v2_request('GET', f'/v2/external/permanent/{citizen_id}/')
    if resp is None:
        messages.error(request, 'เชื่อมต่อ NPU API ไม่ได้')
        return redirect('manage_external_detail', citizen_id=citizen_id)
    if resp.status_code == 404:
        messages.error(request, 'ไม่พบสมาชิกถาวรรายนี้')
        return redirect('manage_external_list')
    if resp.status_code != 200:
        messages.error(request, f'NPU API ตอบกลับ {resp.status_code}')
        return redirect('manage_external_detail', citizen_id=citizen_id)

    member = resp.json()
    return render(request, 'booking/manage/external_edit.html', {
        'form': {'first_name': member.get('first_name', ''), 'last_name': member.get('last_name', '')},
        'member': member,
        'citizen_id': citizen_id,
    })


@staff_required
@require_POST
def manage_external_approve(request, citizen_id):
    """admin อนุมัติ → api ออก permanent_code + active
    ส่งชื่อ staff ที่ล็อกอินไปด้วย (approved_by) เพื่อให้ api เก็บผู้อนุมัติจริงแทน "reserv"
    """
    approved_by = request.user.get_full_name().strip() or request.user.username
    resp = _npu_v2_request(
        'POST', f'/v2/external/permanent/{citizen_id}/approve/',
        data={'approved_by': approved_by},
    )
    if resp is None:
        messages.error(request, 'เชื่อมต่อ NPU API ไม่ได้')
    elif resp.status_code == 200:
        messages.success(request, 'อนุมัติแล้ว — ออกรหัสถาวรเรียบร้อย')
    else:
        messages.error(request, f'อนุมัติไม่สำเร็จ (NPU API {resp.status_code})')
    return redirect('manage_external_detail', citizen_id=citizen_id)


@staff_required
@require_POST
def manage_external_revoke(request, citizen_id):
    """admin ระงับ → รหัสถาวรใช้ไม่ได้ทันที"""
    resp = _npu_v2_request('POST', f'/v2/external/permanent/{citizen_id}/revoke/')
    if resp is None:
        messages.error(request, 'เชื่อมต่อ NPU API ไม่ได้')
    elif resp.status_code == 200:
        messages.success(request, 'ระงับสมาชิกแล้ว')
    else:
        messages.error(request, f'ระงับไม่สำเร็จ (NPU API {resp.status_code})')
    return redirect('manage_external_detail', citizen_id=citizen_id)


@staff_required
@require_POST
def manage_external_delete(request, citizen_id):
    """admin ลบสมาชิกถาวรออกจากระบบ (hard delete ที่ api) — กู้คืนไม่ได้"""
    resp = _npu_v2_request('POST', f'/v2/external/permanent/{citizen_id}/delete/')
    if resp is None:
        messages.error(request, 'เชื่อมต่อ NPU API ไม่ได้')
        return redirect('manage_external_detail', citizen_id=citizen_id)
    if resp.status_code == 200:
        messages.success(request, 'ลบสมาชิกออกจากระบบแล้ว')
        return redirect('manage_external_list')  # เรคคอร์ดถูกลบแล้ว กลับหน้ารายการ
    messages.error(request, f'ลบไม่สำเร็จ (NPU API {resp.status_code})')
    return redirect('manage_external_detail', citizen_id=citizen_id)


@staff_required
def manage_external_photo(request, citizen_id):
    """proxy รูปจาก api (ถือ JWT) → stream ให้ browser; รูปไม่เปิดสาธารณะที่ api"""
    resp = _npu_v2_request('GET', f'/v2/external/permanent/{citizen_id}/photo/')
    if resp is None or resp.status_code != 200:
        return HttpResponse(status=404)
    return HttpResponse(
        resp.content,
        content_type=resp.headers.get('Content-Type', 'application/octet-stream'),
    )
