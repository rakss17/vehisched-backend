from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer, FetchedUserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import permissions
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

        temporary_password = User.objects.make_random_password()
        user.set_password(temporary_password)
        user.save()

        subject = 'Your account has been activated'
        message = f'Your account has been activated.\nUsername: {user.username}\nEmail: {user.email}\nPassword: {temporary_password}\nYou can now log in at {settings.BASE_URL}.'

        from_email = settings.EMAIL_HOST_USER
        to_email = user.email

        send_mail(subject, message, from_email, [to_email])
        messages.success(request, 'Your account has been activated.')
        # return redirect('http://192.168.1.5:3000/Activated')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        # return redirect('http://192.168.1.5:3000/Signup')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_type(request):
    user_profile = request.user
    if user_profile.role:
        role_name = user_profile.role.role_name
        if role_name == 'admin':
            user_type = "admin"
        elif role_name == 'requester':
            user_type = "requester"
        elif role_name == 'vip':
            user_type = "vip"
        elif role_name == 'driver':
            user_type = "driver"
        elif role_name == 'gate guard':
            user_type = "gate guard"
        elif role_name == 'office staff':
            user_type = "office staff"
        else:
            user_type = "unknown"
    else:
        user_type = "unknown"

    return Response({'user_type': user_type})


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
