from django.db import models
from accounts.models import User


class Vehicle(models.Model):
    plate_number = models.CharField(
        primary_key=True, max_length=255)
    model = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    is_vip = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to='vehicle_images/', null=True, blank=True)
    vip_assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='for_vip')
    driver_assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='for_driver')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.plate_number

class OnProcess(models.Model):
    vehicle = models.CharField(max_length=100, null=True, blank=True)
    requester = models.CharField(max_length=255, null=True, blank=True)
    travel_date = models.DateField(null=True, blank=True)
    travel_time = models.TimeField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)
    on_process = models.BooleanField(default=False)

    def __str__(self):
        return self.vehicle