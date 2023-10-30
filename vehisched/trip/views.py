from rest_framework import generics
from django.http import JsonResponse
from .models import Trip
from accounts.models import User
from request.models import Request
from vehicle.models import Vehicle
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.serializers import serialize
import json


class ScheduleRequesterView(generics.ListAPIView):
    
    def get(self, request, *args, **kwargs):
        
        trips = Trip.objects.filter(request_id__requester_name=request.user, request_id__status="Approved")
        await_resched_trips = Trip.objects.filter(request_id__requester_name=request.user, request_id__status="Awaiting Rescheduling")

        # if not trips:
        #     raise PermissionDenied
        if trips:
            trip_data = []
            for current_schedule in trips:
                next_sched_trips = Trip.objects.filter(request_id__status="Approved")

                next_schedules = next_sched_trips.filter(
                    request_id__vehicle=current_schedule.request_id.vehicle,
                    request_id__travel_date__gt=current_schedule.request_id.travel_date,
                )
                next_schedule = None

                if next_schedules:
                    next_schedule = next_schedules.first()

                previous_trip_id = None

                request_data = get_object_or_404(Request, request_id=current_schedule.request_id.request_id)
                driver_data = get_object_or_404(User, username=current_schedule.request_id.driver_name)

                trip_data.append({
                    'trip_id': current_schedule.id,
                    'travel_date': request_data.travel_date,
                    'travel_time': request_data.travel_time,
                    'return_date': request_data.return_date,
                    'return_time': request_data.return_time,
                    'driver': f"{driver_data.last_name}, {driver_data.first_name} {driver_data.middle_name}",
                    'contact_no_of_driver': driver_data.mobile_number,
                    'destination': request_data.destination,
                    'vehicle': f"{request_data.vehicle.plate_number} {request_data.vehicle.model}",
                    'status': current_schedule.request_id.status,
                })

                if next_schedule:
                    previous_trip = Trip.objects.filter(
                        request_id__vehicle=request_data.vehicle,
                        request_id__status="Approved",
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
  
        if await_resched_trips:
            await_resched_trip_queryset = await_resched_trips.all()
            for await_resched_trip in await_resched_trip_queryset:
                await_resched_trip_id = await_resched_trip.id
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
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling'],
                    
                ).exclude(
                    (Q(travel_date=await_resched_vehicle_return_date) & Q(travel_time__gte=await_resched_vehicle_return_time)) |
                    (Q(return_date=await_resched_vehicle_travel_date) & Q(return_time__lte=await_resched_vehicle_travel_time))
                ).values_list('vehicle', flat=True)

                available_vehicles = Vehicle.objects.exclude(plate_number__in=unavailable_vehicles)

                filtered_vehicle_capacity = available_vehicles.filter(capacity__gte=await_resched_vehicle_capacity)
                vehicle_data_recommendation = []

                for vehicle in filtered_vehicle_capacity:
                    vehicle_data_recommendation.append({
                        
                        'vehicle_recommendation_plate_number': vehicle.plate_number,
                        'vehicle_recommendation_model': vehicle.model,
                        'vehicle_recommendation_type': vehicle.type,
                        'vehicle_recommendation_capacity': vehicle.capacity,
                        'vehicle_recommendation_image': str(vehicle.image)
                    })
      
                vehicle_recommendation = []
                vehicle_recommendation.append({
                    'trip_id': await_resched_trip_id,
                    'travel_date': await_resched_vehicle_travel_date,
                    'travel_time': await_resched_vehicle_travel_time,
                    'return_date': await_resched_vehicle_return_date,
                    'return_time': await_resched_vehicle_return_time,
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
        trips = Trip.objects.filter(request_id__status="Approved")

        for trip in trips:
            request_data = Request.objects.get(request_id=trip.request_id.request_id)
            driver_data = User.objects.get(username=trip.request_id.driver_name)
            trip_data.append({
                'trip_id': trip.id,
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
                'status': trip.request_id.status,
            })

        return JsonResponse(trip_data, safe=False)


class CheckVehicleAvailability(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')

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
        status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling'],
    ).exclude(
        (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gte=preferred_end_travel_time)) |
        (Q(return_date=preferred_start_travel_date) & Q(return_time__lte=preferred_start_travel_time))
    ).values_list('vehicle', flat=True)

        
        available_vehicles = Vehicle.objects.exclude(plate_number__in=unavailable_vehicles)

        available_vehicles = list(available_vehicles.values())

        return JsonResponse(available_vehicles, safe=False)

    
class CheckDriverAvailability(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')


        unavailable_drivers = Trip.objects.filter(
            (
                Q(request_id__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_id__return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
            ) | (
                Q(request_id__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) |
                Q(request_id__return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
            ) | (
                Q(request_id__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_id__travel_time__range=[preferred_start_travel_time, preferred_end_travel_time])
            ) | (
                Q(request_id__return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_id__return_time__range=[preferred_start_travel_time, preferred_end_travel_time])
            ) | (
                Q(request_id__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_id__return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_id__travel_time__gte=preferred_start_travel_time) &
                Q(request_id__return_time__lte=preferred_end_travel_time)
            ),
            request_id__vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
            request_id__status__in=['Pending', 'Approved', 'Rescheduled'],
        ).exclude(
            (Q(request_id__travel_date=preferred_end_travel_date) & Q(request_id__travel_time__gte=preferred_end_travel_time)) |
            (Q(request_id__return_date=preferred_start_travel_date) & Q(request_id__return_time__lte=preferred_start_travel_time))
        ).values_list('request_id__driver_name__username', flat=True)

        available_drivers = User.objects.filter(role__role_name='driver').exclude(username__in=unavailable_drivers)

        available_drivers = list(available_drivers.values('id', 'first_name', 'last_name', 'middle_name', 'role_id', 'username', 'email'))

        return JsonResponse(available_drivers, safe=False)


class VehicleSchedulesView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        plate_number = self.request.GET.get('plate_number')
        trip_data = []

        trips = Trip.objects.filter(request_id__status="Approved", request_id__vehicle__plate_number=plate_number)

        for trip in trips:
            request_data = get_object_or_404(Request, request_id=trip.request_id.request_id)
            driver_data = get_object_or_404(User, username=trip.request_id.driver_name)
            trip_data.append({
                'trip_id': trip.id,
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
                'status': trip.request_id.status,
            })

        return JsonResponse(trip_data, safe=False)

class DriverSchedulesView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        driver_id = self.request.GET.get('driver_id')
        trip_data = []

        trips = Trip.objects.filter(request_id__status="Approved", request_id__driver_name__id=driver_id)

        for trip in trips:
            request_data = get_object_or_404(Request, request_id=trip.request_id.request_id)
            driver_data = get_object_or_404(User, username=trip.request_id.driver_name)
            
            trip_data.append({
                'trip_id': trip.id,
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
                'status': trip.request_id.status,
            })

        return JsonResponse(trip_data, safe=False)
