# Generated by Django 4.2.4 on 2023-09-03 05:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicle', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicle_Status',
            fields=[
                ('description', models.CharField(max_length=255, primary_key=True, serialize=False)),
            ],
        ),
    ]