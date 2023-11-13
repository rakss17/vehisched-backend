from rest_framework import serializers
from .models import Request


class RequestSerializer(serializers.ModelSerializer):
    driver_full_name = serializers.SerializerMethodField()
    driver_mobile_number = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    vehicle_driver_status = serializers.SerializerMethodField()

    def get_driver_full_name(self, obj):
        if obj.driver_name:
            driver = obj.driver_name
            driver_full_name = f"{driver.last_name}, {driver.first_name} {driver.middle_name}"
            return driver_full_name
        return None
    def get_driver_mobile_number(self, obj):
        if obj.driver_name:
            driver = obj.driver_name
            driver_mobile_number = driver.mobile_number
            return driver_mobile_number
        return None
    
    def get_type(self, obj):
        if obj.type:
            type = obj.type
            type = type.name
            return type
        return None
    def get_vehicle_driver_status(self, obj):
        if obj.vehicle_driver_status_id:
            vehicle_driver_status = obj.vehicle_driver_status_id
            vehicle_driver_status = vehicle_driver_status.status
            return vehicle_driver_status
        return None
    class Meta:
        model = Request
        fields = ['request_id', 'travel_date', 'travel_time', 'return_date', 'return_time','destination', 'office', 
                  'number_of_passenger', 'passenger_name', 'purpose', 'status', 'vehicle', 'date_reserved', 'driver_full_name', 'type', 
                  'driver_mobile_number','distance', 'vehicle_driver_status']

class RequestOfficeStaffSerializer(serializers.ModelSerializer):
    requester_full_name = serializers.SerializerMethodField()
    driver_full_name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    vehicle_driver_status = serializers.SerializerMethodField()

    def get_driver_full_name(self, obj):
        if obj.driver_name:
            driver = obj.driver_name
            driver_full_name = f"{driver.last_name}, {driver.first_name} {driver.middle_name}"
            return driver_full_name
        return None

    def get_requester_full_name(self, obj):
        if obj.requester_name:
            requester = obj.requester_name
            requester_full_name = f"{requester.last_name}, {requester.first_name} {requester.middle_name}"
            return requester_full_name
        return None
    
    def get_type(self, obj):
        if obj.type:
            type = obj.type
            type = type.name
            return type
        return None
    
    def get_vehicle_driver_status(self, obj):
        if obj.vehicle_driver_status_id:
            vehicle_driver_status = obj.vehicle_driver_status_id
            vehicle_driver_status = vehicle_driver_status.status
            return vehicle_driver_status
        return None

    class Meta:
        model = Request
        fields = ['request_id', 'requester_full_name', 'travel_date', 'travel_time', 'return_date', 'return_time','destination', 
                  'office', 'number_of_passenger', 'passenger_name', 'purpose', 'status', 'vehicle', 'date_reserved', 'driver_full_name', 
                  'type', 'distance', 'vehicle_driver_status']