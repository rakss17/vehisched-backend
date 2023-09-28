from django.db import models
from django.contrib.auth.models import AbstractUser



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
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, null=True, blank=True)
    mobile_number = models.BigIntegerField(null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username


class Driver_Status(models.Model):
    user = models.OneToOneField(
        'User', on_delete=models.CASCADE, primary_key=True)
    status = models.CharField(max_length=255, choices=[
        ('Available', 'Available'),
        ('On trip', 'On Trip'),
        ('Unavailable', 'Unavailable')
    ], default='Available')


