# Generated by Django 4.2.7 on 2024-01-28 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0037_request_merged_with'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='main_merge',
            field=models.BooleanField(default=False),
        ),
    ]