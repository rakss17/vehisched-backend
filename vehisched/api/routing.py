
from django.urls import re_path
from channels.routing import URLRouter
import vehicle.routing
import request.routing


websocket_urlpatterns = [
    re_path(r'vehicle/', URLRouter(vehicle.routing.websocket_urlpatterns)),
    re_path(r'request/', URLRouter(request.routing.websocket_urlpatterns)),
]
