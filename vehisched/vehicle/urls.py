from django.urls import path
from . import views


urlpatterns = [
    path('fetch/', views.VehicleListCreateView.as_view(),
         name='vehicle-list-create'),
    path('update/<int:pk>/', views.VehicleRetrieveUpdateDestroyView.as_view(),
         name='vehicle-retrieve-update-destroy'),

]
