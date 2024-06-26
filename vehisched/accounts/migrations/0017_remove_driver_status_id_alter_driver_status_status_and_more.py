# Generated by Django 4.2.5 on 2023-10-01 07:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_rename_driverstatus_driver_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='driver_status',
            name='id',
        ),
        migrations.AlterField(
            model_name='driver_status',
            name='status',
            field=models.CharField(choices=[('Available', 'Available'), ('On trip', 'On Trip'), ('Unavailable', 'Unavailable')], default='Available', max_length=255),
        ),
        migrations.AlterField(
            model_name='driver_status',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
