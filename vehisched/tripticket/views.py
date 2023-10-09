from rest_framework import generics
from django.http import JsonResponse
from .models import TripTicket
from accounts.models import User
from request.models import Request
from vehicle.models import Vehicle
from django.core.exceptions import PermissionDenied
from django.core import serializers
from datetime import datetime

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
        preferred_start_travel_date = request.data.get('preferred_start_travel_date')
        preferred_end_travel_date = request.data.get('preferred_end_travel_date')
        preferred_start_travel_time = request.data.get('preferred_start_travel_time')
        preferred_end_travel_time = request.data.get('preferred_end_travel_time')

        # Convert the preferred start and end travel dates and times to datetime objects
        preferred_start_travel_datetime = None
        if preferred_start_travel_date and preferred_start_travel_time:
            preferred_start_travel_datetime = datetime.combine(preferred_start_travel_date, preferred_start_travel_time)

        preferred_end_travel_datetime = None
        if preferred_end_travel_date and preferred_end_travel_time:
            preferred_end_travel_datetime = datetime.combine(preferred_end_travel_date, preferred_end_travel_time)

        # Get all scheduled trip tickets
        scheduled_trips = TripTicket.objects.filter(status__description="Scheduled")

        # Initialize a list to store the plate numbers of unavailable vehicles
        unavailable_vehicles = []

        # Check each scheduled trip
        for trip in scheduled_trips:
            # Get the associated request
            request = Request.objects.get(request_id=trip.request_number.request_id)

            # Convert the request travel date and time to datetime objects
            request_start_travel_datetime = datetime.combine(request.travel_date, request.travel_time)
            request_end_travel_datetime = datetime.combine(request.return_date, request.return_time)

            # Check if the requested trip overlaps with the scheduled trip
            if preferred_start_travel_datetime and preferred_end_travel_datetime and (
                (preferred_start_travel_datetime <= request_start_travel_datetime <= preferred_end_travel_datetime) or
                (preferred_start_travel_datetime <= request_end_travel_datetime <= preferred_end_travel_datetime) or
                (request_start_travel_datetime <= preferred_start_travel_datetime <= request_end_travel_datetime) or
                (request_start_travel_datetime <= preferred_end_travel_datetime <= request_end_travel_datetime)
            ):
                unavailable_vehicles.append(trip.plate_number.plate_number)

        # Get all vehicles that are not in the list of unavailable vehicles
        available_vehicles = Vehicle.objects.exclude(plate_number__in=unavailable_vehicles)

        # Serialize the available vehicles
        data = serializers.serialize('json', available_vehicles)

        return JsonResponse(data, safe=False)





    


