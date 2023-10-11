from rest_framework import generics
from django.http import JsonResponse
from .models import TripTicket
from accounts.models import User
from request.models import Request
from vehicle.models import Vehicle
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse

class ScheduleRequesterView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        trip_data = []
        trip_tickets = TripTicket.objects.filter(request_number__requester_name=request.user, status__description="Scheduled")

        if not trip_tickets:
            raise PermissionDenied

        for ticket in trip_tickets:
            request_data = Request.objects.get(request_id=ticket.request_number.request_id)
            driver_data = User.objects.get(username=ticket.driver_name)
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














    


