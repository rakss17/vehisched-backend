from django.db import models


class Vehicle(models.Model):
    plate_number = models.CharField(
        primary_key=True, max_length=255)
    model = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    is_vip = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to='vehicle_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.plate_number
