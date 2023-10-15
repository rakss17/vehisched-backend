from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from notification.models import Notification
from .models import TripTicket
from request.models import Request


@shared_task()
def check_travel_dates():
    
    trip_tickets = TripTicket.objects.filter(status__description="Scheduled")
    for ticket in trip_tickets:
        request_data = Request.objects.get(request_id=ticket.request_number.request_id)
        travel_datetime = datetime.combine(request_data.travel_date, request_data.travel_time)
        travel_datetime = timezone.make_aware(travel_datetime)

        time_zone = timezone.localtime(timezone.now())

       
        if time_zone < travel_datetime - timedelta(days=1):
            
            pass
        elif time_zone < travel_datetime - timedelta(hours=12):
        
            pass
        elif time_zone < travel_datetime - timedelta(hours=1):
            print('1 hour left')
            
            notification = Notification(
            owner = request_data.requester_name,
            subject="1 hour left",
            )
            notification.save()

            pass
    

