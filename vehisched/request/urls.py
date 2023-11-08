from django.urls import path
from . import views

urlpatterns = [
     path('fetch-post/', views.RequestListCreateView.as_view(),
         name='request-list-create'),
     path('fetch/', views.RequestListOfficeStaffView.as_view(),
         name='request-list'),
     path('approve/<int:pk>/', views.RequestApprovedView.as_view(),
         name='request-approved'),
     path('cancel/<int:pk>/', views.RequestCancelView.as_view(),
         name='request-cancelled'),
     path('vehicle-maintenance/', views.VehicleMaintenance.as_view(), name='vehicle-maintenance'),
     path('place-details/', views.get_place_details, name='place-details'),
]
