from rest_framework import generics
from .models import Vehicle
from .serializers import VehicleSerializer
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser


class VehicleListCreateView(generics.ListCreateAPIView):
    # Requires token authentication
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def create(self, request, *args, **kwargs):
        # Deserialize the request data using the serializer
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Save the vehicle object
            self.perform_create(serializer)

            # Handle image upload here
            # Replace with your actual field name
            image_file = request.FILES.get('vehicle_image')
            if image_file:
                # Do something with the image, e.g., save it to the vehicle object
                serializer.instance.vehicle_image = image_file
                serializer.instance.save()

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = (MultiPartParser, FormParser)  # Allow file uploads

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()  # Get the instance to update
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)

        if serializer.is_valid():
            # Check if a new image was provided in the request
            new_image = request.FILES.get('vehicle_image')
            print("imnagege: ", new_image)
            if new_image:
                # Delete the old image file (optional)
                if instance.vehicle_image:
                    instance.vehicle_image.delete()

                # Update the vehicle's image field with the new image
                instance.vehicle_image = new_image

            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
