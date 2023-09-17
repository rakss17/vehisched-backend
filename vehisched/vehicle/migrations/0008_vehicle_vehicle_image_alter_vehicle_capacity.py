# Generated by Django 4.2.5 on 2023-09-16 03:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicle', '0007_rename_name_vehicle_vehicle_name_vehicle_is_vip'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='vehicle_image',
            field=models.ImageField(blank=True, null=True, upload_to='vehicle_images/'),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='capacity',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
