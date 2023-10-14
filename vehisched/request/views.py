from rest_framework import generics, status
from rest_framework.response import Response
from .models import Request, Request_Status
from tripticket.models import TripTicket, TripTicket_Status
from accounts.models import Role, User, Driver_Status
from .serializers import RequestSerializer, RequestOfficeStaffSerializer
from vehicle.models import Vehicle, Vehicle_Status
from notification.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.db.models import Q


class RequestListCreateView(generics.ListCreateAPIView):
    serializer_class = RequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Request.objects.filter(requester_name=user)

        Notification.objects.filter(owner=user).update(read_status=True)
        return queryset

    def send_websocket_notification(self, message):
        channel_layer = get_channel_layer()
        event = {
            'type': 'notify.request_created',
            'message': message,
        }
        async_to_sync(channel_layer.group_send)('notifications', event)

    def create(self, request, *args, **kwargs):
        passenger_names = request.data.get('passenger_names', [])
        office_staff_role = Role.objects.get(role_name='office staff')

        office_staff_users = User.objects.filter(role=office_staff_role)

        try:
            passenger_names = json.loads(passenger_names)
        except json.JSONDecodeError:
            return Response({'passenger_names': ['Invalid JSON data.']}, status=400)

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

        if Request.objects.filter(
            (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) &
                ~Q(travel_time__range=[travel_time, return_time]) &
                ~Q(return_time__range=[travel_time, return_time])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) |
                Q(return_date__range=[travel_date, return_date]) |
                ~Q(travel_time__range=[travel_time, return_time]) |
                ~Q(return_time__range=[travel_time, return_time])
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
            vehicle__tripticket__vehicle_status__in=['Reserved', 'On trip', 'Unavailable'],
            status__in=['Approved', 'Reschedule']
        ).exclude(
            (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
            (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        ).exists():
            error_message = "The selected vehicle is already reserved within the specified date and time range."
            return Response({'error': error_message, "type": "Approved"}, status=400)
        
        if Request.objects.filter(
            (
                Q(travel_date__range=[travel_date, return_date]) &
                Q(return_date__range=[travel_date, return_date]) &
                ~Q(travel_time__range=[travel_time, return_time]) &
                ~Q(return_time__range=[travel_time, return_time])
            ) | (
                Q(travel_date__range=[travel_date, return_date]) |
                Q(return_date__range=[travel_date, return_date]) |
                ~Q(travel_time__range=[travel_time, return_time]) |
                ~Q(return_time__range=[travel_time, return_time])
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
            status__in=['Pending']
        ).exclude(
            (Q(travel_date=return_date) & Q(travel_time__gte=return_time)) |
            (Q(return_date=travel_date) & Q(return_time__lte=travel_time))
        ).exists():
            error_message = "The selected vehicle is in queue. You cannot reserve this at the moment unless the requester cancel it."
            return Response({'error': error_message, "type": "Pending"}, status=400)

        new_request = Request.objects.create(
            requester_name=self.request.user,
            travel_date=travel_date,
            travel_time=travel_time,
            return_date=return_date,
            return_time=return_time,
            destination=request.data['destination'],
            office_or_dept=request.data['office_or_dept'],
            number_of_passenger=request.data['number_of_passenger'],
            passenger_names=passenger_names,
            purpose=request.data['purpose'],
            is_approved=False,
            status=Request_Status.objects.get(description='Pending'),
            vehicle=vehicle
        )

        notification = Notification(
            owner=self.request.user,
            subject=f"Request {new_request.request_id} has been created",
        )
        notification.save()
        message = f"A new request has been created by {self.request.user}"
        self.send_websocket_notification(message)

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

        is_approving = request.data.get('is_approved', False)

        if is_approving:

            driver_id = request.data.get('driver_id')  
            driver = User.objects.get(id=driver_id) 
            driver_name = f"{driver.last_name}, {driver.first_name} {driver.middle_name}"

            approved_status = Request_Status.objects.get(description='Approved')
            instance.status = approved_status
            instance.driver_name = driver_name 
            instance.save()

            requester_name = instance.requester_name
            requester_full_name = f"{requester_name.last_name}, {requester_name.first_name} {requester_name.middle_name}"

            driver_status = Driver_Status.objects.get(description='Assigned')

            plate_number = instance.vehicle
            authorized_passenger = f"{requester_full_name}, {instance.passenger_names}"
            trip_ticket = TripTicket(
                driver_name=driver,
                plate_number=plate_number,
                authorized_passenger=authorized_passenger,
                request_number=instance,
                driver_status = driver_status
            )
            trip_ticket.save()

            

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

    def send_websocket_notification(self, message):
        channel_layer = get_channel_layer()
        event = {
            'type': 'notify.request_canceled',
            'message': message,
        }
        async_to_sync(channel_layer.group_send)('notifications', event)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        office_staff_role = Role.objects.get(role_name='office staff')     
        office_staff_users = User.objects.filter(role=office_staff_role)

        if instance.status.description == 'Canceled':
            return Response({'message': 'Request is already canceled.'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = Request_Status.objects.get(description='Canceled')
        instance.save()

        request_status = request.data.get('selected_status')
        
        if request_status == 'Approved':
            trip_ticket = TripTicket.objects.get(request_number=instance)

            trip_ticket_status_canceled = TripTicket_Status.objects.get(description='Canceled')
            trip_ticket.status = trip_ticket_status_canceled
            trip_ticket.save()


            driver_status = Driver_Status.objects.get(description='Available')
            trip_ticket.driver_status = driver_status

            vehicle_status_available = Vehicle_Status.objects.get(description='Available')
            trip_ticket.vehicle_status = vehicle_status_available
            trip_ticket.save()

        

        for user in office_staff_users:
        
            notification = Notification(
                owner=user,
                subject=f"A request has been canceled by {self.request.user}",
            )
            notification.save()
        message = f"A request has been canceled by {self.request.user}"
        self.send_websocket_notification(message)  

        return Response({'message': 'Request canceled successfully.'})
