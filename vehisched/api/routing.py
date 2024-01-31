
from django.urls import re_path
from channels.routing import URLRouter
import notification.routing


websocket_urlpatterns = [
    re_path(r'notification/', URLRouter(notification.routing.websocket_urlpatterns)),
]
