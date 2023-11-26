# Generated by Django 4.2.7 on 2023-11-24 09:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0026_csm_question_request_csm'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='request',
            name='csm',
        ),
        migrations.AddField(
            model_name='csm',
            name='request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='request.request'),
        ),
    ]