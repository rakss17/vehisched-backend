from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('activation/<uidb64>/<token>/',
         views.activate_account, name='activate_account'),
    path('admin/', views.UserListView.as_view(), name='user-list'),
    path('update/<int:pk>/', views.UserUpdateView.as_view(), name='user-update'),
    path('roles/by-name/', views.RoleByNameView.as_view(), name='role-by-name'),
    path('user-profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('delete/<int:pk>/', views.UserDeleteView.as_view(), name='user-delete')
]
