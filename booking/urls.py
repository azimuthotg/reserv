from django.urls import path
from . import views, manage_views

urlpatterns = [
    # ── Booking (LIFF) ────────────────────────────────────────────────────────
    path('booking/',         views.booking_page,    name='booking'),
    path('booking/success/', views.booking_success, name='booking_success'),

    # ── APIs ──────────────────────────────────────────────────────────────────
    path('api/check-user/',        views.check_user,       name='check_user'),
    path('api/booking/',           views.create_booking,   name='create_booking'),
    path('api/bookings-by-date/',  views.bookings_by_date, name='bookings_by_date'),

    # ── Staff Portal ──────────────────────────────────────────────────────────
    path('manage/login/',   manage_views.manage_login,   name='manage_login'),
    path('manage/logout/',  manage_views.manage_logout,  name='manage_logout'),
    path('manage/',         manage_views.manage_dashboard, name='manage_dashboard'),

    # Bookings
    path('manage/bookings/',                    manage_views.manage_bookings,       name='manage_bookings'),
    path('manage/bookings/<int:pk>/cancel/',    manage_views.manage_booking_cancel, name='manage_booking_cancel'),

    # Holidays
    path('manage/holidays/',                    manage_views.manage_holidays,       name='manage_holidays'),
    path('manage/holidays/add/',                manage_views.manage_holiday_add,    name='manage_holiday_add'),
    path('manage/holidays/<int:pk>/edit/',      manage_views.manage_holiday_edit,   name='manage_holiday_edit'),
    path('manage/holidays/<int:pk>/delete/',    manage_views.manage_holiday_delete, name='manage_holiday_delete'),

    # LINE Users
    path('manage/line-users/',  manage_views.manage_line_users, name='manage_line_users'),

    # Rooms (admin only)
    path('manage/rooms/',                   manage_views.manage_rooms,       name='manage_rooms'),
    path('manage/rooms/add/',               manage_views.manage_room_add,    name='manage_room_add'),
    path('manage/rooms/<int:pk>/edit/',     manage_views.manage_room_edit,   name='manage_room_edit'),
    path('manage/rooms/<int:pk>/toggle/',   manage_views.manage_room_toggle, name='manage_room_toggle'),

    # Staff (admin only)
    path('manage/staff/',                   manage_views.manage_staff_list,  name='manage_staff_list'),
    path('manage/staff/add/',               manage_views.manage_staff_add,   name='manage_staff_add'),
    path('manage/staff/<int:pk>/edit/',     manage_views.manage_staff_edit,  name='manage_staff_edit'),
    path('manage/staff/<int:pk>/toggle/',   manage_views.manage_staff_toggle,name='manage_staff_toggle'),
]
