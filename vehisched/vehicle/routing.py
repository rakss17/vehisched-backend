from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    re_path(r'available', consumers.VehicleStatusConsumer.as_asgi()),
]
