from rest_framework import serializers

from src.users.models import User
from src.common.serializers import ThumbnailerJSONSerializer


class UserSerializer(serializers.ModelSerializer):
    profile_picture = ThumbnailerJSONSerializer(required=False, allow_null=True, alias_target='src.users')

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'profile_picture',
            'progress'
        )
        read_only_fields = ('id',)


class CreateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    progress = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True)
    profile_picture = ThumbnailerJSONSerializer(required=False, allow_null=True, alias_target='src.users')
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, user):
        return user.get_tokens()

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'first_name',
            'last_name',
            'email',
            'tokens',
            'profile_picture',
            'progress'
        )
        read_only_fields = ('tokens',)
        extra_kwargs = {'password': {'write_only': True}}
