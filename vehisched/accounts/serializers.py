from rest_framework import serializers
from .models import User, Role, Office
from typing import Optional


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={"input_type": "password"}, write_only=True)
    mobile_number = serializers.IntegerField(write_only=True)
    office= serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [(role.role_name, role.role_name) for role in Role.objects.all()]

    class Meta:
        model = User
        fields = ['role', 'username', 'email', 'first_name', 'middle_name', 'last_name', 'password',
                  'mobile_number', 'office']

    def save(self, **kwargs):
        role_name = self.validated_data.get('role')
        office_name = self.validated_data.get('office')

        try:
            office = Office.objects.get(name=office_name)
        except Office.DoesNotExist:
            raise serializers.ValidationError("Invalid office")
        
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
                office=office 
            )

            user.is_active = False
            user.save()

            return user

class FetchedUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(
        source='role.role_name', read_only=True)
    office = serializers.SerializerMethodField()

    def get_office(self, obj)-> Optional[str]:
        if obj.office:
            office = obj.office
            office = office.name
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
    office = serializers.SlugRelatedField(slug_field='name', queryset=Office.objects.all())
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [(role.role_name, role.role_name) for role in Role.objects.all()]

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'middle_name', 'last_name', 'mobile_number', 'role', 'office']
        
class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'

class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['old_password', 'new_password']
