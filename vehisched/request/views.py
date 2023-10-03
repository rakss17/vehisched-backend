from rest_framework import generics, status
from rest_framework.response import Response
from .models import Request, Request_Status
from .serializers import RequestSerializer, RequestOfficeStaffSerializer
from vehicle.models import Vehicle, Vehicle_Status
from notification.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

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

        try:
            passenger_names = json.loads(passenger_names)
        except json.JSONDecodeError:
            return Response({'passenger_names': ['Invalid JSON data.']}, status=400)

        plate_number = request.data.get('vehicle')
       
        if plate_number:
            try:
                vehicle = Vehicle.objects.get(plate_number=plate_number)
                print("vehicle", vehicle)
               
                if vehicle.status.description == 'Available':
                    reserved_status = Vehicle_Status.objects.get(description='Reserved')
                    vehicle.status = reserved_status
                    vehicle.save()
                else:
                    return Response({'message': 'Vehicle is not available for reservation.'}, status=400)
            except Vehicle.DoesNotExist:
                return Response({'message': 'Vehicle not found.'}, status=404)
        

        new_request = Request.objects.create(
        requester_name=self.request.user,
        travel_date=request.data['travel_date'],
        travel_time=request.data['travel_time'],
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
        message = "A new request has been created."
        self.send_websocket_notification(message)

        return Response(RequestSerializer(new_request).data, status=201)


class RequestListOfficeStaffView(generics.ListAPIView):
    serializer_class = RequestOfficeStaffSerializer
    queryset = Request.objects.all()
    



class RequestApprovedView(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        is_approving = request.data.get('is_approved', False)

        if is_approving:
            
            approved_status = Request_Status.objects.get(description='Approved')
            instance.status = approved_status
            instance.save()

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

        if instance.status.description == 'Canceled':
            return Response({'message': 'Request is already canceled.'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = Request_Status.objects.get(description='Canceled')
        instance.save()

        if instance.vehicle:
           
            try:
                vehicle = instance.vehicle
                available_status = Vehicle_Status.objects.get(description='Available')
                vehicle.status = available_status
                vehicle.save()
            except Vehicle.DoesNotExist:
                pass  

        return Response({'message': 'Request canceled successfully.'})
