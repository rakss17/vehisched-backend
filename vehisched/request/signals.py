from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Request
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Request)
def request_approval(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    print("triggred!")
    user = f"user_{instance.requester_name}"
    print(user)
    if instance.status.description == 'Approved':
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.requester_name}", 
            {
                'type': 'approve_notification',
                'message': f"Request {instance.request_id} has been approved.",
                'status': instance.status.description,
            }
        )



        