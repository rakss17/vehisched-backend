from django.urls import path
from . import views

urlpatterns = [
    
     path('fetch-requester/', views.ScheduleRequesterView.as_view(),
         name='schedule-requester'),
    path('fetch-office-staff/', views.ScheduleOfficeStaffView.as_view(),
    name='schedule-office-staff'),
    path('check-vehicle-availability/', views.CheckVehicleAvailability.as_view(),
    name='check-vehicle-availability'),
    path('check-driver-availability/', views.CheckDriverAvailability.as_view(),
    name='check-driver-availability'),  
]
