from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from notification.models import Notification
from .models import TripTicket
from request.models import Request
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task()
def check_travel_dates():
    channel_layer = get_channel_layer()
    
    trip_tickets = TripTicket.objects.filter(status__description="Scheduled")
    
    for ticket in trip_tickets:
        request_data = Request.objects.get(request_id=ticket.request_number.request_id)
        travel_datetime = datetime.combine(request_data.travel_date, request_data.travel_time)
        travel_datetime = timezone.make_aware(travel_datetime)
        
        time_zone = timezone.localtime(timezone.now())

        if time_zone >= travel_datetime - timedelta(days=1):
            existing_notification = Notification.objects.filter(
                owner=request_data.requester_name, 
                subject="This is to remind you that you have a scheduled travel in 24 hours", 
                purpose=ticket.id
            ).exists()
            
            if not existing_notification:
                async_to_sync(channel_layer.group_send)(
                    f"user_{request_data.requester_name}", 
                    {
                        'type': 'schedule.reminder',
                        'message': "This is to remind you that you have a scheduled travel in 24 hours",
                    }
                )
                
                notification = Notification(
                    owner=request_data.requester_name,
                    subject="This is to remind you that you have a scheduled travel in 24 hours",
                    purpose=ticket.id
                )
                notification.save()
                            
        if time_zone >= travel_datetime - timedelta(hours=12):
            existing_notification = Notification.objects.filter(
                owner=request_data.requester_name, 
                subject="Only 12 hours left until your travel begins. Make sure you're all set!", 
                purpose=ticket.id).exists()
            
            if not existing_notification:
                async_to_sync(channel_layer.group_send)(
            f"user_{request_data.requester_name}", 
            {
                'type': 'schedule.reminder',
                'message': "Only 12 hours left until your travel begins. Make sure you're all set!",
            }
        )
                notification = Notification(
                    owner=request_data.requester_name,
                    subject="Only 12 hours left until your travel begins. Make sure you're all set!",
                    purpose=ticket.id
                )
                notification.save()
        
        if time_zone >= travel_datetime - timedelta(hours=1):
            existing_notification = Notification.objects.filter(
                owner=request_data.requester_name, 
                subject="Your schedule awaits! Just 1 hour until your travel begins. Be ready!", 
                purpose=ticket.id).exists()
            if not existing_notification:
                async_to_sync(channel_layer.group_send)(
            f"user_{request_data.requester_name}", 
            {
                'type': 'schedule.reminder',
                'message': "Your schedule awaits! Just 1 hour until your travel begins. Be ready!",
            }
        )
                notification = Notification(
                    owner=request_data.requester_name,
                    subject="Your schedule awaits! Just 1 hour until your travel begins. Be ready!",
                    purpose=ticket.id
                )
                notification.save()