from rest_framework import generics, status, mixins
from rest_framework.response import Response
from .models import Request, Type, Vehicle_Driver_Status, Question, Answer
from trip.models import Trip
from accounts.models import Role, User
from .serializers import RequestSerializer, RequestOfficeStaffSerializer, Question2Serializer, AnswerSerializer
from vehicle.models import Vehicle
from notification.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.db.models import Q
from django.http import JsonResponse
import requests
import datetime as timedate
from datetime import datetime
from django.utils import timezone
from dateutil.parser import parse
import fitz
import qrcode
import ast
import re
from dotenv import load_dotenv
import os

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
        queryset = Request.objects.none()
        if Request.objects.filter(purpose=None, requester_name=user):
            queryset = Request.objects.filter(purpose=None, requester_name=user)
        if Request.objects.filter(requester_name=user):
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
                subject=f"A new request has been submitted by {self.request.user}",
            )
            notification.save()

        plate_number = request.data.get('vehicle')

        vehicle = Vehicle.objects.get(plate_number=plate_number)

        travel_date = request.data['travel_date']
        travel_time = request.data['travel_time']
        return_date = request.data['return_date']
        return_time = request.data['return_time']
        typee = request.data['type']
        role = request.data['role']
        merge_trip = request.data['merge_trip']

        if role == 'office staff' and not merge_trip:
            requester_name = User.objects.get(id=request.data['requester_name'])
            driver = User.objects.get(id=request.data['driver_name'])
            vehicle_capacity = request.data['vehicle_capacity']
            number_of_passenger = request.data['number_of_passenger']
            vacant = vehicle_capacity - number_of_passenger
            travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
            travel_time_obj = datetime.strptime(travel_time, '%H:%M').time()

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
        
            
            
            unavailable_driver = Request.objects.filter(
                (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(return_date__range=[travel_date, travel_date])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) |
                    Q(return_date__range=[travel_date, travel_date])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(travel_time__range=[travel_time, travel_time])
                ) | (
                    Q(return_date__range=[travel_date, travel_date]) &
                    Q(return_time__range=[travel_time, travel_time])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(return_date__range=[travel_date, travel_date])
                ),
                driver_name=driver,
                vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Driver Absence']
            ).exclude(
                (Q(travel_date=travel_date) & Q(travel_time__gte=travel_time)) |
                (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
            )
            if unavailable_driver.exists():
                new_request = Request.objects.create(
                    requester_name=requester_name,
                    travel_date=travel_date_obj,
                    travel_time=travel_time_obj,
                    return_date=return_date,
                    return_time=return_time,
                    destination=request.data['destination'],
                    office=request.data['office'],
                    number_of_passenger=request.data['number_of_passenger'],
                    passenger_name=passenger_name,
                    purpose=request.data['purpose'],
                    status= 'Approved',
                    vehicle= vehicle,
                    type = Type.objects.get(name=typee),
                    distance = request.data['distance'],
                    from_vip_alteration = False,
                    driver_name=None,
                     vehicle_capacity=vacant )
                vehicle_driver_status = Vehicle_Driver_Status.objects.create(
                    driver_id=None,
                    plate_number=vehicle,
                    status='Reserved - Assigned')
                new_request.vehicle_driver_status_id = vehicle_driver_status
                new_request.save()

                notification = Notification(
                    owner=self.request.user,
                    subject=f"A new request has been submitted by {self.request.user}" )
                notification.save()

                async_to_sync(channel_layer.group_send)(
                'notifications', 
                {
                    'type': 'notify.request_created',
                    'message': f"A new request has been submitted by {self.request.user}",
                })
                return Response(RequestSerializer(new_request).data, status=201)
            else: 
                new_request = Request.objects.create(
                    requester_name=requester_name,
                    travel_date=travel_date_obj,
                    travel_time=travel_time_obj,
                    return_date=return_date,
                    return_time=return_time,
                    destination=request.data['destination'],
                    office=request.data['office'],
                    number_of_passenger=request.data['number_of_passenger'],
                    passenger_name=passenger_name,
                    purpose=request.data['purpose'],
                    status= 'Approved',
                    vehicle= vehicle,
                    type = Type.objects.get(name=typee),
                    distance = request.data['distance'],
                    from_vip_alteration = False,
                    driver_name = driver,
                    vehicle_capacity=vacant )
                vehicle_driver_status = Vehicle_Driver_Status.objects.create(
                    driver_id=driver,
                    plate_number=vehicle,
                    status='Reserved - Assigned')

                new_request.vehicle_driver_status_id = vehicle_driver_status
                new_request.save()

                notification = Notification(
                    owner=self.request.user,
                    subject=f"A new request has been submitted by {self.request.user}")
                notification.save()

                async_to_sync(channel_layer.group_send)(
                'notifications', 
                {
                    'type': 'notify.request_created',
                    'message': f"A new request has been submitted by {self.request.user}",
                })

                from_vip_alteration = new_request.from_vip_alteration
                
                trip = Trip(
                    trip_id=new_request.request_id,
                    request_id=new_request,
                )
                trip.save()

                if from_vip_alteration:
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
                    ).exclude(request_id=new_request.request_id)

                    if filtered_requests.exists():
                        for requestt in filtered_requests:

                            travel_date_formatted = requestt.travel_date.strftime('%m/%d/%Y')
                            travel_time_formatted = requestt.travel_time.strftime('%I:%M %p')
                            return_date_formatted = requestt.return_date.strftime('%m/%d/%Y')
                            return_time_formatted = requestt.return_time.strftime('%I:%M %p')

                            notification = Notification(
                                owner=requestt.requester_name,
                                subject=f"We regret to inform you that the vehicle you reserved for the date {travel_date_formatted}, {travel_time_formatted} to {return_date_formatted}, {return_time_formatted} is used by the higher official. We apologize for any inconvenience this may cause."
                            )
                            notification.save()

                            async_to_sync(channel_layer.group_send)(
                                f"user_{requestt.requester_name}", 
                                {
                                    'type': 'recommend_notification',
                                    'message': f"We regret to inform you that the vehicle you reserved for the date {travel_date_formatted}, {travel_time_formatted} to {return_date_formatted}, {return_time_formatted} is used by the higher official. We apologize for any inconvenience this may cause."
                                }
                            )
                        filtered_requests.update(status='Awaiting Vehicle Alteration')
                travel_date_formatted = new_request.travel_date.strftime('%m/%d/%Y')
                travel_time_formatted = new_request.travel_time.strftime('%I:%M %p')
                destination = new_request.destination.split(',', 1)[0]

                async_to_sync(channel_layer.group_send)(
                    f"user_{new_request.requester_name}", 
                    {
                        'type': 'approve_notification',
                        'message': f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been approved.",
                    }
                )

                notification = Notification(
                    owner=new_request.requester_name,  
                    subject=f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been approved.",  
                )
                notification.save()

                
                driver_name = new_request.driver_name.get_full_name()
                vehicle_plate_number = new_request.vehicle.plate_number
                vehicle_model = new_request.vehicle.model
                requester_name = new_request.requester_name.get_full_name()
                
                destination = destination
                purpose = new_request.purpose
                if(new_request.date_reserved):
                    formatted_datereserved = timedate.datetime.strftime(new_request.date_reserved, "%m/%d/%Y, %I:%M %p")

                passenger_name_list = new_request.passenger_name

                passenger_names_string = ", ".join(passenger_name_list)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(new_request.request_id)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")

                img.save("temp.png")

                pixmap = fitz.Pixmap("temp.png")

                doc = fitz.open('media/documents/tripticket.pdf')
                page = doc[0] 

                text_annotations = {
                    driver_name: [220, 142],
                    vehicle_plate_number +" " + vehicle_model: [220, 152],
                    requester_name+", " + passenger_names_string: [220, 160],
                    destination: [220, 170],
                    purpose: [130, 180],
                    formatted_datereserved: [450, 80]
                }
                rect = fitz.Rect(520, 20, 570, 70)  
                page.insert_image(rect, pixmap=pixmap)

                for text, coordinates in text_annotations.items():
                    page.insert_text(coordinates, text, fontname="Helvetica-Bold", fontsize=5)

                doc.save(f"media/documents/tripticket{new_request.request_id}.pdf")
                doc.close()
                os.remove("temp.png")
                
                trip.qr_code_data = new_request.request_id
                trip.tripticket_pdf = f"documents/tripticket{new_request.request_id}.pdf"
                trip.save()

            
                return Response(RequestSerializer(new_request).data, status=201)
        
        if role == 'requester' and not merge_trip:
            driver = User.objects.get(username=request.data['driver_name'])
            vehicle_capacity = request.data['vehicle_capacity']
            number_of_passenger = request.data['number_of_passenger']
            vacant = vehicle_capacity - number_of_passenger

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
        
            
            
            unavailable_driver = Request.objects.filter(
                (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(return_date__range=[travel_date, travel_date])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) |
                    Q(return_date__range=[travel_date, travel_date])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(travel_time__range=[travel_time, travel_time])
                ) | (
                    Q(return_date__range=[travel_date, travel_date]) &
                    Q(return_time__range=[travel_time, travel_time])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(return_date__range=[travel_date, travel_date])
                ),
                driver_name=driver,
                vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Driver Absence']
            ).exclude(
                (Q(travel_date=travel_date) & Q(travel_time__gte=travel_time)) |
                (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
            )
            if unavailable_driver.exists():
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
                    type = Type.objects.get(name=typee),
                    distance = request.data['distance'],
                    from_vip_alteration = False,
                    driver_name=None,
                     vehicle_capacity=vacant )
                vehicle_driver_status = Vehicle_Driver_Status.objects.create(
                    driver_id=None,
                    plate_number=vehicle,
                    status='Reserved - Assigned')
                new_request.vehicle_driver_status_id = vehicle_driver_status
                new_request.save()

                notification = Notification(
                    owner=self.request.user,
                    subject=f"A new request has been submitted by {self.request.user}" )
                notification.save()

                async_to_sync(channel_layer.group_send)(
                'notifications', 
                {
                    'type': 'notify.request_created',
                    'message': f"A new request has been submitted by {self.request.user}",
                })
                return Response(RequestSerializer(new_request).data, status=201)
            else: 
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
                    type = Type.objects.get(name=typee),
                    distance = request.data['distance'],
                    from_vip_alteration = False,
                    driver_name = driver,
                    vehicle_capacity=vacant )
                vehicle_driver_status = Vehicle_Driver_Status.objects.create(
                    driver_id=driver,
                    plate_number=vehicle,
                    status='Reserved - Assigned')

                new_request.vehicle_driver_status_id = vehicle_driver_status
                new_request.save()

                notification = Notification(
                    owner=self.request.user,
                    subject=f"A new request has been submitted by {self.request.user}")
                notification.save()

                async_to_sync(channel_layer.group_send)(
                'notifications', 
                {
                    'type': 'notify.request_created',
                    'message': f"A new request has been submitted by {self.request.user}",
                })
            
                return Response(RequestSerializer(new_request).data, status=201)
                                
        if role == "vip" and not merge_trip:
            driver = User.objects.get(username=request.data['driver_name'])
            vehicle_capacity = request.data['vehicle_capacity']
            number_of_passenger = request.data['number_of_passenger']
            vacant = vehicle_capacity - number_of_passenger
            
            unavailable_driver = Request.objects.filter(
                (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(return_date__range=[travel_date, travel_date])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) |
                    Q(return_date__range=[travel_date, travel_date])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(travel_time__range=[travel_time, travel_time])
                ) | (
                    Q(return_date__range=[travel_date, travel_date]) &
                    Q(return_time__range=[travel_time, travel_time])
                ) | (
                    Q(travel_date__range=[travel_date, travel_date]) &
                    Q(return_date__range=[travel_date, travel_date])
                ),
                driver_name=driver,
                vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Driver Absence']
            ).exclude(
                (Q(travel_date=travel_date) & Q(travel_time__gte=travel_time)) |
                (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
            )
            if unavailable_driver.exists():
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
                    type = Type.objects.get(name=typee),
                    distance = request.data['distance'],
                    from_vip_alteration = True,
                    driver_name = None,
                    vehicle_capacity=vacant)
                
                vehicle_driver_status = Vehicle_Driver_Status.objects.create(
                    driver_id=None,
                    plate_number=vehicle,
                    status='Reserved - Assigned')
                
                new_request.vehicle_driver_status_id = vehicle_driver_status
                new_request.save()

                notification = Notification(
                    owner=self.request.user,
                    subject=f"A new request has been submitted by {self.request.user}",
                )
                notification.save()

                async_to_sync(channel_layer.group_send)(
                'notifications', 
                {
                    'type': 'notify.request_created',
                    'message': f"A new request has been submitted by {self.request.user}",
                }
                )
                return Response(RequestSerializer(new_request).data, status=201)
            else: 
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
                    type = Type.objects.get(name=typee),
                    distance = request.data['distance'],
                    from_vip_alteration = True,
                    driver_name = driver,
                    vehicle_capacity=vacant)
                
                vehicle_driver_status = Vehicle_Driver_Status.objects.create(
                    driver_id=driver,
                    plate_number=vehicle,
                    status='Reserved - Assigned')
                
                new_request.vehicle_driver_status_id = vehicle_driver_status
                new_request.save()

                notification = Notification(
                    owner=self.request.user,
                    subject=f"A new request has been submitted by {self.request.user}",
                )
                notification.save()

                async_to_sync(channel_layer.group_send)(
                'notifications', 
                {
                    'type': 'notify.request_created',
                    'message': f"A new request has been submitted by {self.request.user}",
                }
                )
                return Response(RequestSerializer(new_request).data, status=201)

        if merge_trip and not role == 'vip':
            driver = User.objects.get(id=request.data['driver_name'])
            requester = User.objects.get(id=request.data['requester_name'])
            vehicle_driver_status = Vehicle_Driver_Status.objects.create(
                driver_id=driver,
                plate_number=vehicle,
                status='Reserved - Assigned'
            )
            
            vehicle_capacity = request.data['vehicle_capacity']
            number_of_passenger = request.data['number_of_passenger']
            vacant = vehicle_capacity - number_of_passenger
            new_request = Request.objects.create(
                requester_name=requester,
                travel_date=travel_date,
                travel_time=travel_time,
                return_date=return_date,
                return_time=return_time,
                destination=request.data['destination'],
                office=None,
                number_of_passenger=request.data['number_of_passenger'],
                passenger_name=request.data['passenger_name'],
                purpose=request.data['purpose'],
                status= 'Pending',
                vehicle= vehicle,
                type = Type.objects.get(name=typee),
                distance = request.data['distance'],
                driver_name = driver,
                vehicle_capacity=vacant,
                merged_with=request.data['merged_with'],
                main_merge=merge_trip,
                
            )

            new_request.vehicle_driver_status_id = vehicle_driver_status
            new_request.save()

            new_request_merged_with = new_request.merged_with

            existing_requests = Request.objects.filter(request_id=new_request_merged_with)
            for existing_request in existing_requests:

                if existing_request.merged_with is not None:
                    vehicle_capacity = existing_request.vehicle_capacity
                    number_of_passenger = request.data['number_of_passenger']
                    vacant = vehicle_capacity - number_of_passenger
                    existing_request.vehicle_capacity = vacant
                    existing_request.merged_with += f", {new_request.request_id}"
                else:
                    vehicle_capacity = existing_request.vehicle_capacity
                    number_of_passenger = request.data['number_of_passenger']
                    vacant = vehicle_capacity - number_of_passenger
                    existing_request.vehicle_capacity = vacant
                    existing_request.merged_with = f"{new_request.request_id}"
                existing_request.save()
                #     vacant = capacity - number_passenger
                    
                
                # if existing_request.merged_with is not None:
                #     capacity = existing_request.vehicle_capacity
                #     number_passenger = existing_request.number_of_passenger
                #     vacant = capacity - number_passenger
                #     existing_request.vehicle_capacity = vacant
                #     existing_request.merged_with += f", {new_request.request_id}"
                # else:
                #     capacity = existing_request.vehicle_capacity
                #     number_passenger = request.data['number_of_passenger']
                #     vacant = capacity - number_passenger
                #     existing_request.vehicle_capacity = vacant
                #    

       
            return Response(RequestSerializer(new_request).data, status=201)

# class CSMListCreateView(generics.ListCreateAPIView):
#     serializer_class = CSMSerializer

#     def get_queryset(self):
#         request_id = self.kwargs['request_id']
#         return CSM.objects.filter(request__request_id=request_id)

#     def perform_create(self, serializer):
#         request_id = self.kwargs['request_id']
#         request = Request.objects.get(request_id=request_id)
#         csm = serializer.save(request=request)

#         for question_data in self.request.data['questions']:
#             question = Question.objects.get(question_number=question_data['question_number'])
#             Answer.objects.create(question=question, content=question_data['answers'])



class QuestionList(generics.ListAPIView):
   def get(self, request):
       questions = Question.objects.all()
       serializer = Question2Serializer(questions, many=True)
       return Response(serializer.data)
   
class AnswerListCreateView(generics.ListCreateAPIView):
    serializer_class = AnswerSerializer

    def get_queryset(self, request, *args, **kwargs):
        request_id = request.GET.get('request_id')
  
        queryset = Answer.objects.filter(request_id=request_id)

        return queryset

    def create(self, request, *args, **kwargs):
        answers_data = request.data['qaPairs']
        suggestions = request.data['suggestions'] 

        for answer_data in answers_data:
            question = answer_data['question']
            answer = answer_data['answer']
            request_id = answer_data['request']

            question_obj = Question.objects.get(question_number=question)
            request_obj = Request.objects.get(request_id=request_id)

            Answer.objects.create(
                request=request_obj,
                question=question_obj,
                answer=answer,
                suggestions=suggestions # Associate the suggestions with the Answer object
            )

        return Response(status=status.HTTP_201_CREATED)


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

        travel_date = instance.travel_date
        travel_time = instance.travel_time
        return_date = instance.return_date
        return_time = instance.return_time
        vehicle = instance.vehicle
        from_vip_alteration = instance.from_vip_alteration

        existing_vehicle_driver_status = instance.vehicle_driver_status_id
        existing_vehicle_driver_status.driver_id = driver
        existing_vehicle_driver_status.save()
        
        trip = Trip(
            trip_id=instance.request_id,
            request_id=instance,
        )
        trip.save()

        if from_vip_alteration:
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
            ).exclude(request_id=instance.request_id)

            if filtered_requests.exists():
                for requestt in filtered_requests:

                    travel_date_formatted = requestt.travel_date.strftime('%m/%d/%Y')
                    travel_time_formatted = requestt.travel_time.strftime('%I:%M %p')
                    return_date_formatted = requestt.return_date.strftime('%m/%d/%Y')
                    return_time_formatted = requestt.return_time.strftime('%I:%M %p')

                    notification = Notification(
                        owner=requestt.requester_name,
                        subject=f"We regret to inform you that the vehicle you reserved for the date {travel_date_formatted}, {travel_time_formatted} to {return_date_formatted}, {return_time_formatted} is used by the higher official. We apologize for any inconvenience this may cause."
                    )
                    notification.save()

                    async_to_sync(channel_layer.group_send)(
                        f"user_{requestt.requester_name}", 
                        {
                            'type': 'recommend_notification',
                            'message': f"We regret to inform you that the vehicle you reserved for the date {travel_date_formatted}, {travel_time_formatted} to {return_date_formatted}, {return_time_formatted} is used by the higher official. We apologize for any inconvenience this may cause."
                        }
                    )
                filtered_requests.update(status='Awaiting Vehicle Alteration')
        travel_date_formatted = instance.travel_date.strftime('%m/%d/%Y')
        travel_time_formatted = instance.travel_time.strftime('%I:%M %p')
        destination = instance.destination.split(',', 1)[0]

        async_to_sync(channel_layer.group_send)(
            f"user_{instance.requester_name}", 
            {
                'type': 'approve_notification',
                'message': f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been approved.",
            }
        )

        notification = Notification(
            owner=instance.requester_name,  
            subject=f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been approved.",  
        )
        notification.save()

        
        driver_name = instance.driver_name.get_full_name()
        vehicle_plate_number = instance.vehicle.plate_number
        vehicle_model = instance.vehicle.model
        requester_name = instance.requester_name.get_full_name()
        passenger_name = instance.passenger_name
        destination = instance.destination
        purpose = instance.purpose
        if(instance.date_reserved):
            formatted_datereserved = timedate.datetime.strftime(instance.date_reserved, "%m/%d/%Y, %I:%M %p")

            

        passenger_name_list = ast.literal_eval(passenger_name)  
        passenger_names_string = ", ".join(passenger_name_list)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(instance.request_id)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img.save("temp.png")

        pixmap = fitz.Pixmap("temp.png")

        doc = fitz.open('media/documents/tripticket.pdf')
        page = doc[0] 

        text_annotations = {
            driver_name: [220, 142],
            vehicle_plate_number +" " + vehicle_model: [220, 152],
            requester_name+", " + passenger_names_string: [220, 160],
            destination: [220, 170],
            purpose: [130, 180],
            formatted_datereserved: [450, 80]
        }
        rect = fitz.Rect(520, 20, 570, 70)  
        page.insert_image(rect, pixmap=pixmap)

        for text, coordinates in text_annotations.items():
            page.insert_text(coordinates, text, fontname="Helvetica-Bold", fontsize=5)

        doc.save(f"media/documents/tripticket{instance.request_id}.pdf")
        doc.close()
        os.remove("temp.png")
        
        trip.qr_code_data = instance.request_id
        trip.tripticket_pdf = f"documents/tripticket{instance.request_id}.pdf"
        trip.save()

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
        is_from_office_staff = request.data.get('isFromOfficeStaff')
        reason = request.data.get('reason')

        if instance.status == 'Canceled':
            return Response({'message': 'Request is already canceled.'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = 'Canceled'
        instance.save()

        existing_vehicle_driver_status = instance.vehicle_driver_status_id

        existing_vehicle_driver_status.status = 'Available'
        existing_vehicle_driver_status.save()

        existing_requests = Request.objects.filter(request_id=instance.merged_with)
        for existing_request in existing_requests:

            if existing_request.merged_with is not None:
                
                 # Create a regular expression pattern that matches the request_id along with its preceding comma
                pattern = r',\s*' + str(instance.request_id)
                
                # Use the re.sub() function to replace the matched pattern with an empty string
                existing_request.merged_with = re.sub(pattern, '', existing_request.merged_with)

                # If the string starts with a comma, remove it
                if existing_request.merged_with.startswith(','):
                    existing_request.merged_with = existing_request.merged_with[1:]

                if existing_request.merged_with == '':
                    # If the string is empty after the removal, set merged_with to None
                    existing_request.merged_with = None
                vehicle_capacity = existing_request.vehicle_capacity
                number_of_passenger = instance.number_of_passenger
                undo_vacant = vehicle_capacity + number_of_passenger
                existing_request.vehicle_capacity = undo_vacant
                instance.main_merge = False
                instance.merged_with = None
                instance.save()
                
            existing_request.save()

        if not is_from_office_staff:

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
        if is_from_office_staff:
            travel_date_formatted = instance.travel_date.strftime('%m/%d/%Y')
            travel_time_formatted = instance.travel_time.strftime('%I:%M %p')
            destination = instance.destination.split(',', 1)[0]
            async_to_sync(channel_layer.group_send)(
            f"user_{instance.requester_name}", 
            {
                'type': 'reject_notification',
                'message': f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been canceled. Reason: {reason}.",
            }
        )
            notification = Notification(
            owner=instance.requester_name,  
            subject=f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been canceled. Reason: {reason}.",  
        )
            notification.save()

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

        travel_date_converted = datetime.strptime(travel_date, '%Y-%m-%d').date()
        travel_time_converted = datetime.strptime(travel_time, '%H:%M').time()
        return_date_converted = datetime.strptime(return_date, '%Y-%m-%d').date()
        return_time_converted = datetime.strptime(return_time, '%H:%M').time()

        travel_datetime = datetime.combine(travel_date_converted, travel_time_converted)
        travel_datetime = timezone.make_aware(travel_datetime)
        return_datetime = datetime.combine(return_date_converted, return_time_converted)
        return_datetime = timezone.make_aware(return_datetime)

        if travel_datetime > return_datetime:
            error_message = "The starting date comes after the ending date!"
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
                Q(return_date__range=[travel_date, return_date]) &
                Q(travel_time__gte=travel_time) &
                Q(return_time__lte=return_time)
            ),
            vehicle=vehicle,
            vehicle_driver_status_id__status__in = ['Unavailable', 'On Trip'],
            status__in=['Ongoing Vehicle Maintenance'],
        ).exclude(
            (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
            (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        ).exists():
            error_message = "The selected vehicle is already scheduled for maintenance within the specified date and time range."
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
            for request in filtered_requests:

                travel_date_formatted = request.travel_date.strftime('%m/%d/%Y')
                travel_time_formatted = request.travel_time.strftime('%I:%M %p')
                return_date_formatted = request.return_date.strftime('%m/%d/%Y')
                return_time_formatted = request.return_time.strftime('%I:%M %p')

                notification = Notification(
                    owner=request.requester_name,
                    subject=f"We regret to inform you that the vehicle you reserved for the date {travel_date_formatted}, {travel_time_formatted} to {return_date_formatted}, {return_time_formatted} is currently undergoing unexpected maintenance. We apologize for any inconvenience this may cause."
                )
                notification.save()

                async_to_sync(channel_layer.group_send)(
                    f"user_{request.requester_name}", 
                    {
                        'type': 'recommend_notification',
                        'message': f"We regret to inform you that the vehicle you reserved for the date {travel_date_formatted}, {travel_time_formatted} to {return_date_formatted}, {return_time_formatted} is currently undergoing unexpected maintenance. We apologize for any inconvenience this may cause."
                    }
                )
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

        travel_date_converted = datetime.strptime(travel_date, '%Y-%m-%d').date()
        travel_time_converted = datetime.strptime(travel_time, '%H:%M').time()
        return_date_converted = datetime.strptime(return_date, '%Y-%m-%d').date()
        return_time_converted = datetime.strptime(return_time, '%H:%M').time()

        travel_datetime = datetime.combine(travel_date_converted, travel_time_converted)
        travel_datetime = timezone.make_aware(travel_datetime)
        return_datetime = datetime.combine(return_date_converted, return_time_converted)
        return_datetime = timezone.make_aware(return_datetime)

        if travel_datetime > return_datetime:
            error_message = "The starting date comes after the ending date!"
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
            driver_name=driver,
            vehicle_driver_status_id__status__in = ['Unavailable'],
            status__in=['Driver Absence'],
        ).exclude(
            (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
            (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        ).exists():
            error_message = "The selected driver has already scheduled for absence within the specified date and time range."
            return Response({'error': error_message}, status=400)

        
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
            status= 'Driver Absence',
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
            
    
            filtered_requests.update(driver_name=None)
        
        return Response(RequestSerializer(new_request).data, status=201)
    

class MaintenanceAbsenceCompletedView(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer


    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        instance.status = 'Completed'
        instance.save()

        existing_vehicle_driver_status = instance.vehicle_driver_status_id

        existing_vehicle_driver_status.status = 'Available'
        existing_vehicle_driver_status.save()

        return Response({'message': 'Success'})
    

class RejectRequestView(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        channel_layer = get_channel_layer()

        instance.status = 'Rejected'
        instance.save()

        existing_vehicle_driver_status = instance.vehicle_driver_status_id

        existing_vehicle_driver_status.status = 'Available'
        existing_vehicle_driver_status.save()

        existing_requests = Request.objects.filter(request_id=instance.merged_with)
        for existing_request in existing_requests:

            if existing_request.merged_with is not None:
                
                 # Create a regular expression pattern that matches the request_id along with its preceding comma
                pattern = r',\s*' + str(instance.request_id)
                
                # Use the re.sub() function to replace the matched pattern with an empty string
                existing_request.merged_with = re.sub(pattern, '', existing_request.merged_with)

                # If the string starts with a comma, remove it
                if existing_request.merged_with.startswith(','):
                    existing_request.merged_with = existing_request.merged_with[1:]

                if existing_request.merged_with == '':
                    # If the string is empty after the removal, set merged_with to None
                    existing_request.merged_with = None
                vehicle_capacity = existing_request.vehicle_capacity
                number_of_passenger = instance.number_of_passenger
                undo_vacant = vehicle_capacity + number_of_passenger
                existing_request.vehicle_capacity = undo_vacant
                instance.main_merge = False
                instance.merged_with = None
                instance.save()
                
            existing_request.save()

        reason = request.data.get('reason')

        travel_date_formatted = instance.travel_date.strftime('%m/%d/%Y')
        travel_time_formatted = instance.travel_time.strftime('%I:%M %p')
        destination = instance.destination.split(',', 1)[0]
        async_to_sync(channel_layer.group_send)(
        f"user_{instance.requester_name}", 
        {
            'type': 'reject_notification',
            'message': f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been rejected. Reason: {reason}.",
        }
    )
        notification = Notification(
        owner=instance.requester_name,  
        subject=f"Your request to {destination} on {travel_date_formatted} at {travel_time_formatted} has been rejected. Reason: {reason}.",  
    )
        notification.save()

        return Response({'message': 'Success'})


class MergeTripView(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        passenger_name = request.data.get('passenger_name', [])
        number_of_passenger = request.data.get('number_of_passenger')
        purpose = request.data.get('purpose')

        try:
            passenger_name = json.loads(passenger_name)
        except json.JSONDecodeError:
            return Response({'passenger_name': ['Invalid JSON data.']}, status=400)
        
        instance.passenger_name = passenger_name
        instance.number_of_passenger = number_of_passenger
        instance.purpose = purpose
        instance.save()
        
        return Response(status=200)
    
class ChangeRequestDriverView(generics.UpdateAPIView):
    queryset = Request.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_driver = request.data.get('new_driver')

        new_driver = User.objects.get(id=new_driver)
        instance.driver_name = new_driver
        instance.save()

        return Response(status=200)



    