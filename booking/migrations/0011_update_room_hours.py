import datetime
from django.db import migrations


def set_room_hours(apps, schema_editor):
    """อัปเดตเวลาเปิด-ปิดทุกห้องเป็น 08:30–16:30 ตามเวลาบริการจริงของสำนักวิทยบริการ"""
    Room = apps.get_model('booking', 'Room')
    Room.objects.all().update(
        open_time=datetime.time(8, 30),
        close_time=datetime.time(16, 30),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0010_roomclosure'),
    ]

    operations = [
        migrations.RunPython(set_room_hours, migrations.RunPython.noop),
    ]
