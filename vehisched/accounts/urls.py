from django.contrib import admin
from django.urls import path, include
from .views import activate_account, UserListView, UserUpdateView, RoleByNameView, UserProfileView

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('activation/<uidb64>/<token>/',
         activate_account, name='activate_account'),
    path('admin/', UserListView.as_view(), name='user-list'),
    path('update/<int:pk>/', UserUpdateView.as_view(), name='user-update'),
    path('roles/by-name/', RoleByNameView.as_view(), name='role-by-name'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
]
