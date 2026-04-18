from django.urls import path
from . import views

urlpatterns = [
    path('booking/',              views.booking_page, name='booking'),
    path('api/check-user/',       views.check_user,   name='check_user'),
]
