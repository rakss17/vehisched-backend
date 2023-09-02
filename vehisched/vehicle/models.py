from django.db import models


class Vehicle(models.Model):
    plate_number = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)
    vehicle_type = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.IntegerField()

    def __str__(self):
        return self.plate_number
