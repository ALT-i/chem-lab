from rest_framework import serializers

from src.common.models import MoodleConfiguration
from src.common.url_safety import UnsafeUrl, validate_outbound_url


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
        # The stored token is sent to this host, so it must not be internal.
        try:
            value = validate_outbound_url(value)
        except UnsafeUrl as exc:
            raise serializers.ValidationError(str(exc))
        return value

    def validate(self, attrs):
        # Keeping the old token while repointing at a different site would
        # send the existing credential to the new host. Compare against the
        # EFFECTIVE url -- the one the stored token is actually used with,
        # which may come from settings rather than this row.
        from src.common import moodle_client

        if 'base_url' not in attrs:
            return attrs

        new_url = (attrs.get('base_url') or '').rstrip('/')
        # Read the stored and environment values directly rather than through
        # get_moodle_settings(): that blanks everything when is_active is off,
        # which would let an admin disable the integration, repoint base_url
        # with no token, then re-enable it with the old credential attached to
        # the new host.
        instance = self.instance
        stored_token = getattr(instance, 'token', '') or ''
        stored_url = (getattr(instance, 'base_url', '') or '').rstrip('/')
        env_token = moodle_client.MOODLE_TOKEN or ''
        env_url = (moodle_client.MOODLE_BASE_URL or '').rstrip('/')

        effective_url = stored_url or env_url
        has_token = bool(stored_token or env_token)

        if has_token and new_url != effective_url and not attrs.get('token'):
            if not new_url:
                # Clearing the address: drop the credential with it rather
                # than leaving a token that would pair with a settings URL.
                self._force_clear_token = True
                return attrs
            raise serializers.ValidationError({
                'token': 'Enter the web service token for the new site. '
                         'The existing token belongs to the previous site and will not be reused.'
            })
        return attrs

    def update(self, instance, validated_data):
        if getattr(self, '_force_clear_token', False):
            # The site address was cleared, so the token must go with it.
            validated_data['token'] = ''
        elif not validated_data.get('token'):
            # A blank token otherwise means "leave the existing one alone".
            validated_data.pop('token', None)
        return super().update(instance, validated_data)
