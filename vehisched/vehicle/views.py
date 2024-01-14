from rest_framework import generics
from .models import Vehicle, OnProcess
from .serializers import VehicleSerializer
from django.utils import timezone
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q




class VehicleListCreateView(generics.ListCreateAPIView):

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():

            self.perform_create(serializer)

            image_file = request.FILES.get('vehicle_image')
            if image_file:

                serializer.instance.vehicle_image = image_file
                serializer.instance.save()

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)

        if serializer.is_valid():

            new_image = request.FILES.get('image', None)
        
            if new_image:

                if instance.image:
                    instance.image.delete()

                instance.image = new_image

            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VehicleForVIPListView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        print(user)
        role = self.request.GET.get('role')
        if not role == 'vip':
            raise PermissionDenied("Only VIP users can access this view.")
        return Vehicle.objects.filter(vip_assigned_to=user)
    

class CheckVehicleOnProcess(generics.ListAPIView):
        
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')
        preferred_vehicle = self.request.GET.get('preferred_vehicle')
        button_action = self.request.GET.get('button_action')
        requester = self.request.GET.get('requester')

        print(button_action)

        if button_action == 'select_vehicle':
            if OnProcess.objects.filter(
                (
                    Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                    Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
                ) | (
                    Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) |
                    Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
                ) | (
                    Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                    Q(travel_time__range=[preferred_start_travel_time, preferred_end_travel_time])
                ) | (
                    Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                    Q(return_time__range=[preferred_start_travel_time, preferred_end_travel_time])
                ) | (
                    Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                    Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                    Q(travel_time__gte=preferred_start_travel_time) &
                    Q(return_time__lte=preferred_end_travel_time)
                ),
                vehicle=preferred_vehicle,
                on_process=True).exclude(
                (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gte=preferred_end_travel_time)) |
                (Q(return_date=preferred_start_travel_date) & Q(return_time__lte=preferred_start_travel_time))).exists():
                message = "There is a requester on process. Sorry for inconvenience"
                return Response({'message': message}, status=400)
            else:
                OnProcess.objects.create(travel_date=preferred_start_travel_date, travel_time=preferred_start_travel_time, 
                                         return_date=preferred_end_travel_date, return_time=preferred_end_travel_time, requester=requester, 
                                         vehicle=preferred_vehicle, on_process=True)
                message ='Vacant'
                return Response({'message': message}, status=200)
        elif button_action == 'deselect_vehicle':
            on_process_obj = OnProcess.objects.filter(
            (
                Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
            ) | (
                Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) |
                Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
            ) | (
                Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(travel_time__range=[preferred_start_travel_time, preferred_end_travel_time])
            ) | (
                Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(return_time__range=[preferred_start_travel_time, preferred_end_travel_time])
            ) | (
                Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(travel_time__gte=preferred_start_travel_time) &
                Q(return_time__lte=preferred_end_travel_time)
            ),
            vehicle=preferred_vehicle,
            requester=requester,
            on_process=True).exclude(
            (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gte=preferred_end_travel_time)) |
            (Q(return_date=preferred_start_travel_date) & Q(return_time__lte=preferred_start_travel_time)))
            if on_process_obj.exists():
                on_process_obj.delete()
                message ='Deselect vehicle'
                return Response({'message': message}, status=200)
            return Response({'message': 'Success'}, status=200)
                

        