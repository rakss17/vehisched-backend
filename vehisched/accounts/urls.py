from django.contrib import admin
from django.urls import path, include
from .views import activate_account, UserListView, user_type

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('activation/<uidb64>/<token>/',
         activate_account, name='activate_account'),
    path('admin/', UserListView.as_view(), name='user-list'),
    path('user_type/', user_type),
]
