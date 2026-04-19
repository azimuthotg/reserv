from django.db import models


class Room(models.Model):
    name         = models.CharField(max_length=100)
    booking_name = models.CharField(
        max_length=50, unique=True,
        help_text='key ที่ใช้ใน URL เช่น netflix, mini, canva, chat-gpt, meeting_f1'
    )
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
        return f'{self.name} ({self.booking_name})'


class LineUser(models.Model):
    line_user_id     = models.CharField(max_length=100, unique=True)
    display_name     = models.CharField(max_length=200)          # ชื่อ LINE
    user_ldap        = models.CharField(max_length=100)
    user_type        = models.CharField(max_length=50)
    # Profile จริงจาก NPU API
    full_name        = models.CharField(max_length=200, blank=True)  # ชื่อ-นามสกุลจริง
    faculty          = models.CharField(max_length=200, blank=True)
    department       = models.CharField(max_length=200, blank=True)
    profile_updated_at = models.DateTimeField(null=True, blank=True)
    # Meta
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    is_active    = models.BooleanField(default=True)

    def __str__(self):
        name = self.full_name or self.display_name
        return f'{name} ({self.user_ldap})'


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
        return f'{self.room.name} — {self.booking_date} {self.start_time:%H:%M}-{self.end_time:%H:%M}'


class BookingLog(models.Model):
    booking   = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='logs')
    action    = models.CharField(max_length=50)
    note      = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.booking} — {self.action}'
