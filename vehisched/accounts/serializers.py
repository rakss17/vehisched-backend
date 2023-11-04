from rest_framework import serializers
from .models import User, Role, Office


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={"input_type": "password"}, write_only=True)
    mobile_number = serializers.IntegerField(write_only=True)
    office_id= serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [(role.role_name, role.role_name) for role in Role.objects.all()]

    class Meta:
        model = User
        fields = ['role', 'username', 'email', 'first_name', 'middle_name', 'last_name', 'password',
                  'mobile_number', 'office_id']

    def save(self, **kwargs):
        role_name = self.validated_data.get('role')
        office_name = self.validated_data.get('office_id')

        try:
            office = Office.objects.get(name=office_name)
        except Office.DoesNotExist:
            raise serializers.ValidationError("Invalid office_id")
        
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
                role=role,
                office_id=office 
            )

            user.is_active = False
            user.save()

            return user




class FetchedUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(
        source='role.role_name', read_only=True)
    office = serializers.SerializerMethodField()

    def get_office(self, obj):
        if obj.office_id:
            office_id = obj.office_id
            office = office_id.name
            return office
        return None

    class Meta:
        model = User
        fields = ['id', 'role', 'username', 'email',
                  'first_name', 'middle_name', 'last_name', 'mobile_number', 'is_active', 'office']

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
        
class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'
