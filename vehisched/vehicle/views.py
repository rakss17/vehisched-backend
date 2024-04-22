from rest_framework import generics
from .models import Vehicle, OnProcess
from .serializers import VehicleSerializer
from request.views import RequestOfficeStaffSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from request.models import Request
from django.utils import timezone
from django.core.paginator import Paginator

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
    serializer_class = RequestOfficeStaffSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        role = self.request.GET.get('role')
        is_another_vehicle = self.request.GET.get('is_another_vehicle')
        existing_vehicle = self.request.GET.get('existing_vehicle')
        user_id = self.request.GET.get('user_id')
        print("is another", is_another_vehicle)
        if not role == 'vip':
            raise PermissionDenied("Only VIP users can access this view.")
        timezone.activate('Asia/Manila')
        
        if is_another_vehicle == 'true':
            
            all_vehicles = Vehicle.objects.exclude(plate_number=existing_vehicle)

            vehicles = {}

            for vehicle in all_vehicles:
                queryset = Request.objects.filter(
                    vehicle=vehicle, 
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
                    travel_date__gte=timezone.now().date()
                )
                
                serializer = self.serializer_class(queryset, many=True)
                vehicle_key = f"{vehicle.plate_number} {vehicle.model}"
                plate_number = vehicle.plate_number
                model = vehicle.model
                capacity = vehicle.capacity
                type = vehicle.type
                driver_assigned_to = vehicle.driver_assigned_to.username
                is_vip = vehicle.is_vip
                vip_assigned_to = vehicle.vip_assigned_to.username if vehicle.vip_assigned_to else None
                image_url = vehicle.image.url if vehicle.image else None

                vehicles[vehicle.plate_number] = {
                    'vehicle': vehicle_key,
                    'plate_number': plate_number,
                    'model': model,
                    'capacity': capacity,
                    'type': type,
                    'image': image_url,
                    'driver_assigned_to': driver_assigned_to,
                    'vip_assigned_to': vip_assigned_to, 
                    'is_vip': is_vip,
                    'schedules': serializer.data,
                }
            return Response({'data': vehicles, 'another_set_of_vehicles': 'true' }, status=status.HTTP_200_OK)
        else:
            print("trigger diri")
            owner = Request.objects.filter(requester_name=user_id)
            if owner == user_id:
                filtered_vehicles =  Vehicle.objects.filter(vip_assigned_to=user)

                vehicles = {}

                for vehicle in filtered_vehicles:
                    queryset = Request.objects.filter(
                        vehicle=vehicle, 
                        status__in=['Approved', 'Ongoing Vehicle Maintenance'],
                        vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                        travel_date__gte=timezone.now().date(),
                        requester_name=user_id,
                    )
                    
                    serializer = self.serializer_class(queryset, many=True)
                    vehicle_key = f"{vehicle.plate_number} {vehicle.model}"
                    plate_number = vehicle.plate_number
                    model = vehicle.model
                    capacity = vehicle.capacity
                    type = vehicle.type
                    driver_assigned_to = vehicle.driver_assigned_to.username
                    is_vip = vehicle.is_vip
                    vip_assigned_to = vehicle.vip_assigned_to.username if vehicle.vip_assigned_to else None
                    image_url = vehicle.image.url if vehicle.image else None

                    vehicles[vehicle.plate_number] = {
                        'vehicle': vehicle_key,
                        'plate_number': plate_number,
                        'model': model,
                        'capacity': capacity,
                        'type': type,
                        'image': image_url,
                        'driver_assigned_to': driver_assigned_to,
                        'vip_assigned_to': vip_assigned_to, 
                        'is_vip': is_vip,
                        'schedules': serializer.data,
                    }
                return Response({'data': vehicles }, status=status.HTTP_200_OK)
            elif owner != user_id:
                filtered_vehicles =  Vehicle.objects.filter(vip_assigned_to=user)

                vehicles = {}

                for vehicle in filtered_vehicles:
                    queryset = Request.objects.filter(
                        vehicle=vehicle, 
                        status__in=['Approved', 'Ongoing Vehicle Maintenance'],
                        vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                        travel_date__gte=timezone.now().date(),
                    )
                    
                    serializer = self.serializer_class(queryset, many=True)
                    vehicle_key = f"{vehicle.plate_number} {vehicle.model}"
                    plate_number = vehicle.plate_number
                    model = vehicle.model
                    capacity = vehicle.capacity
                    type = vehicle.type
                    driver_assigned_to = vehicle.driver_assigned_to.username
                    is_vip = vehicle.is_vip
                    vip_assigned_to = vehicle.vip_assigned_to.username if vehicle.vip_assigned_to else None
                    image_url = vehicle.image.url if vehicle.image else None

                    vehicles[vehicle.plate_number] = {
                        'vehicle': vehicle_key,
                        'plate_number': plate_number,
                        'model': model,
                        'capacity': capacity,
                        'type': type,
                        'image': image_url,
                        'driver_assigned_to': driver_assigned_to,
                        'vip_assigned_to': vip_assigned_to, 
                        'is_vip': is_vip,
                        'schedules': serializer.data,
                    }
                return Response({'data': vehicles }, status=status.HTTP_200_OK)

class AnotherVehicle(generics.ListAPIView):
    serializer_class=VehicleSerializer

    def get(self, request, *args, **kwargs):
        existing_vehicle = self.request.GET.get("existing_vehicle")

        vehicle = Vehicle.objects.exclude(plate_number=existing_vehicle)

        serializer = VehicleSerializer(vehicle, many=True)
        serialized_data = serializer.data

        return Response(serialized_data)

class CheckVehicleOnProcess(generics.ListAPIView):
        
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')
        preferred_vehicle = self.request.GET.get('preferred_vehicle')
        button_action = self.request.GET.get('button_action')
        requester = self.request.GET.get('requester')

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
                (Q(return_date=preferred_start_travel_date) & Q(return_time__lte=preferred_start_travel_time))).exclude(requester=requester).exists():
                message = "There is a requester on process. Sorry for inconvenience"
                return Response({'message': message}, status=400)
            else:
                on_process_obj = OnProcess.objects.create(travel_date=preferred_start_travel_date, travel_time=preferred_start_travel_time, 
                                         return_date=preferred_end_travel_date, return_time=preferred_end_travel_time, requester=requester, 
                                         vehicle=preferred_vehicle, on_process=True)
                message ='Vacant'
                return Response({'message': message, 'on_process_id': on_process_obj.id}, status=200)
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
        
class HeartbeatView(generics.UpdateAPIView):
    queryset = OnProcess.objects.all()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        instance.last_heartbeat = timezone.now()
        instance.save()
        return Response({'status': 'success'})         

class VehicleEachSchedule(generics.ListAPIView):
    serializer_class = RequestOfficeStaffSerializer

    def get(self, request, *args, **kwargs):
        
        page_size = 2 
        page_number = request.GET.get('page', 1) 

        vehicles = Vehicle.objects.all()
        paginator = Paginator(vehicles, page_size)
        page_obj = paginator.get_page(page_number)
        timezone.activate('Asia/Manila')
        requests_by_vehicle = {}

        for vehicle in page_obj:
            queryset = Request.objects.filter(
                vehicle=vehicle, 
                status__in=[
                    'Approved', 
                    'Approved - Alterate Vehicle', 
                    'Awaiting Vehicle Alteration', 
                    'Ongoing Vehicle Maintenance'
                ],
                travel_date__gte=timezone.now().date()
            )
            
            serializer = self.serializer_class(queryset, many=True)
            
            vehicle_key = f"{vehicle.plate_number} {vehicle.model}"
            plate_number = vehicle.plate_number
            model = vehicle.model
            capacity = vehicle.capacity
            type = vehicle.type
            driver_assigned_to = vehicle.driver_assigned_to.username
            is_vip = vehicle.is_vip
            vip_assigned_to = vehicle.vip_assigned_to.username if vehicle.vip_assigned_to else None
            image_url = vehicle.image.url if vehicle.image else None

            requests_by_vehicle[vehicle.plate_number] = {
                'vehicle': vehicle_key,
                'plate_number': plate_number,
                'model': model,
                'capacity': capacity,
                'type': type,
                'image': image_url,
                'driver_assigned_to': driver_assigned_to,
                'vip_assigned_to': vip_assigned_to, 
                'is_vip': is_vip,
                'schedules': serializer.data,
            }

        return Response({
            'data': requests_by_vehicle,
            'next_page': page_obj.has_next() and page_obj.next_page_number() or None,
        }, status=status.HTTP_200_OK)
    