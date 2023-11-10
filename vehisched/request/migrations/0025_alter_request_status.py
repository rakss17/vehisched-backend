# Generated by Django 4.2.6 on 2023-11-09 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0024_alter_request_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='status',
            field=models.CharField(blank=True, choices=[('Approved', 'Approved'), ('Approved - Alterate Vehicle', 'Approved - Alterate Vehicle'), ('Pending', 'Pending'), ('Canceled', 'Canceled'), ('Rescheduled', 'Rescheduled'), ('Completed', 'Completed'), ('Rejected', 'Rejected'), ('Awaiting Vehicle Alteration', 'Awaiting Vehicle Alteration'), ('Awaiting Rescheduling', 'Awaiting Rescheduling'), ('Ongoing Vehicle Maintenance', 'Ongoing Vehicle Maintenance'), ('Driver Absence', 'Driver Absence')], max_length=255, null=True),
        ),
    ]
