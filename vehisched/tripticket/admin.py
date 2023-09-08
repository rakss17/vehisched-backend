from django.contrib import admin
from .models import TripTicket, FuelStatus, Speedometer

admin.site.register(TripTicket)
admin.site.register(FuelStatus)
admin.site.register(Speedometer)
