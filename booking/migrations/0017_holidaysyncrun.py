from django.db import migrations, models


def bootstrap_first_run(apps, schema_editor):
    """ถ้ามีวันหยุดที่ระบบดึงมาอยู่แล้ว ให้ถือว่าเพิ่งดึงตอนติดตั้งฟีเจอร์นี้

    ไม่งั้นแดชบอร์ดจะขึ้นเตือน "ยังไม่เคยดึงเลย" ทันทีที่ deploy ทั้งที่เพิ่งดึงไปจริง ๆ
    — สัญญาณเตือนผิดตัวตั้งแต่วันแรกทำให้เจ้าหน้าที่เลิกเชื่อแถบเตือน
    """
    HolidayDate    = apps.get_model('booking', 'HolidayDate')
    HolidaySyncRun = apps.get_model('booking', 'HolidaySyncRun')
    if HolidayDate.objects.filter(source='auto').exists():
        HolidaySyncRun.objects.create(created_count=0, trigger='bootstrap')


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0016_holidaydate_source'),
    ]

    operations = [
        migrations.CreateModel(
            name='HolidaySyncRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('synced_at', models.DateTimeField(auto_now_add=True, verbose_name='ดึงเมื่อ')),
                ('created_count', models.PositiveIntegerField(default=0, verbose_name='ได้วันใหม่')),
                ('trigger', models.CharField(
                    choices=[('button', 'เจ้าหน้าที่กดปุ่มในหน้าจัดการวันหยุด'),
                             ('command', 'คำสั่ง sync_holidays (ตั้งเวลา)'),
                             ('bootstrap', 'บันทึกย้อนหลังตอนติดตั้งฟีเจอร์')],
                    default='button', max_length=20, verbose_name='สั่งจาก')),
            ],
            options={
                'verbose_name': 'ประวัติการดึงวันหยุด',
                'verbose_name_plural': 'ประวัติการดึงวันหยุด',
                'ordering': ['-synced_at'],
            },
        ),
        migrations.RunPython(bootstrap_first_run, migrations.RunPython.noop),
    ]
