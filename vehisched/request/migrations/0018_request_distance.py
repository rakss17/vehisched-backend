# Generated by Django 4.2.6 on 2023-10-21 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0017_category_sub_category_request_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='distance',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
