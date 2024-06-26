from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule

class Command(BaseCommand):
    help = 'Creates the check_travel_dates periodic task'

    def handle(self, *args, **options):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        PeriodicTask.objects.create(
            interval=schedule,
            name='Check travel dates every minute',
            task='trip.tasks.check_travel_dates',
        )

        PeriodicTask.objects.create(
            interval=schedule,
            name='Check heart beat every minute',
            task='trip.tasks.check_heartbeat',
        )

        self.stdout.write(self.style.SUCCESS('Successfully created periodic task'))
