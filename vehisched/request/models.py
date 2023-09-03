from django.db import models
from accounts.models import Role
from vehicle.models import Vehicle


class Request (models.Model):
    request_id = models.AutoField(primary_key=True)
    requester_name = models.CharField(max_length=255, null=True, blank=True)
    travel_date = models.DateField()
    travel_time = models.TimeField()
    destination = models.CharField(max_length=255, null=True, blank=True)
    office_or_dept = models.CharField(max_length=255, null=True, blank=True)
    number_of_passenger = models.IntegerField(null=True, blank=True)
    purpose = models.CharField(max_length=1000, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=100, null=True, blank=True)
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, null=True, blank=True)

    requester = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'role_name': 'requester'}
    )

    def __str__(self):
        return self.requester_name
