from django.contrib import admin
from .models import TripTicket, FuelStatus, Speedometer, TripTicket_Status

admin.site.register(TripTicket)
admin.site.register(FuelStatus)
admin.site.register(Speedometer)
admin.site.register(TripTicket_Status)

