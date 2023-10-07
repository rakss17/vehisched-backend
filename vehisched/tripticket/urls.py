from django.urls import path
from . import views

urlpatterns = [
    
     path('fetch/', views.ScheduleRequesterView.as_view(),
         name='schedule-list'),
   
]
