from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('request/', include('request.urls')),
    path('vehicle/', include('vehicle.urls')),
]
