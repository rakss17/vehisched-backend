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
     path('vehicle-schedules/', views.VehicleSchedulesView.as_view(),
     name='vehicle-schedules'),  
     path('driver-schedules/', views.DriverSchedulesView.as_view(),
     name='driver-schedules'),  
     path('accept-vehicle/<int:pk>/', views.VehicleRecommendationAcceptance.as_view(),
          name='accept-vehicle'),
     path('trip-scanned/<int:pk>/', views.TripScannedView.as_view(), name='trip-scanned'),
     path('on-trips-gateguard/', views.OnTripsGateGuardView.as_view(), name='on-trips-gateguard'), 
     path('recent-trips-gateguard/', views.RecentLogsGateGuardView.as_view(), name='recent-trips-gateguard'),   
     path('download-tripticket/<int:request_id>/', views.download_tripticket, name='download_tripticket'),
]
