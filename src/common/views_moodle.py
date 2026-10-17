from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from src.common.models import MoodleConfiguration
from src.common.moodle_client import MoodleClient, MoodleError, MoodleNotConfigured
from src.common.serializers_moodle import MoodleConfigurationSerializer
from src.common.url_safety import UnsafeUrl, validate_outbound_url
from src.users.permissions import IsAdminOrSuper


class MoodleConfigurationView(APIView):
    """Let the institution point the lab at their own Moodle site.

    GET  - current settings (never returns the token itself)
    PUT  - update settings; a blank token keeps the stored one
    """

    permission_classes = [IsAuthenticated, IsAdminOrSuper]

    def get(self, request, *args, **kwargs):
        config = MoodleConfiguration.load()
        return Response(
            {'message': 'Moodle configuration retrieved', 'data': MoodleConfigurationSerializer(config).data},
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        config = MoodleConfiguration.load()
        serializer = MoodleConfigurationSerializer(config, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'message': 'Invalid Moodle configuration', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(updated_by=request.user)
        return Response(
            {'message': 'Moodle configuration saved', 'data': MoodleConfigurationSerializer(config).data},
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)


class MoodleConnectionTestView(APIView):
    """Verify the stored (or supplied) credentials against the Moodle site.

    Without this an administrator only finds out a token is wrong when a
    student's grade submission fails, so the result is recorded on the
    configuration row for later reference.
    """

    permission_classes = [IsAuthenticated, IsAdminOrSuper]

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        # Allow testing values before committing them.
        base_url = (data.get('base_url') or '').strip().rstrip('/') or None
        token = (data.get('token') or '').strip() or None

        # A caller-supplied address must come with its own token. Otherwise
        # MoodleClient would fall back to the STORED token and post it to
        # whatever host was named -- handing the real credential to an
        # arbitrary server.
        if base_url is not None and token is None:
            return Response(
                {
                    'ok': False,
                    'code': 'token_required',
                    'detail': 'To test a different site address you must also supply its token.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if base_url is not None:
            try:
                base_url = validate_outbound_url(base_url)
            except UnsafeUrl as exc:
                return Response(
                    {'ok': False, 'code': 'unsafe_url', 'detail': str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        config = MoodleConfiguration.load()
        try:
            client = MoodleClient(base_url=base_url, token=token)
            info = client.check_connection()
        except MoodleNotConfigured as exc:
            return Response(
                {'ok': False, 'code': 'moodle_not_configured', 'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except MoodleError as exc:
            detail = str(exc)
            # Only record failures against the stored config, not ad-hoc tests.
            if base_url is None and token is None:
                config.last_verification_error = detail
                config.save(update_fields=['last_verification_error', 'updated_at'])
            return Response(
                {'ok': False, 'code': 'moodle_unavailable', 'detail': detail},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if base_url is None and token is None:
            config.last_verified_at = timezone.now()
            config.last_verification_error = ''
            config.save(update_fields=['last_verified_at', 'last_verification_error', 'updated_at'])

        return Response(
            {
                'ok': True,
                'detail': 'Connected to Moodle successfully.',
                'site': {
                    'sitename': info.get('sitename'),
                    'username': info.get('username'),
                    'release': info.get('release'),
                    'siteurl': info.get('siteurl'),
                },
            },
            status=status.HTTP_200_OK,
        )
