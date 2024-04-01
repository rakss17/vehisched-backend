from django.db import models
from request.models import Request
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone


class Trip(models.Model):
    trip_id = models.IntegerField(primary_key=True, default=0)
    request_id = models.OneToOneField(
        Request, on_delete=models.CASCADE, null=True, blank=True)
    departure_time_from_office = models.DateTimeField(null=True, blank=True)
    arrival_time_to_destination = models.DateTimeField(null=True, blank=True)
    departure_time_from_destination = models.DateTimeField(null=True, blank=True)
    arrival_time_to_office = models.DateTimeField(null=True, blank=True)
    qr_code_data = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tripticket_pdf = models.FileField(upload_to='documents/', null=True, blank=True)
    requestform_pdf = models.FileField(upload_to='documents/', null=True, blank=True)

@receiver(post_migrate)
def create_periodic_tasks(sender, **kwargs):

    schedule, created = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.MINUTES,
        
    )

    if not PeriodicTask.objects.filter(name='Check travel dates every minute').exists():
        PeriodicTask.objects.create(
            interval=schedule,
            name='Check travel dates every minute',
            task='trip.tasks.check_travel_dates',
            start_time=timezone.now()
        )
        print('Created check travel dates every minute periodic task')

    if not PeriodicTask.objects.filter(name='Check heart beat every minute').exists():
        PeriodicTask.objects.create(
            interval=schedule,
            name='Check heart beat every minute',
            task='trip.tasks.check_heartbeat',
            start_time=timezone.now()
        )
        print('Created check heart beat every minute periodic task')