# Generated by Django 4.2.6 on 2023-10-26 08:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vehicle', '0014_delete_vehicle_status_and_more'),
        ('request', '0018_request_distance'),
    ]

    operations = [
        migrations.CreateModel(
            name='Type',
            fields=[
                ('type_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(choices=[('Round Trip', 'Round Trip'), ('One-way - Drop', 'One-way - Drop'), ('One-way - Fetch', 'One-way - Fetch')], max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Vehicle_Driver_Status',
            fields=[
                ('vehicle_driver_status_id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('Available', 'Available'), ('Reserved - Assigned', 'Reserved - Assigned'), ('On Trip', 'On Trip'), ('Unavailable', 'Unavailable')], max_length=255)),
                ('driver_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('plate_number', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vehicle.vehicle')),
            ],
        ),
        migrations.RenameField(
            model_name='request',
            old_name='created_at',
            new_name='date_reserved',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='office_or_dept',
            new_name='office',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='passenger_names',
            new_name='passenger_name',
        ),
        migrations.RemoveField(
            model_name='request',
            name='category',
        ),
        migrations.RemoveField(
            model_name='request',
            name='is_approved',
        ),
        migrations.RemoveField(
            model_name='request',
            name='sub_category',
        ),
        migrations.AlterField(
            model_name='request',
            name='driver_name',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='driver_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='request',
            name='requester_name',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='requester_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='request',
            name='status',
            field=models.CharField(blank=True, choices=[('Approved', 'Approved'), ('Pending', 'Pending'), ('Canceled', 'Canceled'), ('Rescheduled', 'Rescheduled'), ('Completed', 'Completed'), ('Rejected', 'Rejected')], max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='Request_Status',
        ),
        migrations.DeleteModel(
            name='Sub_Category',
        ),
        migrations.AddField(
            model_name='request',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='request.type'),
        ),
        migrations.AddField(
            model_name='request',
            name='vehicle_driver_status_id',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='request.vehicle_driver_status'),
        ),
    ]
