from rest_framework import generics, status
from django.http import JsonResponse
from .models import Trip
from notification.models import Notification
from accounts.models import Role
from accounts.models import User
from request.models import Request, Vehicle_Driver_Status
from vehicle.models import Vehicle
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from request.serializers import RequestSerializer
from datetime import datetime
from django.utils import timezone
from django.http import FileResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class ScheduleRequesterView(generics.ListAPIView):
    
    def get(self, request, *args, **kwargs):
        trip_data = []
        trips = Trip.objects.filter(request_id__requester_name=request.user, request_id__status__in=["Approved", "Rescheduled", "Approved - Alterate Vehicle"])
        await_resched_trips = Trip.objects.filter(request_id__requester_name=request.user, request_id__status="Awaiting Vehicle Alteration")

        if trips:
            trip_data = []
            for current_schedule in trips:
                next_sched_trips = Trip.objects.filter(request_id__status__in=["Approved", "Rescheduled", "Approved - Alterate Vehicle"])

                next_schedules = next_sched_trips.filter(
                    request_id__vehicle=current_schedule.request_id.vehicle,
                    request_id__travel_date__gt=current_schedule.request_id.travel_date,
                )
                next_schedule = None

                if next_schedules:
                    next_schedule = next_schedules.first()

                previous_trip_id = None

                request_data = get_object_or_404(Request, request_id=current_schedule.request_id.request_id)
                if current_schedule.request_id.driver_name:
                    driver_data = get_object_or_404(User, username=current_schedule.request_id.driver_name)
                else:
                    driver_data = None
   
                trip_data.append({
                    'trip_id': current_schedule.id,
                    'travel_date': request_data.travel_date,
                    'travel_time': request_data.travel_time,
                    'return_date': request_data.return_date,
                    'return_time': request_data.return_time,
                    'driver': f"{driver_data.last_name}, {driver_data.first_name} {driver_data.middle_name}" if driver_data else "",
                    'contact_no_of_driver': driver_data.mobile_number if driver_data else "",
                    'destination': request_data.destination,
                    'vehicle': f"{request_data.vehicle.plate_number} {request_data.vehicle.model}",
                    'status': current_schedule.request_id.status,
                    'vehicle_driver_status': request_data.vehicle_driver_status_id.status
                })

                if next_schedule:
                    previous_trip = Trip.objects.filter(
                        request_id__vehicle=request_data.vehicle,
                        request_id__status__in=["Approved", "Rescheduled", "Approved - Alterate Vehicle"],
                        request_id__travel_date__lt=next_schedule.request_id.travel_date
                    ).order_by('-request_id__travel_date').first()

                    if previous_trip:
                        previous_trip_id = previous_trip.id

                    trip_data.append({
                        'previous_trip_id': previous_trip_id,
                        'next_schedule_travel_date': next_schedule.request_id.travel_date,
                        'next_schedule_travel_time': next_schedule.request_id.travel_time,
                        'next_schedule_vehicle': next_schedule.request_id.vehicle.plate_number,
                    })
        vehicle_recommendation = []
        
        if await_resched_trips:
            vehicle_recommendation = []
            for await_resched_trip in await_resched_trips:
                await_resched_trip_id = await_resched_trip.id
                await_resched_request_id = await_resched_trip.request_id.request_id
                await_resched_vehicle_capacity = await_resched_trip.request_id.vehicle.capacity
                await_resched_vehicle_travel_date = await_resched_trip.request_id.travel_date
                await_resched_vehicle_travel_time = await_resched_trip.request_id.travel_time
                await_resched_vehicle_return_date = await_resched_trip.request_id.return_date
                await_resched_vehicle_return_time = await_resched_trip.request_id.return_time

                
                unavailable_vehicles = Request.objects.filter(
                    (
                        Q(travel_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date]) &
                        Q(return_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date]) 
                    ) | (
                        Q(travel_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date]) |
                        Q(return_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date]) 
                    ) | (
                        Q(travel_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date]) &
                        Q(travel_time__range=[await_resched_vehicle_travel_time, await_resched_vehicle_return_time])
                    ) | (
                        Q(return_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date]) &
                        Q(return_time__range=[await_resched_vehicle_travel_time, await_resched_vehicle_return_time])
                    ) | (
                        Q(travel_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date]) &
                        Q(return_date__range=[await_resched_vehicle_travel_date, await_resched_vehicle_return_date])         
                    ),
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
                    
                ).exclude(
                    (Q(travel_date=await_resched_vehicle_return_date) & Q(travel_time__gte=await_resched_vehicle_return_time)) |
                    (Q(return_date=await_resched_vehicle_travel_date) & Q(return_time__lte=await_resched_vehicle_travel_time))
                ).values_list('vehicle', flat=True)

                available_vehicles = Vehicle.objects.exclude(plate_number__in=unavailable_vehicles)

                filtered_vehicle_capacity = available_vehicles.filter(capacity__lte=int(await_resched_vehicle_capacity) + 2, capacity__gte=int(await_resched_vehicle_capacity) - 2)
                vehicle_data_recommendation = []

                for vehicle in filtered_vehicle_capacity:
                    vehicle_data_recommendation.append({
                        
                        'vehicle_recommendation_plate_number': vehicle.plate_number,
                        'vehicle_recommendation_model': vehicle.model,
                        'vehicle_recommendation_type': vehicle.type,
                        'vehicle_recommendation_capacity': vehicle.capacity,
                        'vehicle_recommendation_image': str(vehicle.image)
                    })
      
                if not vehicle_data_recommendation:
                    message = 'We always strive to find the most suitable vehicle based on your preferences, but unfortunately, there are no available options at the moment.'
                else:
                    message = "We recommend alternative vehicles based on your preferences."

                vehicle_recommendation.append({
                    'trip_id': await_resched_trip_id,
                    'request_id': await_resched_request_id,
                    'travel_date': await_resched_vehicle_travel_date,
                    'travel_time': await_resched_vehicle_travel_time,
                    'return_date': await_resched_vehicle_return_date,
                    'return_time': await_resched_vehicle_return_time,
                    'message': message,
                    'preferred_seating_capacity': await_resched_vehicle_capacity,
                    'vehicle_data_recommendation': vehicle_data_recommendation
                })
              
        
        if trips or await_resched_trips:
            return JsonResponse({
                'trip_data': trip_data,
                'vehicle_recommendation': vehicle_recommendation,
            })

        return JsonResponse([], safe=False)
        

class ScheduleOfficeStaffView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        trip_data = []
        trips = Request.objects.filter(status__in=["Approved", "Rescheduled", "Approved - Alterate Vehicle"])

        for trip in trips:
            request_data = Request.objects.get(request_id=trip.request_id)
            if trip.driver_name:
                driver_data = User.objects.get(username=trip.driver_name)
            trip_data.append({
                'trip_id': trip.request_id,
                'request_id': request_data.request_id,
                'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}",
                'travel_date': request_data.travel_date,
                'travel_time': request_data.travel_time,
                'return_date': request_data.return_date,
                'return_time': request_data.return_time,
                'driver': f"{driver_data.last_name}, {driver_data.first_name} {driver_data.middle_name}",
                'contact_no_of_driver': driver_data.mobile_number,
                'destination': request_data.destination,
                'vehicle': request_data.vehicle.plate_number,
                'status': trip.status,
            })

        return JsonResponse(trip_data, safe=False)


class CheckVehicleAvailability(generics.ListAPIView):
        
    def get(self, request, *args, **kwargs):
        def convert_time(time_string):
            try:
                return datetime.strptime(time_string, '%H:%M:%S').time()
            except ValueError:
                return datetime.strptime(time_string, '%H:%M').time()
            
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')
        preferred_capacity = self.request.GET.get('preferred_capacity')

        travel_date_converted = datetime.strptime(preferred_start_travel_date, '%Y-%m-%d').date()
        travel_time_converted = convert_time(preferred_start_travel_time)
        return_date_converted = datetime.strptime(preferred_end_travel_date, '%Y-%m-%d').date()
        return_time_converted = convert_time(preferred_end_travel_time)

        travel_datetime = datetime.combine(travel_date_converted, travel_time_converted)
        travel_datetime = timezone.make_aware(travel_datetime)
        return_datetime = datetime.combine(return_date_converted, return_time_converted)
        return_datetime = timezone.make_aware(return_datetime)

        if travel_datetime > return_datetime:
            error_message = "The starting date comes after the ending date!"
            return Response({'error': error_message}, status=400)

        unavailable_vehicles = Request.objects.filter(
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
        vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
        status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
    ).exclude(
        (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gte=preferred_end_travel_time)) |
        (Q(return_date=preferred_start_travel_date) & Q(return_time__lte=preferred_start_travel_time))
    ).values_list('vehicle', flat=True)

        
        available_vehicles = Vehicle.objects.exclude(plate_number__in=unavailable_vehicles)

        available_vehicles_capacity_filtered = available_vehicles.filter(capacity__lte=int(preferred_capacity) + 2, capacity__gte=int(preferred_capacity) - 2)

        available_vehicles = list(available_vehicles_capacity_filtered.values())

        return JsonResponse(available_vehicles, safe=False)

    
class CheckDriverAvailability(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')


        unavailable_drivers = Request.objects.filter(
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
                Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
            ),
            vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
            status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Driver Absence']
        ).exclude(
            (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gte=preferred_end_travel_time)) |
            (Q(return_date=preferred_start_travel_date) & Q(return_time__lte=preferred_start_travel_time))
        ).exclude(
            driver_name__username=None
        ).values_list('driver_name__username', flat=True)

        available_drivers = User.objects.filter(role__role_name='driver').exclude(username__in=unavailable_drivers)

        available_drivers = list(available_drivers.values('id', 'first_name', 'last_name', 'middle_name', 'role_id', 'username', 'email'))

        return JsonResponse(available_drivers, safe=False)


class VehicleSchedulesView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        plate_number = self.request.GET.get('plate_number')
        trip_data = []

        trips = Request.objects.filter(status__in=["Approved", "Rescheduled", "Approved - Alterate Vehicle", "Ongoing Vehicle Maintenance"], vehicle__plate_number=plate_number)

        for trip in trips:
            
            if trip.driver_name:
                request_data_list = Request.objects.filter(request_id=trip.request_id)
                driver_data_list = User.objects.filter(username=trip.driver_name)
            
                for request_data in request_data_list:
                    for driver_data in driver_data_list:
                        trip_data.append({
                            'trip_id': trip.request_id,
                            'request_id': request_data.request_id if request_data else None,
                            'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}" if request_data else None,
                            'travel_date': request_data.travel_date if request_data else None,
                            'travel_time': request_data.travel_time if request_data else None,
                            'return_date': request_data.return_date if request_data else None,
                            'return_time': request_data.return_time if request_data else None,
                            'driver': f"{driver_data.last_name}, {driver_data.first_name} {driver_data.middle_name}" if driver_data else None,
                            'contact_no_of_driver': driver_data.mobile_number if driver_data else None,
                            'destination': request_data.destination if request_data else None,
                            'vehicle': request_data.vehicle.plate_number if request_data else None,
                            'status': trip.status,
                        })
            else:
                request_data_list = Request.objects.filter(request_id=trip.request_id)
                for request_data in request_data_list:
                    trip_data.append({
                        'trip_id': trip.request_id,
                        'request_id': request_data.request_id if request_data else None,
                        'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}" if request_data else None,
                        'travel_date': request_data.travel_date if request_data else None,
                        'travel_time': request_data.travel_time if request_data else None,
                        'return_date': request_data.return_date if request_data else None,
                        'return_time': request_data.return_time if request_data else None,
                        'destination': request_data.purpose if request_data else None,
                        'vehicle': request_data.vehicle.plate_number if request_data else None,
                        'status': trip.status,
                    })

        return JsonResponse(trip_data, safe=False)

class DriverSchedulesView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        driver_id = self.request.GET.get('driver_id')
        trip_data = []

        trips = Request.objects.filter(status__in=["Approved", "Rescheduled", "Approved - Alterate Vehicle", "Driver Absence"], driver_name__id=driver_id)

        for trip in trips:
            if trip.status == 'Driver Absence':
                request_data_list = Request.objects.filter(request_id=trip.request_id)
                driver_data_list = User.objects.filter(username=trip.driver_name)

                for request_data in request_data_list:
                    for driver_data in driver_data_list:
                        trip_data.append({
                            'trip_id': trip.request_id,
                            'request_id': request_data.request_id if request_data else None,
                            'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}" if request_data else None,
                            'travel_date': request_data.travel_date if request_data else None,
                            'travel_time': request_data.travel_time if request_data else None,
                            'return_date': request_data.return_date if request_data else None,
                            'return_time': request_data.return_time if request_data else None,
                            'driver': f"{driver_data.last_name}, {driver_data.first_name} {driver_data.middle_name}" if driver_data else None,
                            'contact_no_of_driver': driver_data.mobile_number if driver_data else None,
                            'destination': request_data.purpose if request_data else None,
                            'status': trip.status,
                        })
            else:
                request_data_list = Request.objects.filter(request_id=trip.request_id)
                driver_data_list = User.objects.filter(username=trip.driver_name)
                for request_data in request_data_list:
                    for driver_data in driver_data_list:
                        trip_data.append({
                            'trip_id': trip.request_id,
                            'request_id': request_data.request_id if request_data else None,
                            'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}" if request_data else None,
                            'travel_date': request_data.travel_date if request_data else None,
                            'travel_time': request_data.travel_time if request_data else None,
                            'return_date': request_data.return_date if request_data else None,
                            'return_time': request_data.return_time if request_data else None,
                            'driver': f"{driver_data.last_name}, {driver_data.first_name} {driver_data.middle_name}" if driver_data else None,
                            'contact_no_of_driver': driver_data.mobile_number if driver_data else None,
                            'destination': request_data.destination if request_data else None,
                            'vehicle': request_data.vehicle.plate_number if request_data else None,
                            'status': trip.status,
                        })    

        return JsonResponse(trip_data, safe=False)
    

class VehicleRecommendationAcceptance(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # channel_layer = get_channel_layer()

        plate_number = request.data.get('plate_number')  
        
        vehicle = Vehicle.objects.get(plate_number=plate_number)
        altered_vehicle_status = 'Approved - Alterate Vehicle'
        instance.status = altered_vehicle_status
        instance.vehicle = vehicle
        if instance.vehicle_driver_status_id:
            instance.vehicle_driver_status_id.plate_number = vehicle
            instance.vehicle_driver_status_id.save()
        
        instance.save()
        # requester_name = instance.requester_name
        # requester_full_name = f"{requester_name.last_name}, {requester_name.first_name} {requester_name.middle_name}"

        # vehicle_driver_status = Vehicle_Driver_Status.objects.get(description='Assigned')

        # existing_vehicle_driver_status = instance.vehicle_driver_status_id

        # existing_vehicle_driver_status.driver_id = driver
        # existing_vehicle_driver_status.save()
        # # plate_number = instance.vehicle
        # # authorized_passenger = f"{requester_full_name}, {instance.passenger_name}"
        # trip = Trip(
        #     # driver_name=driver,
        #     # plate_number=plate_number,
        #     # authorized_passenger=authorized_passenger,
        #     request_id=instance,
        # )
        # trip.save()

    #     async_to_sync(channel_layer.group_send)(
    #     f"user_{instance.requester_name}", 
    #     {
    #         'type': 'approve_notification',
    #         'message': f"Request {instance.request_id} has been approved.",
    #     }
    # )

    #     notification = Notification(
    #         owner=instance.requester_name,  
    #         subject=f"Request {instance.request_id} has been approved",  
    #     )
    #     notification.save()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
    
class TripScannedView(generics.UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        trip = Trip.objects.get(request_id=instance)

        channel_layer = get_channel_layer()
        office_staff_role = Role.objects.get(role_name='office staff')     
        office_staff_users = User.objects.filter(role=office_staff_role)

        time_zone = timezone.localtime(timezone.now())

        # time_zone_12hr_format = time_zone.strftime('%Y-%m-%d %I:%M %p') 

        type = None
        existing_vehicle_driver_status = instance.vehicle_driver_status_id
        if (instance.status == 'Approved' or instance.status == 'Approved - Alterate Vehicle') and existing_vehicle_driver_status.status == 'Reserved - Assigned':
            existing_vehicle_driver_status = instance.vehicle_driver_status_id
            existing_vehicle_driver_status.status = 'On Trip'
            existing_vehicle_driver_status.save()  

            trip.departure_time_from_office = time_zone
            trip.save()

            for user in office_staff_users:
                notification = Notification(
                    owner=user,
                    subject="A travel is on the way",
                )
                notification.save()

            async_to_sync(channel_layer.group_send)(
                'notifications', 
                {
                    'type': 'notify.request_completed',
                    'message': "A travel is on the way",
                }
            )
            type = 'Authorized'
        elif (instance.status == 'Approved' or instance.status == 'Approved - Alterate Vehicle') and existing_vehicle_driver_status.status == 'On Trip':
            existing_vehicle_driver_status = instance.vehicle_driver_status_id
            instance.status = 'Completed'
            trip.arrival_time_to_office = time_zone
            trip.save()
            instance.save()
            existing_vehicle_driver_status.status = 'Available'
            existing_vehicle_driver_status.save()

            type = 'Completed'

        elif (instance.status == 'Completed') and existing_vehicle_driver_status.status == 'Available':
            type = 'Already Completed'
        
        return Response({'message': 'Request completed successfully.', 'type': type})
    

class OnTripsGateGuardView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
      
        vehicle_driver_statuses = Vehicle_Driver_Status.objects.filter(status='On Trip')

        if not vehicle_driver_statuses:
            return JsonResponse({'error': 'No trips found with status "On Trip"'})

        results = []

        for vehicle_driver_status in vehicle_driver_statuses:
            request_fields = Request.objects.filter(vehicle_driver_status_id=vehicle_driver_status).values(
                'requester_name__first_name',
                'travel_date',
                'travel_time',
                'return_date',
                'return_time',
                'destination',
                'distance',
                'office',
                'passenger_name',
                'purpose',
                'vehicle__plate_number',
                'vehicle__model',
                'driver_name__first_name',
                'type'
            )

            trip_fields = Trip.objects.filter(request_id__vehicle_driver_status_id=vehicle_driver_status).values(
                'departure_time_from_office',
                'arrival_time_to_destination',
                'departure_time_from_destination',
                'arrival_time_to_office'
            )

            semi_result = {
                'vehicle_driver_status': vehicle_driver_status.status,
                'request': list(request_fields),
                'trip': list(trip_fields)
            }

            result = {}
            for key, value in semi_result.items():
                if isinstance(value, list):
                    for item in value:
                        result.update(item)
                else:
                    result[key] = value

            results.append(result)

        return JsonResponse(results, safe=False)

class RecentLogsGateGuardView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
      
        recent_tripss = Request.objects.filter(status__in=['Completed'], vehicle_driver_status_id__status__in=['Available']).exclude(
            purpose='Vehicle Maintenance'
        ).exclude(
            purpose= 'Driver Absence'
        )
        recent_trips = [obj.request_id for obj in recent_tripss]

        if not recent_trips:
            return JsonResponse({'error': 'No recent trips found'})

        results = []

        for recent_trip in recent_trips:
            request_fields = Request.objects.filter(request_id=recent_trip).values(
                'requester_name__first_name',
                'travel_date',
                'travel_time',
                'return_date',
                'return_time',
                'destination',
                'distance',
                'office',
                'passenger_name',
                'purpose',
                'vehicle__plate_number',
                'vehicle__model',
                'driver_name__first_name',
                'type'
            )

            trip_fields = Trip.objects.filter(request_id=recent_trip).values(
                'departure_time_from_office',
                'arrival_time_to_destination',
                'departure_time_from_destination',
                'arrival_time_to_office'
            )
            request_obj = Request.objects.get(request_id=recent_trip)
            semi_result = {
                'vehicle_driver_status': request_obj.vehicle_driver_status_id.status,
                'request': list(request_fields),
                'trip': list(trip_fields)
            }

            result = {}
            for key, value in semi_result.items():
                if isinstance(value, list):
                    for item in value:
                        result.update(item)
                else:
                    result[key] = value

            results.append(result)

        return JsonResponse(results, safe=False)

 
def download_tripticket(request, request_id):
    trip = Trip.objects.get(request_id=request_id)

    pdf_path = trip.tripticket_pdf.path

    response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')

    response['Content-Disposition'] = f'attachment; filename="tripticket{request_id}.pdf"'

    return response
