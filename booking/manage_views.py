from datetime import date, timedelta
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import HolidayDateForm, RoomForm, StaffAddForm, StaffEditForm
from .models import Booking, BookingLog, HolidayDate, LineUser, Room


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


# ── Bookings ───────────────────────────────────────────────────────────────────

@staff_required
def manage_bookings(request):
    qs = Booking.objects.select_related('room', 'line_user').order_by('-booking_date', '-start_time')

    room_filter   = request.GET.get('room', '')
    date_filter   = request.GET.get('date', '')
    status_filter = request.GET.get('status', 'confirmed')
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
        booking.status       = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancel_reason = reason
        booking.save()
        BookingLog.objects.create(booking=booking, action='cancelled', note=reason)
    return redirect('manage_bookings')


# ── Holidays ───────────────────────────────────────────────────────────────────

@staff_required
def manage_holidays(request):
    year = int(request.GET.get('year', date.today().year))
    holidays = HolidayDate.objects.filter(date__year=year).order_by('date')
    years = list(range(date.today().year, date.today().year + 3))
    return render(request, 'booking/manage/holidays.html', {
        'holidays': holidays,
        'year': year,
        'years': years,
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


# ── LINE Users ─────────────────────────────────────────────────────────────────

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
