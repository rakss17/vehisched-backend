from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'created_cancel', consumers.NotificationCreatedCanceledConsumer.as_asgi()),
    re_path(r'approval_schedule-reminder', consumers.NotificationApprovalScheduleReminderConsumer.as_asgi()), 
]
