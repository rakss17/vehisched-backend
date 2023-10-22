from rest_framework import generics
from django.http import JsonResponse
from .models import TripTicket
from accounts.models import User
from request.models import Request
from vehicle.models import Vehicle
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

class ScheduleRequesterView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        trip_data = []
        trip_tickets = TripTicket.objects.filter(request_number__requester_name=request.user, status__description="Scheduled")
        next_sched_trip_tickets = TripTicket.objects.filter(status__description="Scheduled")

        if not trip_tickets:
            raise PermissionDenied

        current_schedule = trip_tickets.first() 

        next_schedules = next_sched_trip_tickets.filter(
            request_number__vehicle=current_schedule.request_number.vehicle,
            request_number__travel_date__gt=current_schedule.request_number.travel_date,
        )
        next_schedule = None
        
        if next_schedules:
            next_schedule = next_schedules.first()

        
        previous_tripticket_id = None

        for ticket in trip_tickets.order_by('request_number__travel_date'):
            request_data = get_object_or_404(Request, request_id=ticket.request_number.request_id)
            driver_data = get_object_or_404(User, username=ticket.driver_name)
            trip_data.append({
                'tripticket_id': ticket.id,
                'travel_date': request_data.travel_date,
                'travel_time': request_data.travel_time,
                'return_date': request_data.return_date,
                'return_time': request_data.return_time,
                'driver': request_data.driver_name,
                'contact_no_of_driver': driver_data.mobile_number,
                'destination': request_data.destination,
                'vehicle': request_data.vehicle.plate_number,
                'status': ticket.status.description,
            })

            
            previous_ticket = TripTicket.objects.filter(
                plate_number=request_data.vehicle.plate_number,
                status__description="Scheduled",
                request_number__travel_date__lt=next_schedule.request_number.travel_date
            ).order_by('-request_number__travel_date').first()

            
            if previous_ticket:
                previous_tripticket_id = previous_ticket.id

        if next_schedule:
            trip_data.append({
                'previous_tripticket_id': previous_tripticket_id,
                'next_schedule_travel_date': next_schedule.request_number.travel_date,
                'next_schedule_travel_time': next_schedule.request_number.travel_time,
                'next_schedule_vehicle': next_schedule.request_number.vehicle.plate_number,
            })

        return JsonResponse(trip_data, safe=False)
    
class ScheduleOfficeStaffView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        trip_data = []
        trip_tickets = TripTicket.objects.filter(status__description="Scheduled")

        for ticket in trip_tickets:
            request_data = Request.objects.get(request_id=ticket.request_number.request_id)
            driver_data = User.objects.get(username=ticket.driver_name)
            trip_data.append({
                'tripticket_id': ticket.id,
                'request_id': request_data.request_id,
                'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}",
                'travel_date': request_data.travel_date,
                'travel_time': request_data.travel_time,
                'return_date': request_data.return_date,
                'return_time': request_data.return_time,
                'driver': request_data.driver_name,
                'contact_no_of_driver': driver_data.mobile_number,
                'destination': request_data.destination,
                'vehicle': request_data.vehicle.plate_number,
                'status': ticket.status.description,
            })

        return JsonResponse(trip_data, safe=False)


class CheckVehicleAvailability(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        preferred_start_travel_date = self.request.GET.get('preferred_start_travel_date')
        preferred_end_travel_date = self.request.GET.get('preferred_end_travel_date')
        preferred_start_travel_time = self.request.GET.get('preferred_start_travel_time')
        preferred_end_travel_time = self.request.GET.get('preferred_end_travel_time')
        category = self.request.GET.get('category')
        sub_category = self.request.GET.get('sub_category')


        unavailable_vehicles = Request.objects.filter(
        (
            Q(travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
            Q(return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
            ~Q(travel_time__range=[preferred_start_travel_time, preferred_end_travel_time]) &
            ~Q(return_time__range=[preferred_start_travel_time, preferred_end_travel_time])
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
        vehicle__tripticket__vehicle_status__in=['Reserved', 'On trip', 'Unavailable'],
        status__in=['Pending', 'Approved', 'Reschedule'],
        
   
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


        unavailable_drivers = TripTicket.objects.filter(
            (
                Q(request_number__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_number__return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                ~Q(request_number__travel_time__range=[preferred_start_travel_time, preferred_end_travel_time]) &
                ~Q(request_number__return_time__range=[preferred_start_travel_time, preferred_end_travel_time])
            ) | (
                Q(request_number__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) |
                Q(request_number__return_date__range=[preferred_start_travel_date, preferred_end_travel_date])
            ) | (
                Q(request_number__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_number__travel_time__range=[preferred_start_travel_time, preferred_end_travel_time])
            ) | (
                Q(request_number__return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_number__return_time__range=[preferred_start_travel_time, preferred_end_travel_time])
            ) | (
                Q(request_number__travel_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_number__return_date__range=[preferred_start_travel_date, preferred_end_travel_date]) &
                Q(request_number__travel_time__gte=preferred_start_travel_time) &
                Q(request_number__return_time__lte=preferred_end_travel_time)
            ),
            driver_status__description__in=['Assigned', 'On trip', 'Unavailable'],
            request_number__status__description__in=['Pending', 'Approved', 'Reschedule'],
        ).exclude(
            (Q(request_number__travel_date=preferred_end_travel_date) & Q(request_number__travel_time__gte=preferred_end_travel_time)) |
            (Q(request_number__return_date=preferred_start_travel_date) & Q(request_number__return_time__lte=preferred_start_travel_time))
        ).values_list('driver_name__username', flat=True)

        available_drivers = User.objects.filter(role__role_name='driver').exclude(username__in=unavailable_drivers)

        available_drivers = list(available_drivers.values('id', 'first_name', 'last_name', 'middle_name', 'role_id', 'username', 'email'))

        return JsonResponse(available_drivers, safe=False)


class VehicleSchedulesView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        plate_number = self.request.GET.get('plate_number')
        trip_data = []

        trip_tickets = TripTicket.objects.filter(status__description="Scheduled", request_number__vehicle__plate_number=plate_number)

        for ticket in trip_tickets:
            request_data = get_object_or_404(Request, request_id=ticket.request_number.request_id)
            driver_data = get_object_or_404(User, username=ticket.driver_name)
            trip_data.append({
                'tripticket_id': ticket.id,
                'request_id': request_data.request_id,
                'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}",
                'travel_date': request_data.travel_date,
                'travel_time': request_data.travel_time,
                'return_date': request_data.return_date,
                'return_time': request_data.return_time,
                'driver': request_data.driver_name,
                'contact_no_of_driver': driver_data.mobile_number,
                'destination': request_data.destination,
                'vehicle': request_data.vehicle.plate_number,
                'status': ticket.status.description,
            })

        return JsonResponse(trip_data, safe=False)

class DriverSchedulesView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        driver_id = self.request.GET.get('driver_id')
        trip_data = []

        trip_tickets = TripTicket.objects.filter(status__description="Scheduled", driver_name__id=driver_id)

        for ticket in trip_tickets:
            request_data = get_object_or_404(Request, request_id=ticket.request_number.request_id)
            driver_data = get_object_or_404(User, username=ticket.driver_name)
            trip_data.append({
                'tripticket_id': ticket.id,
                'request_id': request_data.request_id,
                'requester_name': f"{request_data.requester_name.last_name}, {request_data.requester_name.first_name} {request_data.requester_name.middle_name}",
                'travel_date': request_data.travel_date,
                'travel_time': request_data.travel_time,
                'return_date': request_data.return_date,
                'return_time': request_data.return_time,
                'driver': request_data.driver_name,
                'contact_no_of_driver': driver_data.mobile_number,
                'destination': request_data.destination,
                'vehicle': request_data.vehicle.plate_number,
                'status': ticket.status.description,
            })

        return JsonResponse(trip_data, safe=False)
