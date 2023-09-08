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
    plate_number = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)
    vehicle_type = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.IntegerField()
    status = models.ForeignKey(
        Vehicle_Status, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.plate_number
