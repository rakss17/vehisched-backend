# Generated by Django 4.2.4 on 2023-09-01 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_role_role_name_alter_user_middle_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='role_name',
            field=models.CharField(choices=[('admin', 'Admin'), ('requester', 'Requester'), ('vip', 'VIP'), ('driver', 'Driver'), ('gate_guard', 'Gate Guard'), ('office_staff', 'Office Staff')], max_length=255),
        ),
    ]