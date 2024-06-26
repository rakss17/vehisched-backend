from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from notification.models import Notification
from vehicle.models import OnProcess
from .models import Trip
from request.models import Request
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.mail import send_mail

@shared_task()
def check_travel_dates():
    channel_layer = get_channel_layer()
    
    trips = Trip.objects.filter(request_id__status__in=["Approved", "Approved - Alterate Vehicle"])
    
    for trip in trips:
        request_data = Request.objects.get(request_id=trip.request_id.request_id)
        travel_datetime = datetime.combine(request_data.travel_date, request_data.travel_time)
        travel_datetime = timezone.make_aware(travel_datetime)
        
        time_zone = timezone.localtime(timezone.now())

        # if travel_datetime < time_zone:
        #     continue

        if time_zone >= travel_datetime - timedelta(days=1):
            existing_notification = Notification.objects.filter(
                owner=request_data.requester_name, 
                subject=f"This is a reminder that your scheduled travel to {request_data.destination} is in 24 hours. Departure time: {request_data.travel_time}. Safe travels!", 
                purpose=trip.trip_id
            ).exists()
            
            if not existing_notification:
                async_to_sync(channel_layer.group_send)(
                    f"user_{request_data.requester_name}", 
                    {
                        'type': 'schedule.reminder',
                        'message': f"This is a reminder that your scheduled travel to {request_data.destination} is in 24 hours. Departure time: {request_data.travel_time}. Safe travels!",
                    }
                )
                
                notification = Notification(
                    owner=request_data.requester_name,
                    subject=f"This is a reminder that your scheduled travel to {request_data.destination} is in 24 hours. Departure time: {request_data.travel_time}. Safe travels!",
                    purpose=trip.trip_id
                )
                notification.save()
                subject='Schedule Reminder'
                from_email = settings.EMAIL_HOST_USER
                to_email = request_data.requester_name.email

                send_mail(subject, notification.subject, from_email, [to_email])
                            
        if time_zone >= travel_datetime - timedelta(hours=12):
            existing_notification = Notification.objects.filter(
                owner=request_data.requester_name, 
                subject="Only 12 hours left until your travel begins. Make sure you're all set!", 
                purpose=trip.trip_id).exists()
            
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
                    purpose=trip.trip_id
                )
                notification.save()
        
        if time_zone >= travel_datetime - timedelta(hours=1):
            existing_notification = Notification.objects.filter(
                owner=request_data.requester_name, 
                subject="Your schedule awaits! Just 1 hour until your travel begins. Be ready!", 
                purpose=trip.trip_id).exists()
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
                    purpose=trip.trip_id
                )
                notification.save()

        if time_zone >= travel_datetime:
            existing_notification = Notification.objects.filter(
                owner=request_data.requester_name, 
                subject="Your travel will commence now", 
                purpose=trip.trip_id).exists()
            if not existing_notification:
                async_to_sync(channel_layer.group_send)(
            f"user_{request_data.requester_name}", 
            {
                'type': 'schedule.reminder',
                'message': "Your travel will commence now",
            }
        )
                notification = Notification(
                    owner=request_data.requester_name,
                    subject="Your travel will commence now",
                    purpose=trip.trip_id
                )
                notification.save()

    requests = Request.objects.filter(status__in=["Ongoing Vehicle Maintenance", "Driver Absence"])

    for request in requests:
        travel_datetime = datetime.combine(request.return_date, request.return_time)
        travel_datetime = timezone.make_aware(travel_datetime)

        time_zone = timezone.localtime(timezone.now())


        if time_zone >= travel_datetime:
            request.status = 'Completed'
            request.save()
        #     existing_notification = Notification.objects.filter(
        #         owner=request_data.requester_name, 
        #         subject="Your schedule awaits! Just 1 hour until your travel begins. Be ready!", 
        #         purpose=trip.trip_id).exists()
        #     if not existing_notification:
        #         async_to_sync(channel_layer.group_send)(
        #     f"user_{request_data.requester_name}", 
        #     {
        #         'type': 'schedule.reminder',
        #         'message': "Your schedule awaits! Just 1 hour until your travel begins. Be ready!",
        #     }
        # )
        #         notification = Notification(
        #             owner=request_data.requester_name,
        #             subject="Your schedule awaits! Just 1 hour until your travel begins. Be ready!",
        #             purpose=trip.trip_id
        #         )
        #         notification.save()
            

@shared_task
def check_heartbeat():
    threshold = timezone.now() - timedelta(minutes=1)
    stale_processes = OnProcess.objects.filter(last_heartbeat__lt=threshold, on_process=True)
    
    for process in stale_processes:
        process.delete()