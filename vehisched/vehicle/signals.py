from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Vehicle

@receiver(post_save, sender=Vehicle)
@receiver(post_delete, sender=Vehicle)
def vehicle_status_changed(sender, instance, **kwargs):
    if instance.status.description == 'Available':
        action = 'added'
    else:
        action = 'removed'

    print(f"Signal received: Vehicle {instance.plate_number} status changed to {instance.status.description} ({action}).")

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "vehicle_status_updates",
        {
            "type": "status_update",
            "message": f"Vehicle {instance.plate_number} has been {action}.",
            "plate_number": instance.plate_number
        },
    )
