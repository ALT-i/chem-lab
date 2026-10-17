from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from src.common.models import MoodleConfiguration
from src.common.moodle_client import MoodleClient, MoodleError, MoodleNotConfigured, get_moodle_settings
from src.users.models import User


class MoodleConfigurationModelTests(TestCase):
    def test_load_is_a_singleton(self):
        a = MoodleConfiguration.load()
        b = MoodleConfiguration.load()
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(MoodleConfiguration.objects.count(), 1)

    def test_saving_a_second_row_overwrites_the_singleton(self):
        MoodleConfiguration.load()
        other = MoodleConfiguration(base_url='https://x.example.com', token='t')
        other.save()
        self.assertEqual(MoodleConfiguration.objects.count(), 1)

    def test_trailing_slash_is_stripped(self):
        c = MoodleConfiguration.load()
        c.base_url = 'https://moodle.example.com/'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.base_url, 'https://moodle.example.com')

    def test_is_configured_requires_url_token_and_active(self):
        c = MoodleConfiguration.load()
        self.assertFalse(c.is_configured)
        c.base_url, c.token = 'https://moodle.example.com', 'tok'
        c.save()
        self.assertTrue(c.is_configured)
        c.is_active = False
        c.save()
        self.assertFalse(c.is_configured)


class MoodleSettingsResolutionTests(TestCase):
    def test_database_configuration_takes_precedence(self):
        c = MoodleConfiguration.load()
        c.base_url, c.token, c.course_id = 'https://noun.example.com', 'dbtok', 42
        c.save()
        resolved = get_moodle_settings()
        self.assertEqual(resolved['base_url'], 'https://noun.example.com')
        self.assertEqual(resolved['token'], 'dbtok')
        self.assertEqual(resolved['course_id'], 42)

    def test_client_raises_not_configured_when_blank(self):
        MoodleConfiguration.load()  # exists but empty
        with mock.patch('src.common.moodle_client.MOODLE_BASE_URL', ''), \
             mock.patch('src.common.moodle_client.MOODLE_TOKEN', ''):
            with self.assertRaises(MoodleNotConfigured):
                MoodleClient()

    def test_inactive_configuration_disables_integration(self):
        c = MoodleConfiguration.load()
        c.base_url, c.token, c.is_active = 'https://noun.example.com', 'tok', False
        c.save()
        with mock.patch('src.common.moodle_client.MOODLE_BASE_URL', ''), \
             mock.patch('src.common.moodle_client.MOODLE_TOKEN', ''):
            with self.assertRaises(MoodleNotConfigured):
                MoodleClient()

    def test_decommissioned_site_reports_clearly(self):
        """A dead MoodleCloud site redirects to an HTML 'not found' page."""
        c = MoodleConfiguration.load()
        c.base_url, c.token = 'https://gone.moodlecloud.com', 'tok'
        c.save()
        fake = mock.Mock(status_code=200)
        fake.json.side_effect = ValueError('not json')
        with mock.patch('src.common.moodle_client.requests.post', return_value=fake):
            with self.assertRaises(MoodleError) as ctx:
                MoodleClient().check_connection()
        self.assertIn('did not return a valid API response', str(ctx.exception))


class MoodleConfigurationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_instructor(
            email='admin@example.com', password='p', role=User.Roles.ADMIN
        )
        self.student = User.objects.create_user(
            email='student@example.com', password='p', role=User.Roles.STUDENT
        )

    def test_students_cannot_read_or_change_configuration(self):
        self.client.force_authenticate(user=self.student)
        self.assertIn(self.client.get('/api/v1/moodle/config/').status_code, (401, 403))
        self.assertIn(
            self.client.put('/api/v1/moodle/config/', {'base_url': 'https://x.example.com'}, format='json').status_code,
            (401, 403),
        )

    def test_anonymous_cannot_read_configuration(self):
        self.assertIn(self.client.get('/api/v1/moodle/config/').status_code, (401, 403))

    def test_admin_can_save_and_token_is_never_returned(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.put(
            '/api/v1/moodle/config/',
            {'base_url': 'https://noun.moodlecloud.com', 'token': 'secret-token', 'course_id': 7},
            format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertNotIn('token', res.data['data'])
        self.assertTrue(res.data['data']['token_set'])
        self.assertEqual(MoodleConfiguration.load().token, 'secret-token')

    def test_blank_token_preserves_the_stored_one(self):
        self.client.force_authenticate(user=self.admin)
        self.client.put(
            '/api/v1/moodle/config/',
            {'base_url': 'https://noun.moodlecloud.com', 'token': 'keep-me'},
            format='json',
        )
        self.client.put('/api/v1/moodle/config/', {'course_id': 9, 'token': ''}, format='json')
        self.assertEqual(MoodleConfiguration.load().token, 'keep-me')

    def test_webservice_path_is_rejected_with_guidance(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.put(
            '/api/v1/moodle/config/',
            {'base_url': 'https://noun.moodlecloud.com/webservice/rest/server.php'},
            format='json',
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn('base_url', res.data['errors'])

    def test_missing_scheme_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.put('/api/v1/moodle/config/', {'base_url': 'noun.moodlecloud.com'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_connection_test_records_success(self):
        self.client.force_authenticate(user=self.admin)
        self.client.put(
            '/api/v1/moodle/config/',
            {'base_url': 'https://noun.moodlecloud.com', 'token': 'tok'},
            format='json',
        )
        fake = mock.Mock(status_code=200)
        fake.json.return_value = {'sitename': 'NOUN', 'username': 'svc', 'release': '4.3'}
        with mock.patch('src.common.moodle_client.requests.post', return_value=fake):
            res = self.client.post('/api/v1/moodle/config/test/', {}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(res.data['ok'])
        self.assertEqual(res.data['site']['sitename'], 'NOUN')
        self.assertIsNotNone(MoodleConfiguration.load().last_verified_at)

    def test_connection_test_records_failure(self):
        self.client.force_authenticate(user=self.admin)
        self.client.put(
            '/api/v1/moodle/config/',
            {'base_url': 'https://noun.moodlecloud.com', 'token': 'bad'},
            format='json',
        )
        fake = mock.Mock(status_code=403)
        with mock.patch('src.common.moodle_client.requests.post', return_value=fake):
            res = self.client.post('/api/v1/moodle/config/test/', {}, format='json')
        self.assertEqual(res.status_code, 502)
        self.assertFalse(res.data['ok'])
        self.assertTrue(MoodleConfiguration.load().last_verification_error)

    def test_connection_test_without_configuration_is_503(self):
        self.client.force_authenticate(user=self.admin)
        MoodleConfiguration.load()
        with mock.patch('src.common.moodle_client.MOODLE_BASE_URL', ''), \
             mock.patch('src.common.moodle_client.MOODLE_TOKEN', ''):
            res = self.client.post('/api/v1/moodle/config/test/', {}, format='json')
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data['code'], 'moodle_not_configured')


class MoodleEndpointDegradationTests(TestCase):
    """The lab must say what is wrong, not return an opaque 500."""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            email='student@example.com', password='p', role=User.Roles.STUDENT
        )
        self.client.force_authenticate(user=self.student)
        MoodleConfiguration.load()

    def test_profile_lookup_reports_not_configured(self):
        with mock.patch('src.common.moodle_client.MOODLE_BASE_URL', ''), \
             mock.patch('src.common.moodle_client.MOODLE_TOKEN', ''):
            res = self.client.get('/api/v1/moodle/user/profile/?email=a@b.com')
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data['code'], 'moodle_not_configured')

    def test_grade_submission_reports_not_configured(self):
        with mock.patch('src.common.moodle_client.MOODLE_BASE_URL', ''), \
             mock.patch('src.common.moodle_client.MOODLE_TOKEN', ''):
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2, 'grades': [{'email': 'a@b.com', 'grade': 100}]},
                format='json',
            )
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data['code'], 'moodle_not_configured')

    def test_unreachable_site_is_502_not_500(self):
        c = MoodleConfiguration.load()
        c.base_url, c.token = 'https://gone.moodlecloud.com', 'tok'
        c.save()
        import requests as _requests

        with mock.patch(
            'src.common.moodle_client.requests.post',
            side_effect=_requests.RequestException('connection refused'),
        ):
            res = self.client.get('/api/v1/moodle/user/profile/?email=a@b.com')
        self.assertEqual(res.status_code, 502)
        self.assertEqual(res.data['code'], 'moodle_unavailable')
