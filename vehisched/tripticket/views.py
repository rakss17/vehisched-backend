from rest_framework import generics
from django.http import JsonResponse
from .models import TripTicket
from accounts.models import User
from request.models import Request
from django.core.exceptions import PermissionDenied

class ScheduleRequesterView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        trip_data = []
        trip_tickets = TripTicket.objects.filter(request_number__requester_name=request.user)

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
