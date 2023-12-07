from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import generics, permissions, status
from .models import User, Role, Office
from .serializers import FetchedUserSerializer, UserUpdateSerializer, RoleByNameSerializer, OfficeSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


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


class UserListView(generics.ListAPIView):
    serializer_class = FetchedUserSerializer
    

    def get_queryset(self):
        allowed_roles = ["requester", "office staff",
                         "driver", "gate guard", "vip"]
        queryset = User.objects.filter(role__role_name__in=allowed_roles)
        return queryset
    
class FetchVIPUserView(generics.ListAPIView):
    serializer_class = FetchedUserSerializer
    

    def get_queryset(self):
        allowed_roles = ["vip"]
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
        office_name = request.data.get('office', user.office)
        office = Office.objects.get(name=office_name)
      
        user_data_to_update = {
            'username': request.data.get('username', user.username),
            'email': request.data.get('email', user.email),
            'first_name': request.data.get('first_name', user.first_name),
            'middle_name': request.data.get('middle_name', user.middle_name),
            'last_name': request.data.get('last_name', user.last_name),
            'mobile_number': request.data.get('mobile_number', user.mobile_number),
            'office': office
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
    serializer_class = FetchedUserSerializer

    def get_queryset(self):
        driver_role = Role.objects.get(role_name='driver')
        queryset = User.objects.filter(role=driver_role)
        return queryset
    
class RequesterListView(generics.ListAPIView):
    serializer_class = FetchedUserSerializer

    def get_queryset(self):
        requester_role = Role.objects.get(role_name='requester')
        queryset = User.objects.filter(role=requester_role)
        return queryset
    

class OfficeListCreateView(generics.ListCreateAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        capitalized_name = name.upper() 

       
        if Office.objects.filter(name=capitalized_name).exists():
            error_message = "This office is already exists."
            return Response({'error': error_message}, status=400)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['name'] = capitalized_name 
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
