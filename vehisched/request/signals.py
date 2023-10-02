from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Request
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Request)
def request_approval(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    if instance.status.description == 'Approved':
        
        async_to_sync(channel_layer.group_send)(
            "request_status_approved",
              {
            'type': 'approve_notification',
             "message": f" {instance.request_id} has been approved.",
            # 'request_id': instance.request_id,
            # 'travel_date': instance.travel_date,
            # 'travel_time': instance.travel_time,
            'status': instance.status.description,
        })



        