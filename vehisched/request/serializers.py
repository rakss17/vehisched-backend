from rest_framework import serializers
from .models import Request, Question, Answer
from vehicle.models import Vehicle
from django.utils.timezone import localtime
import pytz

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
                  'driver_mobile_number','distance', 'vehicle_driver_status', 'main_merge']
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.purpose is None and instance.vehicle is not None:
            vehicle = Vehicle.objects.get(plate_number=instance.vehicle.plate_number)
            representation['vehicle_details'] = {
                'plate_number': vehicle.plate_number,
                'model': vehicle.model,
                'type': vehicle.type,
                'capacity': vehicle.capacity,
                'is_vip': vehicle.is_vip,
                'image': vehicle.image.url if vehicle.image else None,
                'merge_trip': True

                # add other fields as needed
            }
        return representation

class RequestOfficeStaffSerializer(serializers.ModelSerializer):
    requester_full_name = serializers.SerializerMethodField()
    requester_id = serializers.SerializerMethodField()
    driver_full_name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    vehicle_driver_status = serializers.SerializerMethodField()
    departure_time_from_office = serializers.SerializerMethodField()
    arrival_time_to_office = serializers.SerializerMethodField()
    driver_id = serializers.SerializerMethodField()
    vehicle_model = serializers.SerializerMethodField()

    def get_driver_full_name(self, obj):
        if obj.driver_name:
            driver = obj.driver_name
            driver_full_name = f"{driver.last_name}, {driver.first_name} {driver.middle_name}"
            return driver_full_name
        return None
    def get_driver_id(self, obj):
        if obj.driver_name:
            driver= obj.driver_name
            driver_id = driver.id
            return driver_id
        return None
    
    def get_requester_full_name(self, obj):
        if obj.requester_name:
            requester = obj.requester_name
            requester_full_name = f"{requester.last_name}, {requester.first_name} {requester.middle_name}"
            return requester_full_name
        return None
    
    def get_requester_id(self, obj):
        if obj.requester_name:
            requester = obj.requester_name
            requester_id = requester.id
            return requester_id
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
    
    def get_vehicle_model(self, obj):
        if obj.vehicle:
            vehicle = obj.vehicle
            vehicle_model = vehicle.model
            return vehicle_model
        return None
    
    def get_departure_time_from_office(self, obj):
        if hasattr(obj, 'trip') and obj.trip.departure_time_from_office is not None:
            departure_time = obj.trip.departure_time_from_office
            
            departure_time_from_office = departure_time.astimezone(pytz.timezone('Asia/Manila'))
            return departure_time_from_office
        return None

    def get_arrival_time_to_office(self, obj):
        if hasattr(obj, 'trip') and obj.trip.arrival_time_to_office is not None:
            arrival_time = obj.trip.arrival_time_to_office
            
            arrival_time_to_office = arrival_time.astimezone(pytz.timezone('Asia/Manila'))
            return arrival_time_to_office
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        date_reserved = localtime(instance.date_reserved, pytz.timezone('Asia/Manila'))
        representation['date_reserved'] = date_reserved.isoformat()

        return representation

    class Meta:
        model = Request
        fields = ['request_id', 'requester_full_name','requester_id', 'travel_date', 'travel_time', 'return_date', 'return_time','destination', 
                  'office', 'number_of_passenger', 'passenger_name', 'purpose', 'status', 'vehicle', 'vehicle_model', 'date_reserved', 'driver_full_name', 
                  'type', 'distance', 'vehicle_driver_status', 'departure_time_from_office', 'arrival_time_to_office', 'driver_id', 'vehicle_capacity', 'merged_with', 'main_merge']

# class AnswerSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Answer
#        fields = ['content']

class QuestionSerializer(serializers.ModelSerializer):
#    answers = AnswerSerializer(many=True)

   class Meta:
       model = Question
       fields = ['question_number', 'content']

#    def create(self, validated_data):
#        answers_data = validated_data.pop('answers')
#        question = Question.objects.create(**validated_data)
#        for answer_data in answers_data:
#            Answer.objects.create(question=question, **answer_data)
#        return question

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['content']



class Question2Serializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ['question_number', 'question', ]



    # def create(self, validated_data):
    #     questions_data = validated_data.pop('question')
    #     csm = CSM.objects.create(**validated_data)
    #     for question_data in questions_data:
    #         answers_data = question_data.pop('answers')
    #         question = Question.objects.get(question_number=question_data['question_number'])
    #         for answer_data in answers_data:
    #             Answer.objects.create(question=question, **answer_data)
    #     return csm
