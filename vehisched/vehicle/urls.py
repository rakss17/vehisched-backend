from django.urls import path
from . import views

urlpatterns = [
    path('vehicles/', views.VehicleListCreateView.as_view(),
         name='vehicle-list-create'),
    path('vehicles/<int:pk>/', views.VehicleRetrieveUpdateDestroyView.as_view(),
         name='vehicle-retrieve-update-destroy'),
]
