from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('booking/', views.booking_view, name='booking'),
    path('booking/success/', views.booking_success, name='booking_success'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/calendar-events/', views.calendar_events_api, name='calendar_events'),
]
