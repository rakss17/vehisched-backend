from rest_framework import serializers
from .models import TripTicket


class TripTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripTicket
        fields = '__all__'
