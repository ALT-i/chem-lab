from rest_framework import serializers

from src.common.models import MoodleConfiguration


class MoodleConfigurationSerializer(serializers.ModelSerializer):
    """Read/write the institution's Moodle settings.

    The token is write-only: it is never echoed back. `token_set` tells the
    dashboard whether one is stored so it can show "configured" without
    exposing the secret. Submitting a blank token leaves the stored one
    unchanged, so saving the form without retyping it does not wipe it.
    """

    token = serializers.CharField(
        write_only=True, required=False, allow_blank=True, trim_whitespace=True
    )
    token_set = serializers.SerializerMethodField(read_only=True)
    is_configured = serializers.BooleanField(read_only=True)

    class Meta:
        model = MoodleConfiguration
        fields = [
            'base_url',
            'token',
            'token_set',
            'course_id',
            'default_assignment_id',
            'is_active',
            'is_configured',
            'last_verified_at',
            'last_verification_error',
            'updated_at',
        ]
        read_only_fields = ['last_verified_at', 'last_verification_error', 'updated_at']

    def get_token_set(self, obj):
        return bool(obj.token)

    def validate_base_url(self, value):
        value = (value or '').strip().rstrip('/')
        if not value:
            return value
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                "Enter the full site address including https://, e.g. https://your-site.moodlecloud.com"
            )
        if '/webservice' in value:
            raise serializers.ValidationError(
                "Enter only the site address, not the web service path. "
                "Use https://your-site.moodlecloud.com rather than .../webservice/rest/server.php"
            )
        return value

    def update(self, instance, validated_data):
        # A blank token means "leave the existing one alone".
        if not validated_data.get('token'):
            validated_data.pop('token', None)
        return super().update(instance, validated_data)
