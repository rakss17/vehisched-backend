from django.urls import path
from . import views

urlpatterns = [
    path('requests/', views.RequestListCreateView.as_view(),
         name='request-list-create'),
    path('requests/<int:pk>/', views.RequestRetrieveUpdateDestroyView.as_view(),
         name='request-retrieve-update-destroy'),
]
