from rest_framework import serializers
from .models import User, Role


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={"input_type": "password"}, write_only=True)
    confirm_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True)
    mobile_number = serializers.IntegerField(write_only=True)

    # Add a field for selecting the user's role
    role = serializers.ChoiceField(choices=Role.objects.all(
    ).values_list('role_name', flat=True), write_only=True)

    class Meta:
        model = User
        fields = ['role', 'username', 'email', 'first_name', 'middle_name', 'last_name', 'password',
                  'confirm_password', 'mobile_number']

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
            role=role  # Assign the role to the user
        )

        user.is_active = False
        user.save()

        return user
