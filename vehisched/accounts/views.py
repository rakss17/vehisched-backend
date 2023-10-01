from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import generics, permissions, status
from .models import User, Role, Driver_Status
from .serializers import UserSerializer, FetchedUserSerializer, UserUpdateSerializer, RoleByNameSerializer, DriverSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

User = get_user_model()


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        activation_link = f"{settings.BASE_URL}/activation/{uidb64}/{token}/"

        temporary_password = f"{user.last_name.lower()}@{user.first_name.lower()}"
        temporary_password = temporary_password.replace(" ", "") 
        user.set_password(temporary_password)
        user.save()

        subject = 'Your account has been activated'
        message = f'Your account has been activated.\nUsername: {user.username}\nEmail: {user.email}\nPassword: {temporary_password}\nYou can now log in at {settings.BASE_URL}.'

        from_email = settings.EMAIL_HOST_USER
        to_email = user.email

        send_mail(subject, message, from_email, [to_email])
        messages.success(request, 'Your account has been activated.')
        return redirect('http://localhost:5173/#/AccountActivated')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return redirect('http://localhost:5173/#/NotFound')


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FetchedUserSerializer

    def get_object(self):
        return self.request.user


class CustomPagination(PageNumberPagination):
    page_size = 10

    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.role.role_name == 'admin' or request.method in permissions.SAFE_METHODS)


class UserListView(generics.ListAPIView):
    serializer_class = FetchedUserSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        allowed_roles = ["requester", "office staff",
                         "driver", "gate guard", "vip"]
        queryset = User.objects.filter(role__role_name__in=allowed_roles)
        return queryset


class RoleByNameView(generics.RetrieveAPIView):
    serializer_class = RoleByNameSerializer

    def get_object(self):
        role_name = self.request.query_params.get('role_name')
        try:
            role = Role.objects.get(role_name=role_name)
            return role
        except Role.DoesNotExist:
            return Response({'message': f"Role with name '{role_name}' does not exist."}, status=404)


class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user_id = self.kwargs.get('pk')
        return self.queryset.get(pk=user_id)

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        role_name_serializer = RoleByNameSerializer(data=request.data)
        role_name_serializer.is_valid(raise_exception=True)
        role_name = role_name_serializer.validated_data.get('role_name')

        try:
            role_instance = Role.objects.get(role_name=role_name)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

        user.role = role_instance

        user_data_to_update = {
            'username': request.data.get('username', user.username),
            'email': request.data.get('email', user.email),
            'first_name': request.data.get('first_name', user.first_name),
            'middle_name': request.data.get('middle_name', user.middle_name),
            'last_name': request.data.get('last_name', user.last_name),
            'mobile_number': request.data.get('mobile_number', user.mobile_number),
        }

        user_serializer = UserUpdateSerializer(
            user, data=user_data_to_update, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return super().update(request, *args, **kwargs)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class DriverListView(generics.ListAPIView):
    queryset = Driver_Status.objects.all()
    serializer_class = DriverSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user_activation(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    
    user.save()
    
    return Response({'message': 'User activation status changed successfully.', 'is_active': user.is_active}, status=status.HTTP_200_OK)
