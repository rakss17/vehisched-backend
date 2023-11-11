from django.db import models
from request.models import Request


class Trip(models.Model):
    request_id = models.OneToOneField(
        Request, on_delete=models.CASCADE, null=True, blank=True)
    departure_time_from_office = models.TimeField(null=True, blank=True)
    arrival_time_to_destination = models.TimeField(null=True, blank=True)
    departure_time_from_destination = models.TimeField(null=True, blank=True)
    arrival_time_to_office = models.TimeField(null=True, blank=True)
    qr_code_data = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tripticket_pdf = models.FileField(upload_to='documents/', null=True, blank=True)

