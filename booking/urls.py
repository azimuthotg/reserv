from django.urls import path
from . import views

urlpatterns = [
    path('booking/',          views.booking_page,    name='booking'),
    path('booking/success/',  views.booking_success, name='booking_success'),
    path('api/check-user/',   views.check_user,      name='check_user'),
    path('api/booking/',           views.create_booking,   name='create_booking'),
    path('api/bookings-by-date/',  views.bookings_by_date, name='bookings_by_date'),
]
