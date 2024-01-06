from rest_framework import generics
from .models import Vehicle
from .serializers import VehicleSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied


class VehicleListCreateView(generics.ListCreateAPIView):

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():

            self.perform_create(serializer)

            image_file = request.FILES.get('vehicle_image')
            if image_file:

                serializer.instance.vehicle_image = image_file
                serializer.instance.save()

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)

        if serializer.is_valid():

            new_image = request.FILES.get('image', None)
        
            if new_image:

                if instance.image:
                    instance.image.delete()

                instance.image = new_image

            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VehicleForVIPListView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        print(user)
        role = self.request.GET.get('role')
        if not role == 'vip':
            raise PermissionDenied("Only VIP users can access this view.")
        return Vehicle.objects.filter(assigned_to=user)