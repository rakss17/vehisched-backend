from django.urls import path
from . import views

urlpatterns = [
    path('fetch-post/', views.RequestListCreateView.as_view(),
         name='request-list-create'),
     path('fetch/', views.RequestListOfficeStaffView.as_view(),
         name='request-list'),
    path('approve/<int:pk>/', views.RequestApprovedView.as_view(),
         name='request-approved'),
]
