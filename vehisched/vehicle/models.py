from django.db import models


class Vehicle_Status(models.Model):
    description = models.CharField(primary_key=True, max_length=255, choices=[
        ('available', 'Available'),
        ('on trip', 'On Trip'),
        ('unavailable', 'Unavailable'),
    ])

    def __str(self):
        return self.description


class Vehicle(models.Model):
    plate_number = models.CharField(
        primary_key=True, max_length=255)
    vehicle_name = models.CharField(max_length=255, null=True, blank=True)
    vehicle_type = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey(
        Vehicle_Status, on_delete=models.SET_NULL, null=True, blank=True)
    is_vip = models.BooleanField(default=False)
    vehicle_image = models.ImageField(
        upload_to='vehicle_images/', null=True, blank=True)

    def __str__(self):
        return self.plate_number
