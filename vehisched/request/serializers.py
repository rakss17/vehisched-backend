from rest_framework import serializers
from .models import Request


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = '__all__'

class RequestOfficeStaffSerializer(serializers.ModelSerializer):
    requester_last_name = serializers.CharField(source='requester_name.last_name')
    requester_first_name = serializers.CharField(source='requester_name.first_name')
    requester_middle_name = serializers.CharField(source='requester_name.middle_name')

    class Meta:
        model = Request
        fields = ['request_id', 'requester_last_name', 'requester_first_name', 'requester_middle_name', 'travel_date', 'travel_time', 'destination', 'office_or_dept', 'number_of_passenger', 'passenger_names', 'purpose', 'is_approved', 'status', 'vehicle', 'created_at']