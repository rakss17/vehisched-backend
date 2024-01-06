from rest_framework import serializers
from .models import Vehicle
from accounts.models import User


class NullableSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        if data is None:
            return None
        return super().to_internal_value(data)


class VehicleSerializer(serializers.ModelSerializer):
    vip_assigned_to = NullableSlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        allow_null=True
    )
    driver_assigned_to = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        allow_null=True
    )

    class Meta:
        model = Vehicle
        fields = '__all__'

    def update(self, instance, validated_data):
        if 'is_vip' in validated_data and not validated_data['is_vip']:
            validated_data['vip_assigned_to'] = None
        return super().update(instance, validated_data)

