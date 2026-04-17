from django.db import models


class Room(models.Model):
    """ห้อง/พื้นที่บริการ"""
    name         = models.CharField(max_length=100)
    booking_name = models.CharField(max_length=50, unique=True)  # key: mini, netflix, canva, meeting_f1, chat-gpt
    description  = models.TextField(blank=True)
    location     = models.CharField(max_length=200)
    capacity     = models.IntegerField()
    open_time    = models.TimeField()
    close_time   = models.TimeField()
    is_active    = models.BooleanField(default=True)
    ha_entity_id = models.CharField(max_length=200, blank=True)  # Phase 2: switch.room_mini

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LineUser(models.Model):
    """
    Cache ข้อมูลผู้ใช้ที่ผูก LINE กับ LDAP แล้ว
    แหล่งข้อมูลจริงอยู่ที่ api.npu.ac.th/api/{userId}
    """
    line_user_id = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    user_ldap    = models.CharField(max_length=100)  # รหัสนักศึกษา หรือ เลขบัตรประชาชน
    user_type    = models.CharField(max_length=50)   # "นักศึกษา" หรือ "บุคลากรภายในมหาวิทยาลัย"
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    is_active    = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.display_name} ({self.user_ldap})"

    @property
    def is_student(self):
        return self.user_type == "นักศึกษา"

    @property
    def is_staff_npu(self):
        return self.user_type == "บุคลากรภายในมหาวิทยาลัย"


class Booking(models.Model):
    """การจองพื้นที่"""

    STATUS_CHOICES = [
        ('confirmed', 'confirmed'),
        ('cancelled', 'cancelled'),
    ]

    # ผู้จอง
    line_user    = models.ForeignKey(LineUser, on_delete=models.PROTECT, related_name='bookings')
    faculty      = models.CharField(max_length=200)
    department   = models.CharField(max_length=200, blank=True)

    # การจอง
    room         = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings')
    group_name   = models.CharField(max_length=200)
    booking_date = models.DateField()
    start_time   = models.TimeField()
    end_time     = models.TimeField()
    attendees    = models.TextField()

    # ระบบ
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at    = models.DateTimeField(auto_now_add=True)
    cancelled_at  = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['room', 'booking_date', 'status']),
        ]
        ordering = ['-booking_date', '-start_time']

    def __str__(self):
        return f"{self.room.name} | {self.booking_date} {self.start_time}-{self.end_time} | {self.line_user.display_name}"


class BookingLog(models.Model):
    """Audit trail"""
    booking   = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='logs')
    action    = models.CharField(max_length=50)  # created, cancelled, accessed, auto_off
    note      = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.booking_id} | {self.action} | {self.timestamp}"
