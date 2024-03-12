from django.urls import path
from . import views

urlpatterns = [
    path('fetch-post/', views.RequestListCreateView.as_view(),
        name='request-list-create'),
    path('fetch/', views.RequestListOfficeStaffView.as_view(),
        name='request-list'),
    path('approve/<int:pk>/', views.RequestApprovedView.as_view(),
        name='request-approved'),
    path('reschedule/<int:pk>/', views.RequestReschedule.as_view(),
        name='request-reschedule'),
    path('cancel/<int:pk>/', views.RequestCancelView.as_view(),
        name='request-cancelled'),
    path('vehicle-maintenance/', views.VehicleMaintenance.as_view(), name='vehicle-maintenance'),
    path('driver-absence/', views.DriverAbsence.as_view(), name='driver-absence'),
    path('place-details/', views.get_place_details, name='place-details'),
    path('maintenance-absence-completed/<int:pk>/', views.MaintenanceAbsenceCompletedView.as_view(),
        name='maintenance-absence-completed'),
    path('reject-request/<int:pk>/', views.RejectRequestView.as_view(),
        name='reject-request'),
    path('change-request-driver/<int:pk>/', views.ChangeRequestDriverView.as_view(),
        name='change-request-driver'),
    # path('csm/<int:request_id>/', views.CSMListCreateView.as_view(), name='csm'),
    path('questions/', views.QuestionList.as_view(), name='question'),
    path('answer/', views.AnswerListCreateView.as_view(), name='answer'),
    path('submit-trip-merge/<int:pk>/', views.MergeTripView.as_view(),
        name='submit-trip-merge'),
]
