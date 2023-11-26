# Generated by Django 4.2.7 on 2023-11-26 12:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0031_csm_email_address_csm_suggestions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='csm',
        ),
        migrations.AddField(
            model_name='csm',
            name='question',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='request.question'),
        ),
    ]
