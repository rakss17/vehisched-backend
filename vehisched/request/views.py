from rest_framework import generics, status
from rest_framework.response import Response
from .models import Request, Type, Vehicle_Driver_Status
from trip.models import Trip
from accounts.models import Role, User, Driver_Status
from .serializers import RequestSerializer, RequestOfficeStaffSerializer
from vehicle.models import Vehicle
from notification.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.db.models import Q
from channels.layers import get_channel_layer
from django.http import JsonResponse
import requests
import datetime as timedate
from datetime import datetime
from dateutil.parser import parse
from dotenv import load_dotenv
import os
from django.db import transaction

load_dotenv()

def estimate_arrival_time(origin, destination, departure_time):
    api_key = os.getenv('GOOGLE_MAP_API_KEY')
    distance_matrix_api_url = 'https://maps.googleapis.com/maps/api/distancematrix/json'

    datetime_str = departure_time.strftime("%Y-%m-%d %H:%M")
    
    departure_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    departure_timestamp = int(departure_datetime.timestamp())

    params = {
        'origins': origin,
        'destinations': destination,
        'departure_time': departure_timestamp,
        'key': api_key,
    }

    response = requests.get(distance_matrix_api_url, params=params)
    data = response.json()

    
    if 'rows' in data and data['rows'] and 'elements' in data['rows'][0] and data['rows'][0]['elements']:
        
        duration = data['rows'][0]['elements'][0]['duration_in_traffic']['value']
        distance = data['rows'][0]['elements'][0]['distance']['text']

        departure_datetime = datetime.fromtimestamp(departure_timestamp)

        arrival_time = departure_datetime + timedate.timedelta(seconds=duration)

        return arrival_time, distance

    return None, None


def get_place_details(request):
    api_key = os.getenv('GOOGLE_MAP_API_KEY')
    place_id = request.GET.get('place_id')
    travel_date = request.GET.get('travel_date')
    travel_time = request.GET.get('travel_time')

    if not place_id:
        return JsonResponse({'error': 'Missing place_id parameter'}, status=400)

    response = requests.get(
        'https://maps.googleapis.com/maps/api/place/details/json',
        params={
            'place_id': place_id,
            'key': api_key
        }
    )
    place_data = response.json()
    ustp_coordinates = '8.484769199999999,124.6567168'

    destination_coordinates = f"{place_data['result']['geometry']['location']['lat']},{place_data['result']['geometry']['location']['lng']}"


    departure_time = parse(f"{travel_date}T{travel_time}")

    
    arrival_time, distance = estimate_arrival_time(ustp_coordinates, destination_coordinates, departure_time)

    if arrival_time is not None:
        return_time, _ = estimate_arrival_time(destination_coordinates, ustp_coordinates, arrival_time)

      
        place_data['estimated_arrival_time'] = arrival_time.isoformat()
        place_data['estimated_return_time'] = return_time.isoformat() if return_time is not None else None
        place_data['distance'] = distance
    else:
        place_data['estimated_arrival_time'] = None
        place_data['estimated_return_time'] = None
        place_data['distance'] = None

    return JsonResponse(place_data)

class RequestListCreateView(generics.ListCreateAPIView):
    serializer_class = RequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Request.objects.filter(requester_name=user)

        Notification.objects.filter(owner=user).update(read_status=True)
        return queryset

    def create(self, request, *args, **kwargs):
        passenger_name = request.data.get('passenger_name', [])
        office_staff_role = Role.objects.get(role_name='office staff')
        channel_layer = get_channel_layer()

        office_staff_users = User.objects.filter(role=office_staff_role)

        try:
            passenger_name = json.loads(passenger_name)
        except json.JSONDecodeError:
            return Response({'passenger_name': ['Invalid JSON data.']}, status=400)

        for user in office_staff_users:
            notification = Notification(
                owner=user,
                subject=f"A new request has been created by {self.request.user}",
            )
            notification.save()

        plate_number = request.data.get('vehicle')

        vehicle = Vehicle.objects.get(plate_number=plate_number)

        travel_date = request.data['travel_date']
        travel_time = request.data['travel_time']
        return_date = request.data['return_date']
        return_time = request.data['return_time']
        type = request.data['type']
        

        matching_requests_approved_maintenance = Request.objects.filter(
            (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) 
            ) | (
                Q(travel_date__range=[travel_date, return_date]) |
                Q(return_date__range=[travel_date, return_date])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(travel_time__range=[travel_time, return_time])
            ) | (
                Q(return_date__range=[travel_date, return_date]) &
                Q(return_time__range=[travel_time, return_time])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) 
            ),
            vehicle=vehicle,
            vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
            status__in=['Approved', 'Rescheduled', 'Approved - Alterate Vehicle', 'Ongoing Vehicle Maintenance'],
        ).exclude(
            (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
            (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        )

        if matching_requests_approved_maintenance.exists():
            
            status = matching_requests_approved_maintenance.first().status

            if status == 'Ongoing Vehicle Maintenance':
                error_message = "Sorry to inform you that there is sudden maintenance required for this vehicle. We apologize for any inconvenience it may cause."
            else: 
                error_message = "Someone has already selected and reserved this vehicle for the specified date and time range prior to your request"
            
            return Response({'error': error_message}, status=400)
        
        if Request.objects.filter(
            (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) 
            ) | (
                Q(travel_date__range=[travel_date, return_date]) |
                Q(return_date__range=[travel_date, return_date]) 
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(travel_time__range=[travel_time, return_time])
            ) | (
                Q(return_date__range=[travel_date, return_date]) &
                Q(return_time__range=[travel_time, return_time])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date])         
            ),
            vehicle=vehicle,
            status__in=['Pending', 'Awaiting Vehicle Alteration']
        ).exclude(
            (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
            (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        ).exists():
            error_message = "The selected vehicle is in queue. You cannot reserve this at the moment unless the requester cancel it."
            return Response({'error': error_message}, status=400)
        
        vehicle_driver_status = Vehicle_Driver_Status.objects.create(
            driver_id=None,
            plate_number=vehicle,
            status='Reserved - Assigned'
        )
        
        new_request = Request.objects.create(
            requester_name=self.request.user,
            travel_date=travel_date,
            travel_time=travel_time,
            return_date=return_date,
            return_time=return_time,
            destination=request.data['destination'],
            office=request.data['office'],
            number_of_passenger=request.data['number_of_passenger'],
            passenger_name=passenger_name,
            purpose=request.data['purpose'],
            status= 'Pending',
            vehicle= vehicle,
            type = Type.objects.get(name=type),
            distance = request.data['distance'],
        )

        new_request.vehicle_driver_status_id = vehicle_driver_status
        new_request.save()

        notification = Notification(
            owner=self.request.user,
            subject=f"Request {new_request.request_id} has been created",
        )
        notification.save()

        async_to_sync(channel_layer.group_send)(
        'notifications', 
        {
            'type': 'notify.request_canceled',
            'message': f"A new request has been created by {self.request.user}",
        }
    )
        
       
        return Response(RequestSerializer(new_request).data, status=201)


class RequestListOfficeStaffView(generics.ListAPIView):
    serializer_class = RequestOfficeStaffSerializer
    queryset = Request.objects.all()

    def list(self, request, *args, **kwargs):
        office_staff_role = Role.objects.get(role_name='office staff')
        office_staff_users = User.objects.filter(role=office_staff_role)

        for user in office_staff_users:
            Notification.objects.filter(owner=user).update(read_status=True)

        return super().list(request, *args, **kwargs)

 
class RequestApprovedView(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        channel_layer = get_channel_layer()

        driver_id = request.data.get('driver_id')  
        driver = User.objects.get(id=driver_id) 
        driver_name = f"{driver.last_name}, {driver.first_name} {driver.middle_name}"

        approved_status = 'Approved'
        instance.status = approved_status
        instance.driver_name = driver
        instance.save()

        # requester_name = instance.requester_name
        # requester_full_name = f"{requester_name.last_name}, {requester_name.first_name} {requester_name.middle_name}"

        # vehicle_driver_status = Vehicle_Driver_Status.objects.get(description='Assigned')

        existing_vehicle_driver_status = instance.vehicle_driver_status_id

        existing_vehicle_driver_status.driver_id = driver
        existing_vehicle_driver_status.save()
        # plate_number = instance.vehicle
        # authorized_passenger = f"{requester_full_name}, {instance.passenger_name}"
        trip = Trip(
            # driver_name=driver,
            # plate_number=plate_number,
            # authorized_passenger=authorized_passenger,
            request_id=instance,
        )
        trip.save()

        async_to_sync(channel_layer.group_send)(
        f"user_{instance.requester_name}", 
        {
            'type': 'approve_notification',
            'message': f"Request {instance.request_id} has been approved.",
        }
    )

        notification = Notification(
            owner=instance.requester_name,  
            subject=f"Request {instance.request_id} has been approved",  
        )
        notification.save()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
    
class RequestCancelView(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        channel_layer = get_channel_layer()
        office_staff_role = Role.objects.get(role_name='office staff')     
        office_staff_users = User.objects.filter(role=office_staff_role)

        if instance.status == 'Canceled':
            return Response({'message': 'Request is already canceled.'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = 'Canceled'
        instance.save()

        existing_vehicle_driver_status = instance.vehicle_driver_status_id

        existing_vehicle_driver_status.status = 'Available'
        existing_vehicle_driver_status.save()

        for user in office_staff_users:
        
            notification = Notification(
                owner=user,
                subject=f"A request has been canceled by {self.request.user}",
            )
            notification.save()

        async_to_sync(channel_layer.group_send)(
        'notifications', 
        {
            'type': 'notify.request_canceled',
            'message': f"A request has been canceled by {self.request.user}",
        }
    )

        return Response({'message': 'Request canceled successfully.'})


class VehicleMaintenance(generics.CreateAPIView):
    serializer_class = RequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Request.objects.filter(requester_name=user)

        Notification.objects.filter(owner=user).update(read_status=True)
        return queryset

    def create(self, request, *args, **kwargs):
        
        channel_layer = get_channel_layer()

        plate_number = request.data.get('plate_number')
        travel_date = request.data['travel_date']
        travel_time = request.data['travel_time']
        return_date = request.data['return_date']
        return_time = request.data['return_time']
        vehicle = Vehicle.objects.get(plate_number=plate_number)


        if Request.objects.filter(
            (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) 
            ) | (
                Q(travel_date__range=[travel_date, return_date]) |
                Q(return_date__range=[travel_date, return_date])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(travel_time__range=[travel_time, return_time])
            ) | (
                Q(return_date__range=[travel_date, return_date]) &
                Q(return_time__range=[travel_time, return_time])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) &
                Q(travel_time__gte=travel_time) &
                Q(return_time__lte=return_time)
            ),
            vehicle=vehicle,
            vehicle_driver_status_id__status__in = ['Unavailable'],
            status__in=['Ongoing Vehicle Maintenance'],
        ).exclude(
            (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
            (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        ).exists():
            error_message = "The selected vehicle is currently undergoing maintenance within the specified date and time range."
            return Response({'error': error_message}, status=400)

        
        vehicle_driver_status = Vehicle_Driver_Status.objects.create(
            driver_id=None,
            plate_number=vehicle,
            status='Unavailable'
        )

        new_request = Request.objects.create(
            requester_name=self.request.user,
            travel_date=travel_date,
            travel_time=travel_time,
            return_date=return_date,
            return_time=return_time,
            purpose='Vehicle Maintenance',
            status= 'Ongoing Vehicle Maintenance',
            vehicle= vehicle,
        )

        new_request.vehicle_driver_status_id = vehicle_driver_status
        new_request.save()


        filtered_requests = Request.objects.filter(
            (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) 
            ) | (
                Q(travel_date__range=[travel_date, return_date]) |
                Q(return_date__range=[travel_date, return_date])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(travel_time__range=[travel_time, return_time])
            ) | (
                Q(return_date__range=[travel_date, return_date]) &
                Q(return_time__range=[travel_time, return_time])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) &
                Q(travel_time__gte=travel_time) &
                Q(return_time__lte=return_time)
            ),
            vehicle=vehicle,
            vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip'],
            status__in=['Approved', 'Rescheduled', 'Approved - Alterate Vehicle'],
        )

        if filtered_requests.exists():
            filtered_requests.update(status='Awaiting Vehicle Alteration')

            



    #     notification = Notification(
    #         owner=self.request.user,
    #         subject=f"Request {new_request.request_id} has been created",
    #     )
    #     notification.save()

    #     async_to_sync(channel_layer.group_send)(
    #     'notifications', 
    #     {
    #         'type': 'notify.request_canceled',
    #         'message': f"A new request has been created by {self.request.user}",
    #     }
    # )
        
       
        return Response(RequestSerializer(new_request).data, status=201)
    

class DriverAbsence(generics.CreateAPIView):
    serializer_class = RequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Request.objects.filter(requester_name=user)

        Notification.objects.filter(owner=user).update(read_status=True)
        return queryset

    def create(self, request, *args, **kwargs):
        
        channel_layer = get_channel_layer()

        driver_id = request.data.get('driver')
        travel_date = request.data['travel_date']
        travel_time = request.data['travel_time']
        return_date = request.data['return_date']
        return_time = request.data['return_time']
        driver = User.objects.get(id=driver_id)


        # if Request.objects.filter(
        #     (
        #         Q(travel_date__range=[travel_date, return_date]) &
        #         Q(return_date__range=[travel_date, return_date]) 
        #     ) | (
        #         Q(travel_date__range=[travel_date, return_date]) |
        #         Q(return_date__range=[travel_date, return_date])
        #     ) | (
        #         Q(travel_date__range=[travel_date, return_date]) &
        #         Q(travel_time__range=[travel_time, return_time])
        #     ) | (
        #         Q(return_date__range=[travel_date, return_date]) &
        #         Q(return_time__range=[travel_time, return_time])
        #     ) | (
        #         Q(travel_date__range=[travel_date, return_date]) &
        #         Q(return_date__range=[travel_date, return_date]) &
        #         Q(travel_time__gte=travel_time) &
        #         Q(return_time__lte=return_time)
        #     ),
        #     vehicle=vehicle,
        #     vehicle_driver_status_id__status__in = ['Unavailable'],
        #     status__in=['Ongoing Vehicle Maintenance'],
        # ).exclude(
        #     (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
        #     (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        # ).exists():
        #     error_message = "The selected vehicle is currently undergoing maintenance within the specified date and time range."
        #     return Response({'error': error_message}, status=400)

        
        vehicle_driver_status = Vehicle_Driver_Status.objects.create(
            driver_id=driver,
            plate_number=None,
            status='Unavailable'
        )

        new_request = Request.objects.create(
            requester_name=self.request.user,
            travel_date=travel_date,
            travel_time=travel_time,
            return_date=return_date,
            return_time=return_time,
            purpose='Driver Absence',
            driver_name=driver,
        )

        new_request.vehicle_driver_status_id = vehicle_driver_status
        new_request.save()


        filtered_requests = Request.objects.filter(
            (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) 
            ) | (
                Q(travel_date__range=[travel_date, return_date]) |
                Q(return_date__range=[travel_date, return_date])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(travel_time__range=[travel_time, return_time])
            ) | (
                Q(return_date__range=[travel_date, return_date]) &
                Q(return_time__range=[travel_time, return_time])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) &
                Q(travel_time__gte=travel_time) &
                Q(return_time__lte=return_time)
            ),
            driver_name=driver,
            vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip'],
            status__in=['Approved', 'Rescheduled', 'Approved - Alterate Vehicle'],
        )

        if filtered_requests.exists():
            unavailable_drivers = Request.objects.filter(
                    (
                        Q(travel_date__range=[travel_date, return_date]) &
                        Q(return_date__range=[travel_date, return_date]) 
                    ) | (
                        Q(travel_date__range=[travel_date, return_date]) |
                        Q(return_date__range=[travel_date, return_date]) 
                    ) | (
                        Q(travel_date__range=[travel_date, return_date]) &
                        Q(travel_time__range=[travel_time, return_time])
                    ) | (
                        Q(return_date__range=[travel_date, return_date]) &
                        Q(return_time__range=[travel_time, return_time])
                    ) | (
                        Q(travel_date__range=[travel_date, return_date]) &
                        Q(return_date__range=[travel_date, return_date])         
                    ),
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],              
                ).exclude(
                    (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
                    (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
                ).values_list('user', flat=True)
            
            available_driver = User.objects.exclude(user__in=unavailable_drivers)
            driver_role = Role.objects.get(role_name='driver')   
            available_filtered_driver_role = available_driver.filter(role = driver_role)
            first_available_filtered_driver_role = available_filtered_driver_role.first()

            filtered_requests.update(driver_name = first_available_filtered_driver_role)




            
            


            



    #     notification = Notification(
    #         owner=self.request.user,
    #         subject=f"Request {new_request.request_id} has been created",
    #     )
    #     notification.save()

    #     async_to_sync(channel_layer.group_send)(
    #     'notifications', 
    #     {
    #         'type': 'notify.request_canceled',
    #         'message': f"A new request has been created by {self.request.user}",
    #     }
    # )
        
       
        return Response(RequestSerializer(new_request).data, status=201)