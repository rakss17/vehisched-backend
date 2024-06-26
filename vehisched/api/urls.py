from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('request/', include('request.urls')),
    path('vehicles/', include('vehicle.urls')),
    path('trip/', include('trip.urls')),
    path('notification/', include('notification.urls'))
]
