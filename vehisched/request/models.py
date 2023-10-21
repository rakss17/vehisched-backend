from django.db import models
from accounts.models import User
from vehicle.models import Vehicle


class Request_Status(models.Model):
    description = models.CharField(primary_key=True, max_length=255, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Canceled', 'Canceled'),
        ('Reschedule', 'Reschedule'),
        ('Completed', 'Completed'),
    ])

    def __str__(self):
        return self.description

class Category(models.Model):
    description = models.CharField(primary_key=True, max_length=255, choices=[
        ('Round Trip', 'Round Trip'),
        ('One-way', 'One-way'),
    ])
    
    def __str__(self):
        return self.description

class Sub_Category(models.Model):
    description = models.CharField(primary_key=True, max_length=255, choices=[
        ('Drop', 'Drop'),
        ('Fetch', 'Fetch'),
        ('N/A', 'N/A')
    ])

    def __str__(self):
        return self.description

class Request (models.Model):
    request_id = models.AutoField(primary_key=True)
    requester_name = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    travel_date = models.DateField(null=True, blank=True)
    travel_time = models.TimeField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    distance = models.IntegerField(null=True, blank=True)
    office_or_dept = models.CharField(max_length=255, null=True, blank=True)
    number_of_passenger = models.IntegerField(null=True, blank=True)
    passenger_names = models.TextField(null=True, blank=True, help_text="List of passenger names in JSON format")
    purpose = models.CharField(max_length=1000, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    status = models.ForeignKey(
        Request_Status, on_delete=models.SET_NULL, null=True, blank=True, default="Pending")
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    driver_name = models.CharField(max_length=100, null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True)
    sub_category = models.ForeignKey(
        Sub_Category, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.office_or_dept
