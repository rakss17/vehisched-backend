from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user  
        return Notification.objects.filter(owner=user)

