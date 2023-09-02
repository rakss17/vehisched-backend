from rest_framework import generics
from .models import Request
from .serializers import RequestSerializer


class RequestListCreateView(generics.ListCreateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer


class RequestRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
