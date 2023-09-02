from rest_framework import serializers
from .models import Request


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['requester_name', 'travel_date', 'travel_time', 'destination',
                  'office_or_dept', 'number_of_passenger', 'purpose', 'is_approved', 'vehicle']
