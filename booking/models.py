from datetime import date

from django.db import models
from django.utils import timezone


class Room(models.Model):
    name         = models.CharField(max_length=100)
    booking_name = models.CharField(
        max_length=50, unique=True,
        help_text='key ที่ใช้ใน URL เช่น netflix, mini, canva, chat-gpt, meeting_f1'
    )
    description      = models.TextField(blank=True)
    location         = models.CharField(max_length=200)
    capacity         = models.IntegerField()
    min_attendees    = models.IntegerField(default=1, help_text='จำนวนผู้ใช้ขั้นต่ำ')
    # ⚠️ เลิกใช้แล้ว (2026-08-09) — ระบบไม่เคยบังคับตามฟิลด์นี้ เพดานจริงคือ
    # service_hours.MAX_BOOKING_MINUTES เท่ากันทุกห้อง · คงฟิลด์ไว้เพื่อไม่ต้อง migrate
    # แต่ถอดออกจาก RoomForm และหน้าแสดงผลแล้ว ห้ามนำกลับมาใช้โดยไม่บังคับใช้จริง
    max_booking_hours = models.IntegerField(default=2, help_text='เวลาจองสูงสุดต่อครั้ง (ชั่วโมง)')
    eligible_users   = models.TextField(blank=True, help_text='ผู้มีสิทธิ์ใช้บริการ เช่น นักศึกษา, บุคลากร')
    facilities       = models.TextField(blank=True, help_text='อุปกรณ์/สิ่งอำนวยความสะดวก (แต่ละรายการขึ้นบรรทัดใหม่)')
    rules            = models.TextField(blank=True, help_text='กฎระเบียบการใช้ห้อง (แต่ละข้อขึ้นบรรทัดใหม่)')
    how_to_use       = models.TextField(blank=True, help_text='ขั้นตอนการใช้บริการ (แต่ละขั้นตอนขึ้นบรรทัดใหม่)')
    open_time        = models.TimeField()
    close_time       = models.TimeField()
    is_active        = models.BooleanField(default=True)
    allow_overlap    = models.BooleanField(
        default=False,
        help_text='ยอมให้ผู้ใช้คนเดียวจองห้องนี้ทับเวลากับห้องอื่นได้ '
                  '(สำหรับพื้นที่กลุ่ม/พื้นที่เปิด เช่น โต๊ะประชุม)'
    )
    is_online        = models.BooleanField(
        default=False,
        help_text='บริการออนไลน์ที่ไม่ต้องเข้าอาคาร (เช่น เครื่องเสมือน Canva/Netflix) '
                  'จองได้ทุกวันตามเวลาเปิด-ปิดของห้องนี้ ไม่ถูกจำกัดด้วยเวลาเปิดอาคารหรือวันหยุด'
    )
    day_round_enabled = models.BooleanField(
        default=True,
        help_text='เปิดจองรอบกลางวัน (08:30–17:00) หรือไม่ — ปิดเมื่อทรัพยากรถูกใช้ที่จุดบริการอื่น '
                  'ในเวลาราชการ เช่น บัญชี Netflix ที่ให้บริการอยู่ที่ Edutainment Zone ช่วงกลางวัน'
    )
    ha_entity_id     = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.booking_name})'


class RoomDevice(models.Model):
    # room ว่างได้ = อุปกรณ์หลังบ้านที่ไม่สังกัดห้องจอง (เช่น flip gate ทางเข้า)
    # อุปกรณ์แบบนี้จับกลุ่มด้วย group_name และเห็นเฉพาะหน้า IoT Monitor ของ admin เท่านั้น
    room        = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='devices',
                                    null=True, blank=True, verbose_name='ห้อง')
    group_name  = models.CharField(max_length=100, blank=True, verbose_name='กลุ่มอุปกรณ์ (ใช้เมื่อไม่สังกัดห้อง)')
    device_name = models.CharField(max_length=100, verbose_name='ชื่ออุปกรณ์')
    entity_id   = models.CharField(max_length=200, verbose_name='Entity ID (Home Assistant)')
    order       = models.PositiveSmallIntegerField(default=0, verbose_name='ลำดับ')

    class Meta:
        ordering = ['order', 'id']

    @property
    def owner_name(self):
        if self.room_id:
            return self.room.name
        return self.group_name or 'ไม่ระบุกลุ่ม'

    def __str__(self):
        return f'{self.owner_name} — {self.device_name}'


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
    # LINE notification tracking
    notified_start    = models.BooleanField(default=False)  # แจ้งจองสำเร็จ
    notified_15min    = models.BooleanField(default=False)  # แจ้งก่อนเริ่ม 15 นาที
    notified_10min    = models.BooleanField(default=False)  # แจ้งก่อนหมด 10 นาที
    notified_auto_off = models.BooleanField(default=False)  # ปิดอุปกรณ์อัตโนมัติเมื่อหมดเวลา
    # Check-in
    checked_in    = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-booking_date', '-start_time']
        indexes  = [models.Index(fields=['room', 'booking_date', 'status'])]

    def __str__(self):
        return f'{self.room.name} — {self.booking_date} {self.start_time:%H:%M}-{self.end_time:%H:%M}'


class RoomClosure(models.Model):
    PERIOD_CHOICES = [
        ('am',      'ช่วงเช้า (AM)'),
        ('pm',      'ช่วงบ่าย (PM)'),
        ('all_day', 'ทั้งวัน'),
    ]
    room      = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='closures',
                                  verbose_name='ห้อง')
    date      = models.DateField(verbose_name='วันที่')
    period    = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name='ช่วงเวลา')
    reason    = models.CharField(max_length=200, verbose_name='สาเหตุ')
    is_active = models.BooleanField(default=True, verbose_name='เปิดใช้งาน')

    class Meta:
        ordering        = ['date', 'room']
        verbose_name    = 'ปิดห้องชั่วคราว'
        verbose_name_plural = 'ปิดห้องชั่วคราว'
        unique_together = [['room', 'date', 'period']]

    def __str__(self):
        return f'{self.room.name} — {self.date} ({self.get_period_display()})'


class HolidayDate(models.Model):
    SOURCE_MANUAL = 'manual'
    SOURCE_AUTO   = 'auto'
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, 'เจ้าหน้าที่เพิ่มเอง'),
        (SOURCE_AUTO,   'ดึงจากปฏิทินวันหยุดอัตโนมัติ'),
    ]

    date        = models.DateField(unique=True, verbose_name='วันที่')
    description = models.CharField(max_length=200, verbose_name='เหตุผล/ชื่อวันหยุด')
    is_active   = models.BooleanField(default=True, verbose_name='เปิดใช้งาน')
    # แยกแถวที่ระบบดึงมาเอง ออกจากแถวที่เจ้าหน้าที่กรอก — sync รอบถัดไปจะไม่แตะของที่คนแก้
    source      = models.CharField(max_length=10, choices=SOURCE_CHOICES,
                                   default=SOURCE_MANUAL, verbose_name='ที่มา')

    class Meta:
        ordering     = ['date']
        verbose_name = 'วันหยุด'
        verbose_name_plural = 'วันหยุด'

    def __str__(self):
        return f'{self.date} — {self.description}'


# sync ตั้งใจให้รันเดือนละครั้ง เผื่อพลาดได้อีกครึ่งเดือนก่อนจะถือว่าข้อมูลเก่า
HOLIDAY_SYNC_STALE_DAYS = 45
# ตารางควรมีวันหยุดครอบไปข้างหน้าอย่างน้อย 2 เดือน — จองล่วงหน้าได้แค่ 7 วันเปิดบริการ
# แต่เผื่อเวลาให้เจ้าหน้าที่ตรวจฉบับร่างและแจ้งผู้ใช้ล่วงหน้าด้วย
HOLIDAY_HORIZON_MIN_DAYS = 60


class HolidaySyncRun(models.Model):
    """บันทึกทุกครั้งที่ดึงปฏิทินวันหยุดสำเร็จ — **แม้รอบนั้นจะไม่มีวันใหม่เลย**

    มีไว้ตอบคำถามที่ตาราง `HolidayDate` ตอบไม่ได้ คือ "ข้อมูลวันหยุดเก่าแค่ไหน"
    แถบเตือนบนแดชบอร์ดเดิมขึ้นเฉพาะเมื่อ *มี* ฉบับร่างค้างอยู่ แดชบอร์ดที่เงียบเพราะ
    เจ้าหน้าที่ตรวจครบแล้ว จึงหน้าตาเหมือนกันเป๊ะกับที่เงียบเพราะไม่มีใครกดดึงข้อมูล
    มาเลยหลายเดือน — รูปแบบเดียวกับตอนที่ตารางค้างตั้งแต่ 3 มิ.ย. 2569 จนนักศึกษา
    จอง MINI THEATER วันแม่ 12 ส.ค. ได้ 2 รายการ

    ห้ามใช้ `HolidayDate` วันที่สร้างล่าสุดแทน — sync ที่รันตรงเวลาแต่ไม่เจอวันใหม่
    จะดูเหมือนไม่เคยรัน ซึ่งเป็นสัญญาณเตือนผิดตัว
    """
    TRIGGER_BUTTON    = 'button'
    TRIGGER_COMMAND   = 'command'
    TRIGGER_BOOTSTRAP = 'bootstrap'
    TRIGGER_CHOICES = [
        (TRIGGER_BUTTON,    'เจ้าหน้าที่กดปุ่มในหน้าจัดการวันหยุด'),
        (TRIGGER_COMMAND,   'คำสั่ง sync_holidays (ตั้งเวลา)'),
        (TRIGGER_BOOTSTRAP, 'บันทึกย้อนหลังตอนติดตั้งฟีเจอร์'),
    ]

    synced_at     = models.DateTimeField(auto_now_add=True, verbose_name='ดึงเมื่อ')
    created_count = models.PositiveIntegerField(default=0, verbose_name='ได้วันใหม่')
    trigger       = models.CharField(max_length=20, choices=TRIGGER_CHOICES,
                                     default=TRIGGER_BUTTON, verbose_name='สั่งจาก')

    class Meta:
        ordering     = ['-synced_at']
        verbose_name = 'ประวัติการดึงวันหยุด'
        verbose_name_plural = 'ประวัติการดึงวันหยุด'

    def __str__(self):
        return f'{self.synced_at:%Y-%m-%d %H:%M} — ได้ใหม่ {self.created_count} วัน'

    @classmethod
    def data_status(cls):
        """สรุปว่า "ข้อมูลวันหยุดในระบบยังเชื่อถือได้อยู่ไหม" ให้แดชบอร์ดและหน้าจัดการใช้ร่วมกัน

        เตือน 2 กรณีที่ต่างกัน:
        - `is_stale`      ไม่ได้ดึงมานาน → วันหยุดที่ ครม. ประกาศเพิ่มกลางปียังไม่เข้าระบบ
        - `horizon_short` ข้อมูลที่มีครอบไปข้างหน้าไม่พอ → อีกไม่นานจะไม่มีวันหยุดให้บล็อกเลย
        """
        today   = date.today()
        last    = cls.objects.first()                       # Meta.ordering = ล่าสุดก่อน
        horizon = HolidayDate.objects.aggregate(m=models.Max('date'))['m']

        # แปลงเป็นเวลาไทยก่อนเสมอ — synced_at เก็บเป็น UTC ถ้าอ่านตรง ๆ วันจะเพี้ยนได้ 1 วัน
        last_date    = timezone.localtime(last.synced_at).date() if last else None
        days_since   = (today - last_date).days if last_date else None
        horizon_days = (horizon - today).days if horizon else None

        is_stale      = days_since is None or days_since > HOLIDAY_SYNC_STALE_DAYS
        horizon_short = horizon_days is None or horizon_days < HOLIDAY_HORIZON_MIN_DAYS

        return {
            'last_run':      last,
            'last_date':     last_date,
            'days_since':    days_since,
            'horizon':       horizon,
            'horizon_days':  horizon_days,
            'is_stale':      is_stale,
            'horizon_short': horizon_short,
            'stale_days':    HOLIDAY_SYNC_STALE_DAYS,
            'needs_attention': is_stale or horizon_short,
        }


class BookingLog(models.Model):
    booking   = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='logs')
    action    = models.CharField(max_length=50)
    note      = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.booking} — {self.action}'
