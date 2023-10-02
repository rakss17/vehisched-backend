from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'approve', consumers.RequestConsumer.as_asgi()),
]





