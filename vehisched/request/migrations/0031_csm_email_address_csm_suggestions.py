# Generated by Django 4.2.7 on 2023-11-26 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0030_remove_question_answers_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='csm',
            name='email_address',
            field=models.CharField(blank=True, max_length=244, null=True),
        ),
        migrations.AddField(
            model_name='csm',
            name='suggestions',
            field=models.TextField(blank=True, null=True),
        ),
    ]
