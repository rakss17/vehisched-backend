from rest_framework import serializers
from .models import Request


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = '__all__'

class RequestOfficeStaffSerializer(serializers.ModelSerializer):
    requester_last_name = serializers.SerializerMethodField()
    requester_first_name = serializers.SerializerMethodField()
    requester_middle_name = serializers.SerializerMethodField()

    def get_requester_last_name(self, obj):
        if obj.requester_name:
            return obj.requester_name.last_name
        return None

    def get_requester_first_name(self, obj):
        if obj.requester_name:
            return obj.requester_name.first_name
        return None

    def get_requester_middle_name(self, obj):
        if obj.requester_name:
            return obj.requester_name.middle_name
        return None

    class Meta:
        model = Request
        fields = ['request_id', 'requester_last_name', 'requester_first_name', 'requester_middle_name', 
                  'travel_date', 'travel_time', 'destination', 'office_or_dept', 'number_of_passenger', 
                  'passenger_names', 'purpose', 'is_approved', 'status', 'vehicle', 'created_at', 'driver_name']