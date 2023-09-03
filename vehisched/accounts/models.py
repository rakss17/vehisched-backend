from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from rest_framework.authtoken.models import Token


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=255, choices=[
        ('admin', 'Admin'),
        ('requester', 'Requester'),
        ('vip', 'VIP'),
        ('driver', 'Driver'),
        ('gate guard', 'Gate Guard'),
        ('office staff', 'Office Staff'),
    ])

    def __str__(self):
        return self.role_name


class User(AbstractUser):
    role = models.OneToOneField(
        Role, on_delete=models.CASCADE, null=True, blank=True)
    mobile_number = models.BigIntegerField(null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username


class DriverStatus(models.Model):
    user = models.OneToOneField(
        'User', on_delete=models.CASCADE, related_name='driver_status')
    status = models.CharField(max_length=255, choices=[
        ('available', 'Available'),
        ('on trip', 'On Trip'),
        ('unavailable', 'Unavailable')
    ], default='Available')
