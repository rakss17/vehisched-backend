from django.db import models
from accounts.models import User
from vehicle.models import Vehicle


class Type(models.Model):
    type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, choices=[
        ('Round Trip', 'Round Trip'),
        ('One-way - Drop', 'One-way - Drop'),
        ('One-way - Fetch', 'One-way - Fetch'),
    ])
    
    def __str__(self):
        return self.name

class Vehicle_Driver_Status(models.Model):
    vehicle_driver_status_id = models.AutoField(primary_key=True)
    driver_id = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    plate_number = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=255, choices=[
        ('Available', 'Available'),
        ('Reserved - Assigned', 'Reserved - Assigned'),
        ('On Trip', 'On Trip'),
        ('Unavailable', 'Unavailable'),
    ])

class Request(models.Model):
    request_id = models.AutoField(primary_key=True)
    requester_name = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='requester_requests')
    travel_date = models.DateField(null=True, blank=True)
    travel_time = models.TimeField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    distance = models.IntegerField(null=True, blank=True)
    office = models.CharField(max_length=255, null=True, blank=True)
    number_of_passenger = models.IntegerField(null=True, blank=True)
    passenger_name = models.TextField(null=True, blank=True, help_text="List of passenger names in JSON format")
    purpose = models.CharField(max_length=1000, null=True, blank=True)
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    date_reserved = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    driver_name = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_requests')
    type = models.ForeignKey(
        Type, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_driver_status_id = models.OneToOneField(
        Vehicle_Driver_Status, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=255, choices=[
        ('Approved', 'Approved'),
        ('Approved - Alterate Vehicle', 'Approved - Alterate Vehicle'),
        ('Pending', 'Pending'),
        ('Canceled', 'Canceled'),
        ('Rescheduled', 'Rescheduled'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
        ('Awaiting Vehicle Alteration', 'Awaiting Vehicle Alteration'),
        ('Awaiting Rescheduling', 'Awaiting Rescheduling'),
        ('Ongoing Vehicle Maintenance', 'Ongoing Vehicle Maintenance'),
    ], null=True, blank=True)

    def __str__(self):
        return self.purpose
