from django.urls import path
from . import views

urlpatterns = [
    path('fetch-post/', views.VehicleListCreateView.as_view(),
         name='vehicle-list-create'),
    path('update-delete/<str:pk>/', views.VehicleRetrieveUpdateDestroyView.as_view(),
         name='vehicle-retrieve-update-destroy'),
     path('fetch-vehicle-vip/', views.VehicleForVIPListView.as_view(),
         name='fetch-vehicle-vip'),
]
