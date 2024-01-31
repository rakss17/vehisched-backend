from django.urls import path
from . import views

urlpatterns = [
    path('fetch-post/', views.VehicleListCreateView.as_view(),
         name='vehicle-list-create'),
    path('update-delete/<str:pk>/', views.VehicleRetrieveUpdateDestroyView.as_view(),
         name='vehicle-retrieve-update-destroy'),
     path('fetch-vehicle-vip/', views.VehicleForVIPListView.as_view(),
         name='fetch-vehicle-vip'),
    path('check-vehicle-on-process/', views.CheckVehicleOnProcess.as_view(), name='check-vehicle-on-process'),
    path('fetch-each-vehicle-schedule/', views.VehicleEachSchedule.as_view(), name='fetch-each-vehicle-schedule'),
    path('heartbeat-on-process-vehicle/<int:pk>/', views.HeartbeatView.as_view(), name='heartbeat-on-process-vehicle')
]
