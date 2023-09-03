from rest_framework import serializers
from .models import User, Role


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        style={"input_type": "password"}, write_only=True)
    mobile_number = serializers.IntegerField(write_only=True)

    # Add a field for selecting the user's role
    role = serializers.ChoiceField(choices=Role.objects.all(
    ).values_list('role_name', flat=True), write_only=True)

    class Meta:
        model = User
        fields = ['role', 'username', 'email', 'first_name', 'middle_name', 'last_name', 'password',
                  'mobile_number']

    def save(self, **kwargs):
        # Remove role from validated_data
        role_name = self.validated_data.pop('role')
        role = Role.objects.get(role_name=role_name)

        user = User.objects.create_user(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
            first_name=self.validated_data['first_name'],
            middle_name=self.validated_data['middle_name'],
            last_name=self.validated_data['last_name'],
            password=self.validated_data['password'],
            mobile_number=self.validated_data['mobile_number'],
            role=role
        )

        user.is_active = False
        user.save()

        return user


class FetchedUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(
        source='role.role_name', read_only=True)

    class Meta:
        model = User
        fields = ['role', 'username', 'email',
                  'first_name', 'middle_name', 'last_name', 'mobile_number']
