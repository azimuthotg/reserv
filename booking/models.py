from django.db import models


class Room(models.Model):
    name         = models.CharField(max_length=100)
    booking_name = models.CharField(max_length=50, unique=True)
    description  = models.TextField(blank=True)
    location     = models.CharField(max_length=200)
    capacity     = models.IntegerField()
    open_time    = models.TimeField()
    close_time   = models.TimeField()
    is_active    = models.BooleanField(default=True)
    ha_entity_id = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LineUser(models.Model):
    line_user_id = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    user_ldap    = models.CharField(max_length=100)
    user_type    = models.CharField(max_length=50)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    is_active    = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.display_name} ({self.user_ldap})"


class Booking(models.Model):
    STATUS_CHOICES = [('confirmed', 'confirmed'), ('cancelled', 'cancelled')]

    room         = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings')
    line_user    = models.ForeignKey(LineUser, on_delete=models.PROTECT, related_name='bookings')
    faculty      = models.CharField(max_length=200)
    department   = models.CharField(max_length=200, blank=True)
    group_name   = models.CharField(max_length=200)
    booking_date = models.DateField()
    start_time   = models.TimeField()
    end_time     = models.TimeField()
    attendees    = models.TextField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at   = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-booking_date', '-start_time']
        indexes  = [models.Index(fields=['room', 'booking_date', 'status'])]

    def __str__(self):
        return f"{self.room} — {self.booking_date} {self.start_time}"


class BookingLog(models.Model):
    booking   = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='logs')
    action    = models.CharField(max_length=50)
    note      = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
