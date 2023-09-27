from rest_framework import generics, status
from rest_framework.response import Response
from .models import Request
from .serializers import RequestSerializer, RequestOfficeStaffSerializer
from vehicle.models import Vehicle, Vehicle_Status
import json

class RequestListCreateView(generics.ListCreateAPIView):
    serializer_class = RequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Request.objects.filter(requester_name=user)
        return queryset


    def create(self, request, *args, **kwargs):
        passenger_names = request.data.get('passenger_names', [])

        try:
            passenger_names = json.loads(passenger_names)
        except json.JSONDecodeError:
            return Response({'passenger_names': ['Invalid JSON data.']}, status=400)

        plate_number = request.data.get('vehicle')
        print("plate", plate_number)
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

        return super().create(request, *args, **kwargs)


class RequestListOfficeStaffView(generics.ListAPIView):
    serializer_class = RequestOfficeStaffSerializer
    queryset = Request.objects.all()
    



class RequestRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
