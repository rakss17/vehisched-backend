# Generated by Django 4.2.4 on 2023-09-02 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('plate_number', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('vehicle_type', models.CharField(blank=True, max_length=255, null=True)),
                ('capacity', models.IntegerField()),
            ],
        ),
    ]
