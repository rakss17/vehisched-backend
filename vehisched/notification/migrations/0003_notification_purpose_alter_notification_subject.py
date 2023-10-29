# Generated by Django 4.2.6 on 2023-10-16 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0002_notification_travel_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='purpose',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='subject',
            field=models.CharField(max_length=1000, null=True),
        ),
    ]