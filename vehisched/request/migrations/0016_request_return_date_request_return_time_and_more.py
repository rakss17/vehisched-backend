# Generated by Django 4.2.5 on 2023-10-10 10:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0015_request_driver_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='return_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='request',
            name='return_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='request',
            name='travel_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='request',
            name='travel_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]