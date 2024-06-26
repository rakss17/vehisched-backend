# Generated by Django 4.2.7 on 2023-11-24 09:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0025_alter_request_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='CSM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_type', models.CharField(blank=True, max_length=244, null=True)),
                ('region_of_residence', models.CharField(blank=True, max_length=244, null=True)),
                ('service_availed', models.CharField(blank=True, max_length=244, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, null=True)),
                ('answer', models.TextField(blank=True, null=True)),
                ('csm', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='request.csm')),
            ],
        ),
        migrations.AddField(
            model_name='request',
            name='csm',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='request.csm'),
        ),
    ]
