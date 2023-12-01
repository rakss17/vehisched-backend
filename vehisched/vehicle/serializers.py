from rest_framework import serializers
from .models import Vehicle
from accounts.models import User


class VehicleSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), allow_null=True)

    class Meta:
        model = Vehicle
        fields = '__all__'
