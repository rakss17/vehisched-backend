from rest_framework import serializers
from .models import User, Role


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        style={"input_type": "password"}, write_only=True)
    mobile_number = serializers.IntegerField(write_only=True)

    role = serializers.ChoiceField(choices=[])
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [(role.role_name, role.role_name) for role in Role.objects.all()]

    class Meta:
        model = User
        fields = ['role', 'username', 'email', 'first_name', 'middle_name', 'last_name', 'password',
                  'mobile_number']
                  

    def save(self, **kwargs):

        role_name = self.validated_data.get('role')  
        if role_name:
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

            # if role_name == 'driver':
            #     driver = Driver_Status.objects.create(user=user, status='Available')

            return user


class FetchedUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(
        source='role.role_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'role', 'username', 'email',
                  'first_name', 'middle_name', 'last_name', 'mobile_number', 'is_active']
# class UserDriverSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email', 'mobile_number', 'middle_name', 'first_name', 'middle_name', 'last_name',)
        
# class DriverSerializer(serializers.ModelSerializer):
#     user = UserDriverSerializer()  

#     class Meta:
#         model = Driver_Status
#         fields = ('user', 'status')

class RoleByNameSerializer(serializers.Serializer):
    role_name = serializers.CharField()


class UserUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=[])
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [(role.role_name, role.role_name) for role in Role.objects.all()]

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'middle_name', 'last_name', 'mobile_number', 'role']
