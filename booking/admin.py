from django.contrib import admin
from .models import Booking, BookingLog, HolidayDate, LineUser, Room


class BookingLogInline(admin.TabularInline):
    model   = BookingLog
    extra   = 0
    readonly_fields = ('action', 'note', 'timestamp')
    can_delete = False


@admin.register(HolidayDate)
class HolidayDateAdmin(admin.ModelAdmin):
    list_display  = ('date', 'description', 'is_active')
    list_editable = ('is_active',)
    list_filter   = ('is_active',)
    ordering      = ('date',)
    search_fields = ('description',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display  = ('name', 'booking_name', 'capacity', 'location', 'open_time', 'close_time', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name', 'booking_name')


@admin.register(LineUser)
class LineUserAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'display_name', 'user_ldap', 'user_type', 'faculty', 'department', 'profile_updated_at')
    search_fields = ('full_name', 'display_name', 'user_ldap', 'line_user_id')
    readonly_fields = ('line_user_id', 'created_at', 'updated_at', 'profile_updated_at')
    list_filter   = ('user_type',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ('room', 'group_name', 'booking_date', 'start_time', 'end_time',
                     'line_user', 'faculty', 'status', 'created_at')
    list_filter   = ('status', 'room', 'booking_date')
    search_fields = ('group_name', 'line_user__full_name', 'line_user__user_ldap', 'faculty')
    date_hierarchy = 'booking_date'
    readonly_fields = ('created_at', 'cancelled_at')
    inlines   = [BookingLogInline]
