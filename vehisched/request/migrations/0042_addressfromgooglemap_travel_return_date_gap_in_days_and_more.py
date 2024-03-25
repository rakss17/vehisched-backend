# Generated by Django 4.2.9 on 2024-03-25 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0041_addressfromgooglemap_travel_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='addressfromgooglemap',
            name='travel_return_date_gap_in_days',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='addressfromgooglemap',
            name='travel_return_date_gap_in_hours',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='addressfromgooglemap',
            name='travel_return_date_gap_in_minutes',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='addressfromgooglemap',
            name='travel_return_date_gap_in_seconds',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
