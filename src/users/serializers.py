import datetime

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from src.users.models import User
from src.common.serializers import ThumbnailerJSONSerializer


class UserSerializer(serializers.ModelSerializer):
    image = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'image',
            'title',
            'level',
            'matric_number',
            'department',
            'office',
            'phone',
            'role',
            'progress',
            'is_active',
            'date_joined',
        )
        read_only_fields = ('id', 'role', 'email')
        
    def to_representation(self, instance):
        """Remove redundant info form user data"""
        ret = super().to_representation(instance)
        if ret['role'] == User.Roles.STUDENT:
            for items in ['office', 'title']:
                ret.pop(items)
        if ret['role'] == User.Roles.INSTRUCTOR: 
            for items in ['progress', 'level', 'department', 'matric_number']:
                ret.pop(items)
        if ret['role'] == User.Roles.ADMIN: 
            for items in ['office', 'progress', 'level', 'department', 'matric_number']:
                ret.pop(items)
                    
        return ret


class CreateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=User.Roles, default=User.Roles.STUDENT)
    progress = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, user):
        return user.get_tokens()

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        
        # Keep all email addresses unique by converting them to lower case
        validated_data['email'] = validated_data['email'].lower()  
        
        if validated_data['role'] == 'ADMIN':
            user = User.objects.create_superuser(**validated_data)
            return user
        elif validated_data['role'] == 'INSTRUCTOR':
            user = User.objects.create_instructor(**validated_data)
            return user
        else:
            user = User.objects.create_user(**validated_data)
            return user

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'first_name',
            'last_name',
            'title',
            'office',
            'level',
            'matric_number',
            'department',
            'phone',
            'email',
            'role',
            'tokens',
            'image',
            'progress'
        )
        read_only_fields = ('tokens', 'role', )
        extra_kwargs = {'password': {'write_only': True}}


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role

        return token
