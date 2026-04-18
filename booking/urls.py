from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('liff/', views.liff_entry_view, name='liff_entry'),
    path('api/liff-login/', views.liff_login_api, name='liff_login'),
    path('register/', views.register_view, name='register'),
    path('booking/', views.booking_view, name='booking'),
    path('booking/success/', views.booking_success, name='booking_success'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/calendar-events/', views.calendar_events_api, name='calendar_events'),
]
