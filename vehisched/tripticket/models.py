from django.db import models
from accounts.models import User, Driver_Status
from vehicle.models import Vehicle, Vehicle_Status
from request.models import Request


class FuelStatus(models.Model):
    fuel_status_id = models.AutoField(primary_key=True)
    tank_balance = models.IntegerField(null=True, blank=True)
    office_stock_issued = models.IntegerField(null=True, blank=True)
    deduct_used_during_trip = models.IntegerField(null=True, blank=True)
    tank_balance_after_trip = models.IntegerField(null=True, blank=True)
    lubricating_office = models.IntegerField(null=True, blank=True)


class Speedometer(models.Model):
    speedometer_id = models.AutoField(primary_key=True)
    reading_after_trip = models.IntegerField(null=True, blank=True)
    beginning_of_trip = models.IntegerField(null=True, blank=True)
    distance_traveled = models.IntegerField(null=True, blank=True)

class TripTicket_Status(models.Model):
    description = models.CharField(primary_key=True, max_length=255, choices=[
        ('Scheduled', 'Scheduled'),
        ('Canceled', 'Canceled'),
        ('Reschedule', 'Reschedule'),
        ('Completed', 'Completed'),
    ])

    def __str__(self):
        return self.description

class TripTicket(models.Model):
    driver_name = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    plate_number = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    authorized_passenger = models.CharField(
        max_length=255, null=True, blank=True)
    request_number = models.OneToOneField(
        Request, on_delete=models.SET_NULL, null=True, blank=True)
    departure_time_from_office = models.TimeField(null=True, blank=True)
    arrival_time_to_destination = models.TimeField(null=True, blank=True)
    departure_time_from_destination = models.TimeField(null=True, blank=True)
    arrival_time_to_office = models.TimeField(null=True, blank=True)
    fuel_status = models.OneToOneField(
        FuelStatus, on_delete=models.SET_NULL, null=True, blank=True)
    speedometer = models.OneToOneField(
        Speedometer, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(
        TripTicket_Status, on_delete=models.SET_NULL, null=True, blank=True, default="Scheduled")
    qr_code_data = models.TextField(null=True, blank=True)
    vehicle_status = models.ForeignKey(
        Vehicle_Status, on_delete=models.SET_NULL, null=True, blank=True, default="Reserved")
    driver_status = models.ForeignKey(
        Driver_Status, on_delete=models.SET_NULL, null=True, blank=True, default="Assigned")

    def __str__(self):
        return self.authorized_passenger
