from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0009_checkin_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoomClosure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='วันที่')),
                ('period', models.CharField(
                    choices=[('am', 'ช่วงเช้า (AM)'), ('pm', 'ช่วงบ่าย (PM)'), ('all_day', 'ทั้งวัน')],
                    max_length=10, verbose_name='ช่วงเวลา'
                )),
                ('reason', models.CharField(max_length=200, verbose_name='สาเหตุ')),
                ('is_active', models.BooleanField(default=True, verbose_name='เปิดใช้งาน')),
                ('room', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='closures',
                    to='booking.room',
                    verbose_name='ห้อง'
                )),
            ],
            options={
                'verbose_name': 'ปิดห้องชั่วคราว',
                'verbose_name_plural': 'ปิดห้องชั่วคราว',
                'ordering': ['date', 'room'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='roomclosure',
            unique_together={('room', 'date', 'period')},
        ),
    ]
