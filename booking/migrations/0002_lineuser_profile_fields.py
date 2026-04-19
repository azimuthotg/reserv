from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lineuser',
            name='full_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='lineuser',
            name='faculty',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='lineuser',
            name='department',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='lineuser',
            name='profile_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
