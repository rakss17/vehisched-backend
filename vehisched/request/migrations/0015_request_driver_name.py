# Generated by Django 4.2.5 on 2023-10-05 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0014_remove_request_is_viewed'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='driver_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
