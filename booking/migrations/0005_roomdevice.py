from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_notification_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoomDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_name', models.CharField(max_length=100, verbose_name='ชื่ออุปกรณ์')),
                ('entity_id', models.CharField(max_length=200, verbose_name='Entity ID (Home Assistant)')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='ลำดับ')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='booking.room')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
    ]
