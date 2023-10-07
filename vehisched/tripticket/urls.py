from django.urls import path
from . import views

urlpatterns = [
    
     path('fetch-requester/', views.ScheduleRequesterView.as_view(),
         name='schedule-requester'),
    path('fetch-office-staff/', views.ScheduleOfficeStaffView.as_view(),
    name='schedule-office-staff'),
   
]
