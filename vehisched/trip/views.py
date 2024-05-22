from rest_framework import generics, status
from django.http import JsonResponse
from .models import Trip
from notification.models import Notification
from accounts.models import Role
from accounts.models import User
from request.models import Request, Vehicle_Driver_Status
from vehicle.models import Vehicle
from vehicle.serializers import VehicleSerializer
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from request.serializers import RequestSerializer
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date, parse_time
from django.utils import timezone
from django.http import FileResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class ScheduleRequesterView(generics.ListAPIView):
    
    def get(self, request, *args, **kwargs):
        trip_data = []
        trips = Trip.objects.filter(request_id__requester_name=request.user, request_id__status__in=["Approved", "Rescheduled", "Approved - Alterate Vehicle"])
        await_alterate_trips = Trip.objects.filter(request_id__requester_name=request.user, request_id__status="Awaiting Vehicle Alteration")

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
                    'trip_id': current_schedule.trip_id,
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
                        previous_trip_id = previous_trip.trip_id

                    trip_data.append({
                        'previous_trip_id': previous_trip_id,
                        'next_schedule_travel_date': next_schedule.request_id.travel_date,
                        'next_schedule_travel_time': next_schedule.request_id.travel_time,
                        'next_schedule_vehicle': next_schedule.request_id.vehicle.plate_number,
                    })
        vehicle_recommendation = []
        
        if await_alterate_trips:
            vehicle_recommendation = []
            for await_alterate_trip in await_alterate_trips:
                await_alterate_trip_id = await_alterate_trip.trip_id
                await_alterate_request_id = await_alterate_trip.request_id.request_id
                await_alterate_vehicle_capacity = await_alterate_trip.request_id.vehicle.capacity
                await_alterate_vehicle_travel_date = await_alterate_trip.request_id.travel_date
                await_alterate_vehicle_travel_time = await_alterate_trip.request_id.travel_time
                await_alterate_vehicle_return_date = await_alterate_trip.request_id.return_date
                await_alterate_vehicle_return_time = await_alterate_trip.request_id.return_time
                await_alterate_from_vip_alteration = await_alterate_trip.request_id.from_vip_alteration

                
                unavailable_vehicles = Request.objects.filter(
                    (
                        Q(travel_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date]) &
                        Q(return_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date]) 
                    ) | (
                        Q(travel_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date]) |
                        Q(return_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date]) 
                    ) | (
                        Q(travel_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date]) &
                        Q(travel_time__range=[await_alterate_vehicle_travel_time, await_alterate_vehicle_return_time])
                    ) | (
                        Q(return_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date]) &
                        Q(return_time__range=[await_alterate_vehicle_travel_time, await_alterate_vehicle_return_time])
                    ) | (
                        Q(travel_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date]) &
                        Q(return_date__range=[await_alterate_vehicle_travel_date, await_alterate_vehicle_return_date])         
                    ),
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
                    
                ).exclude(
                    (Q(travel_date=await_alterate_vehicle_return_date) & Q(travel_time__gte=await_alterate_vehicle_return_time)) |
                    (Q(return_date=await_alterate_vehicle_travel_date) & Q(return_time__lte=await_alterate_vehicle_travel_time))
                ).values_list('vehicle', flat=True)

                available_vehicles = Vehicle.objects.exclude(plate_number__in=unavailable_vehicles)

                filtered_vehicle_capacity = available_vehicles.filter(capacity__lte=await_alterate_vehicle_capacity)
                vehicle_data_recommendation = []

                for vehicle in filtered_vehicle_capacity:
                    vehicle_data_recommendation.append({
                        
                        'vehicle_recommendation_plate_number': vehicle.plate_number,
                        'vehicle_recommendation_model': vehicle.model,
                        'vehicle_recommendation_type': vehicle.type,
                        'vehicle_recommendation_capacity': vehicle.capacity,
                        'vehicle_recommendation_image': str(vehicle.image)
                    })

                if await_alterate_from_vip_alteration == True:
                    if not vehicle_data_recommendation:
                        message = "is used by the higher official. We apologize for any inconvenience this may cause. We always strive to find the most suitable vehicle based on your preferences, but unfortunately, there are no available options at the moment."
                    else:
                        message = "is used by the higher official. We apologize for any inconvenience this may cause. We recommend alternative vehicles based on your preferences."
                else:
                    if not vehicle_data_recommendation:
                        message = "is currently undergoing unexpected maintenance. We apologize for any inconvenience this may cause. We always strive to find the most suitable vehicle based on your preferences, but unfortunately, there are no available options at the moment."
                    else:
                        message = "is currently undergoing unexpected maintenance. We apologize for any inconvenience this may cause. We recommend alternative vehicles based on your preferences."
                

                vehicle_recommendation.append({
                    'trip_id': await_alterate_trip_id,
                    'request_id': await_alterate_request_id,
                    'travel_date': await_alterate_vehicle_travel_date,
                    'travel_time': await_alterate_vehicle_travel_time,
                    'return_date': await_alterate_vehicle_return_date,
                    'return_time': await_alterate_vehicle_return_time,
                    'message': message,
                    'preferred_seating_capacity': await_alterate_vehicle_capacity,
                    'vehicle_data_recommendation': vehicle_data_recommendation
                })
              
        
        if trips or await_alterate_trips:
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

        available_vehicles_capacity_filtered = available_vehicles.filter(capacity__lte=preferred_capacity)

        serializer = VehicleSerializer(available_vehicles_capacity_filtered, many=True)
        serialized_data = serializer.data

        return Response(serialized_data)

    
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
    
class CheckTimeAvailability(generics.ListAPIView):
    
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = datetime.strptime(self.request.GET.get('preferred_start_travel_date'), "%Y-%m-%d")
        preferred_end_travel_date = datetime.strptime(self.request.GET.get('preferred_end_travel_date'), "%Y-%m-%d")
        selected_vehicle = self.request.GET.get("selected_vehicle")
        user_id = self.request.GET.get("user_id")
        role = self.request.GET.get("role")
        is_another_vehicle = self.request.GET.get("is_another_vehicle")
        available_times_by_date = {}
        current_date = preferred_start_travel_date
        unavailable_times = {'unavailable_time_in_date_range': []}
        is_unavailable_within_day_only = False
        unavailable_within_date_range = None
        unavailable_time_greater = None
        is_unavailable_within_day_greater = False
       
        
        while current_date <= preferred_end_travel_date:
            start_time = datetime.combine(current_date, datetime.min.time())
            end_time = datetime.combine(current_date, datetime.max.time())
            time_slots = self.generate_time_slots(start_time, end_time)
            available_times_by_date[current_date.strftime("%Y-%m-%d")] = []
            
            for time_slot in time_slots:
                is_available, is_unavailable_within_date_range_less, is_unavailable_within_date_range_greater, is_unavailable_within_day = self.is_time_slot_available(time_slot, current_date, selected_vehicle, role, user_id, is_another_vehicle)
                
                

                if is_unavailable_within_day:
                    if preferred_start_travel_date.date() == preferred_end_travel_date.date():
                        is_unavailable_within_day_only = True
                    
                        
                if is_unavailable_within_date_range_less:
                    
                    if unavailable_within_date_range is not None and preferred_start_travel_date.date() != preferred_end_travel_date.date() and preferred_start_travel_date.date() < unavailable_within_date_range.date(): 
                        
                        if unavailable_within_date_range is not None and time_slot.time() > unavailable_within_date_range.time():
                            
                            unavailable_times['unavailable_time_in_date_range'].append(unavailable_within_date_range.date())
                            
                            continue
                        
                if is_unavailable_within_date_range_greater: 
                    
                    if unavailable_within_date_range is not None and preferred_start_travel_date.date() != preferred_end_travel_date.date() and preferred_start_travel_date.date() == unavailable_within_date_range.date(): 
                        
                        if unavailable_within_date_range is not None and time_slot.time() > unavailable_within_date_range.time():
                            unavailable_time_greater = unavailable_within_date_range

                if is_available:
                    available_times_by_date[current_date.strftime("%Y-%m-%d")].append(time_slot.strftime("%H:%M"))
                else:
                    unavailable_within_date_range = time_slot

                if is_unavailable_within_day and not is_unavailable_within_day_greater:
                    is_unavailable_within_day_greater = is_unavailable_within_day

            current_date += timedelta(days=1)

            if unavailable_time_greater is not None and preferred_start_travel_date.date() != preferred_end_travel_date.date() and preferred_start_travel_date.date() == unavailable_time_greater.date() and is_unavailable_within_day_greater:

                time_slotss = self.generate_time_slots_for_greater(start_time, end_time, unavailable_time_greater.time())
            
                available_times_by_date[preferred_start_travel_date.date().strftime("%Y-%m-%d")] = [slot.strftime("%H:%M") for slot in time_slotss]
        
        formatted_available_times = {date: {'available_time': times} for date, times in available_times_by_date.items()}
        formatted_available_times['unavailable_time_in_date_range'] = unavailable_times
        if is_unavailable_within_day_only:
            formatted_available_times['is_unavailable_within_day_only'] = is_unavailable_within_day_only
        return Response(formatted_available_times)

    def generate_time_slots(self, start_time, end_time):
        time_slots = []
        current_time = start_time
        while current_time < end_time:
            current_time_str = current_time.strftime("%H:%M")
            
            if current_time_str not in ["11:00", "11:30", "12:00", "12:30"]:
                time_slots.append(current_time)
            
            current_time += timedelta(minutes=30)
        
        return time_slots

    def generate_time_slots_for_greater(self, start_time, end_time, unavailable_time_greater):
        time_slots = []
        current_time = start_time
        
        while current_time < end_time:
            current_time_str = current_time.strftime("%H:%M")
  
            if current_time_str not in ["11:00", "11:30", "12:00", "12:30"]:
                
                if unavailable_time_greater and unavailable_time_greater < current_time.time():
                    time_slots.append(current_time)

            current_time += timedelta(minutes=30)
        
        return time_slots

    def is_time_slot_available(self, time_slot, date, selected_vehicle, role, user_id, is_another_vehicle):
        time_slot_time = time_slot.time()
        preferred_start_travel_date = date 
        preferred_end_travel_date = date 
        preferred_start_travel_time = time_slot_time 
        preferred_end_travel_time = time_slot_time

        if (role == 'requester' and is_another_vehicle == 'false') or (role == 'vip' and is_another_vehicle == 'true'):
            overlapping_requests = Request.objects.filter(
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
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
                ).exclude(
                    (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gt=preferred_end_travel_time)) |
                    (Q(return_date=preferred_start_travel_date) & Q(return_time__lt=preferred_start_travel_time))     
                )
        
            is_available = not overlapping_requests.exists()

            is_unavailable_within_day = False 
         
            if not is_available:
                
                for request in overlapping_requests:
                    if request.travel_date == request.return_date:
                        is_unavailable_within_day = True
                        
                        break

            overlapping_date_range_less = Request.objects.filter(
                
                Q(travel_date=date, travel_time__lte=time_slot_time),
                status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
                    )
            is_available_overlapping_date_range_less = not overlapping_date_range_less.exists()
 
            is_unavailable_within_date_range_less = False
            if not is_available_overlapping_date_range_less:
                is_unavailable_within_date_range_less = True

            overlapping_date_range_greater = Request.objects.filter(
                
                Q(travel_date=date, return_time__lte=time_slot_time),
                status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
                    )
            is_available_overlapping_date_range_greater = not overlapping_date_range_greater.exists()
 
            is_unavailable_within_date_range_greater = False
            if not is_available_overlapping_date_range_greater:
                is_unavailable_within_date_range_greater = True
            
            
            return is_available, is_unavailable_within_date_range_less, is_unavailable_within_date_range_greater, is_unavailable_within_day
        
        elif role == "vip" and is_another_vehicle == 'false':
            owner = User.objects.get(id=user_id)
            
            overlapping_requests = None
            is_available = False
            overlapping_date_range_less = None
            overlapping_date_range_greater = None
            is_unavailable_within_date_range_less = False
            is_unavailable_within_date_range_greater = False
            is_available_overlapping_date_range_less = False
            is_available_overlapping_date_range_greater = False
            is_unavailable_within_day = False


            # ------------------  overlapping_requests_owner   --------------------------------------------#  
            overlapping_requests_owner = Request.objects.filter(
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
                    requester_name=owner,
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Approved'],
                ).exclude(
                    (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gt=preferred_end_travel_time)) |
                    (Q(return_date=preferred_start_travel_date) & Q(return_time__lt=preferred_start_travel_time))     
                )
            

            # ------------------  overlapping_date_range_less_owner   --------------------------------------------#  
            overlapping_date_range_less_owner = Request.objects.filter(
                
                Q(travel_date=date, travel_time__lte=time_slot_time),
                status__in=['Approved'],
                requester_name=owner,
                vehicle=selected_vehicle,
                    )
            if overlapping_date_range_less_owner is not None and overlapping_date_range_less_owner.exists():
                overlapping_date_range_less = overlapping_date_range_less_owner

            if overlapping_date_range_less is not None:

                is_available_overlapping_date_range_less = not overlapping_date_range_less.exists()

            if not is_available_overlapping_date_range_less:
                is_unavailable_within_date_range_less = True


            # ------------------  overlapping_date_range_greater_owner   --------------------------------------------#  
            overlapping_date_range_greater_owner = Request.objects.filter(
                
                Q(travel_date=date, return_time__lte=time_slot_time),
                status__in=['Approved'],
                requester_name=owner,
                vehicle=selected_vehicle,
                    )
            if overlapping_date_range_greater_owner is not None and overlapping_date_range_greater_owner.exists():
                overlapping_date_range_greater = overlapping_date_range_greater_owner

            if overlapping_date_range_greater is not None:
                is_available_overlapping_date_range_greater = not overlapping_date_range_greater.exists()

            if not is_available_overlapping_date_range_greater:
                is_unavailable_within_date_range_greater = True


            # ------------------  overlapping_requests_maintenance   --------------------------------------------#
            overlapping_requests_maintenance = Request.objects.filter(
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
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Ongoing Vehicle Maintenance'],
                ).exclude(
                    (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gt=preferred_end_travel_time)) |
                    (Q(return_date=preferred_start_travel_date) & Q(return_time__lt=preferred_start_travel_time))     
                )


            # ------------------  overlapping_date_range_less_maintenance   --------------------------------------------#
            overlapping_date_range_less_maintenance = Request.objects.filter(
                
                Q(travel_date=date, travel_time__lte=time_slot_time),
                status__in=['Ongoing Vehicle Maintenance'],
                vehicle=selected_vehicle,
                    )
            if overlapping_date_range_less_maintenance is not None and overlapping_date_range_less_maintenance.exists():
                overlapping_date_range_less = overlapping_date_range_less_maintenance
            if overlapping_date_range_less is not None:
                is_available_overlapping_date_range_less = not overlapping_date_range_less.exists()

            if not is_available_overlapping_date_range_less:
                is_unavailable_within_date_range_less = True
            

            # ------------------  overlapping_date_range_greater_maintenance   --------------------------------------------#
            overlapping_date_range_greater_maintenance = Request.objects.filter(
                
                Q(travel_date=date, return_time__lte=time_slot_time),
                status__in=['Ongoing Vehicle Maintenance'],
                vehicle=selected_vehicle,
                    )
            if overlapping_date_range_greater is not None:
                is_available_overlapping_date_range_greater = not overlapping_date_range_greater.exists()

            if overlapping_date_range_greater_maintenance is not None and overlapping_date_range_greater_maintenance.exists():
                overlapping_date_range_greater = overlapping_date_range_greater_maintenance

            if not is_available_overlapping_date_range_greater:
                is_unavailable_within_date_range_greater = True


            # ------------------------------------- is_available logic -----------------------------------------------#
            is_available = not overlapping_requests_owner.exists() and not overlapping_requests_maintenance.exists()

            if not is_available:
                if overlapping_requests_owner.exists():
                    for request in overlapping_requests_owner:
                        if request.travel_date == request.return_date:
                            is_unavailable_within_day = True
                            
                            break
                if overlapping_requests_maintenance.exists():
                    for request in overlapping_requests_maintenance:
                        if request.travel_date == request.return_date:
                            is_unavailable_within_day = True
                            
                            break
                        
            # ---------------------------------------------------------------------------------------------------------#                    
            return is_available, is_unavailable_within_date_range_less, is_unavailable_within_date_range_greater, is_unavailable_within_day


class CheckReturnTimeAvailability(generics.ListAPIView):
    
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_travel_time = self.request.GET.get("preferred_travel_time")
        user_id = self.request.GET.get("user_id")
        role = self.request.GET.get("role")
        is_another_vehicle = self.request.GET.get("is_another_vehicle")
        selected_vehicle = self.request.GET.get("selected_vehicle")

        start_date = datetime.strptime(preferred_start_travel_date, "%Y-%m-%d")
        end_date = datetime.strptime(preferred_end_travel_date, "%Y-%m-%d")

        available_times_by_date = {}

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            existing_request_after = None
            existing_request_before = None

            if role == 'requester' and is_another_vehicle == 'false':
                existing_request_after = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, return_time__gte=preferred_travel_time, 
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],)
                existing_request_before = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, travel_time__lte=preferred_travel_time, 
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'])
            
            elif role == "vip" and is_another_vehicle == 'false':
                owner = User.objects.get(id=user_id)
                existing_request_after_owner = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, return_time__gte=preferred_travel_time, 
                    requester_name=owner,
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Approved'],)
                existing_request_before_owner = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, travel_time__lte=preferred_travel_time, 
                    requester_name=owner,
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Approved'],)
                
                if existing_request_before_owner is not None and existing_request_before_owner.exists():
                    existing_request_before = existing_request_before_owner

                if existing_request_after_owner is not None and existing_request_after_owner.exists():
                    existing_request_after = existing_request_after_owner
            
                existing_request_after_maintenance = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, return_time__gte=preferred_travel_time, 
                        vehicle=selected_vehicle,
                        vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                        status__in=['Ongoing Vehicle Maintenance'],)
                existing_request_before_maintenance = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, travel_time__lte=preferred_travel_time, 
                        vehicle=selected_vehicle,
                        vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                        status__in=['Ongoing Vehicle Maintenance'],)
                
                if existing_request_before_maintenance is not None and existing_request_before_maintenance.exists():
                    existing_request_before = existing_request_before_maintenance
                
                if existing_request_after_maintenance is not None and existing_request_after_maintenance.exists():
                    existing_request_after = existing_request_after_maintenance

            elif role == 'vip' and is_another_vehicle == 'true':
                existing_request_after = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, return_time__gte=preferred_travel_time, 
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],)
                existing_request_before = Request.objects.filter(travel_date=date_str, return_date=preferred_end_travel_date, travel_time__lte=preferred_travel_time, 
                    vehicle=selected_vehicle,
                    vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
                    status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'])
            
            start_time = datetime.combine(current_date, datetime.strptime(preferred_travel_time, "%H:%M").time())
            end_time = start_time + timedelta(hours=24)
 
            exclude_before_time = None
            exclude_after_time = None
            
            if existing_request_after is not None and existing_request_after.exists():
                exclude_after_time = min(existing_request_after.values_list('travel_time', flat=True))
               
            if existing_request_before is not None and existing_request_before.exists():
                exclude_before_time = max(existing_request_before.values_list('return_time', flat=True))
           
            time_slots = self.generate_time_slots(start_time, end_time, exclude_before_time, exclude_after_time)
          
            available_times_by_date[date_str] = [slot.strftime("%H:%M") for slot in time_slots]
            
            current_date += timedelta(days=1)
        
        formatted_available_times = {date: times for date, times in available_times_by_date.items()}
        return Response(formatted_available_times)
    
    def generate_time_slots(self, start_time, end_time, exclude_before_time=None, exclude_after_time=None):
        time_slots = []
        current_time = start_time
        
        while current_time < end_time:
            current_time_str = current_time.strftime("%H:%M")
  
            if current_time_str not in ["11:00", "11:30", "12:00", "12:30"]:
                
                if exclude_after_time and exclude_after_time > current_time.time():
                    time_slots.append(current_time)

                if exclude_before_time and exclude_before_time < current_time.time():
                    time_slots.append(current_time)

            current_time += timedelta(minutes=30)
        
        return time_slots
        
    
class CheckScheduleConflictsForOneway(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')
        selected_vehicle = self.request.GET.get("selected_vehicle")

        schedule_conflicts = Request.objects.filter(
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
            vehicle=selected_vehicle,
            vehicle_driver_status_id__status__in = ['Reserved - Assigned', 'On Trip', 'Unavailable'],
            status__in=['Pending', 'Approved', 'Rescheduled', 'Awaiting Rescheduling', 'Approved - Alterate Vehicle', 'Awaiting Vehicle Alteration', 'Ongoing Vehicle Maintenance'],
        ).exclude(
            (Q(travel_date=preferred_end_travel_date) & Q(travel_time__gt=preferred_end_travel_time)) |
            (Q(return_date=preferred_start_travel_date) & Q(return_time__lt=preferred_start_travel_time))     
        )
        if schedule_conflicts.exists():
            error_message = "There's a conflict with your estimated return date and time. Please change your travel date and then re-enter your destination. Thank you!"
            return Response({'error': error_message}, status=400)
        else: 
            return Response({"success"})
    

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
        #     # authorized_passenger=authorized_passenger
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

        travel_datetime = datetime.combine(instance.travel_date, instance.travel_time)
        travel_datetime = timezone.make_aware(travel_datetime)

        time_zone = timezone.localtime(timezone.now())

        # time_zone_12hr_format = time_zone.strftime('%Y-%m-%d %I:%M %p') 
        type = None
        if travel_datetime > time_zone:
            type =  'Not Yet'
        else:    
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
                        subject=f"{instance.requester_name} is on the way to {instance.destination}",
                    )
                    notification.save()

                async_to_sync(channel_layer.group_send)(
                    'notifications', 
                    {
                        'type': 'notify.request_ontheway',
                        'message': f"{instance.requester_name} is on the way to {instance.destination}",
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

                for user in office_staff_users:
                    notification = Notification(
                        owner=user,
                        subject=f"The travel to {instance.destination} using {instance.vehicle} has been successfully completed.",
                    )
                    notification.save()

                async_to_sync(channel_layer.group_send)(
                    'notifications', 
                    {
                        'type': 'notify.request_completed',
                        'message': f"The travel to {instance.destination} using {instance.vehicle} has been successfully completed.",
                    }
                )

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
                'type__name'
            )

            trip_fields = Trip.objects.filter(request_id__vehicle_driver_status_id=vehicle_driver_status).values(
                'trip_id',
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
                'type__name'
            )

            trip_fields = Trip.objects.filter(request_id=recent_trip).values(
                'trip_id',
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

class DriverOwnScheduleView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
      
        recent_tripss = Request.objects.filter(status__in=['Approved', 'Approved - Alterate Vehicle', 'Rescheduled'], driver_name=request.user).exclude(
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
                'type__name'
            )

            trip_fields = Trip.objects.filter(request_id=recent_trip).values(
                'trip_id',
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

class DriverTripsView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
      
        recent_tripss = Request.objects.filter(status__in=['Completed', 'Canceled', 'Rescheduled'], driver_name=request.user).exclude(
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
                'type__name',
                'status'
            )

            trip_fields = Trip.objects.filter(request_id=recent_trip).values(
                'trip_id',
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

def download_printedform(request, request_id):
    trip = Trip.objects.get(request_id=request_id)

    pdf_path = trip.requestform_pdf.path

    response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')

    response['Content-Disposition'] = f'attachment; filename="requestform{request_id}.pdf"'

    return response
