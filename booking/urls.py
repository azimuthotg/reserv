from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('booking/', views.booking_view, name='booking'),
    path('booking/success/', views.booking_success, name='booking_success'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/calendar-events/', views.calendar_events_api, name='calendar_events'),
    path('api/set-session/', views.set_session_api, name='set_session'),
    path('api/check-user/', views.check_user_api, name='check_user'),
]
