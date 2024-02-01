from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os


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
    

class Driver_Status(models.Model):
    description = models.CharField(primary_key=True,max_length=255, choices=[
        ('Available', 'Available'),
        ('On trip', 'On Trip'),
        ('Unavailable', 'Unavailable'),
        ('Assigned', 'Assigned')
    ])

    def __str__(self):
        return self.description

class Office(models.Model):
    office_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, null=True, blank=True)
    mobile_number = models.BigIntegerField(null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username


@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    if sender.name == 'accounts':
        Custom_User = User
        username = os.getenv('DJANGO_ADMIN_USERNAME')
        email = os.getenv('DJANGO_ADMIN_EMAIL')
        password = os.getenv('DJANGO_ADMIN_PASSWORD')
        role = Role.objects.get(role_name='admin')

        if not Custom_User.objects.filter(username=username).exists():
            # Create the superuser with is_active set to False
            superuser = Custom_User.objects.create_superuser(
                username=username, email=email, password=password, role=role)

            # Activate the superuser
            superuser.is_active = True
            print('Created admin account')
            superuser.save()

