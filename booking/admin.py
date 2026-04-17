from django.contrib import admin
from .models import Room, LineUser, Booking, BookingLog


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'booking_name', 'location', 'capacity', 'open_time', 'close_time', 'is_active']
    list_filter = ['is_active', 'location']
    search_fields = ['name', 'booking_name']


@admin.register(LineUser)
class LineUserAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user_ldap', 'user_type', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_active']
    search_fields = ['display_name', 'user_ldap', 'line_user_id']
    readonly_fields = ['created_at', 'updated_at']


class BookingLogInline(admin.TabularInline):
    model = BookingLog
    extra = 0
    readonly_fields = ['action', 'note', 'timestamp']
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['room', 'booking_date', 'start_time', 'end_time', 'line_user', 'group_name', 'status', 'created_at']
    list_filter = ['status', 'room', 'booking_date']
    search_fields = ['group_name', 'line_user__display_name', 'line_user__user_ldap']
    readonly_fields = ['created_at', 'cancelled_at']
    date_hierarchy = 'booking_date'
    inlines = [BookingLogInline]


@admin.register(BookingLog)
class BookingLogAdmin(admin.ModelAdmin):
    list_display = ['booking', 'action', 'note', 'timestamp']
    list_filter = ['action']
    readonly_fields = ['timestamp']
