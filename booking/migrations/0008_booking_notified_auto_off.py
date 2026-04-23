from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_merge_0005_roomdevice_0006_room_add_how_to_use'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='notified_auto_off',
            field=models.BooleanField(default=False),
        ),
    ]
