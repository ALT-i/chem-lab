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


class MoodleConfigSecurityTests(TestCase):
    """Regression tests for the security review findings on this feature."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_instructor(
            email='admin@example.com', password='p', role=User.Roles.ADMIN
        )
        self.instructor = User.objects.create_instructor(
            email='teacher@example.com', password='p', role=User.Roles.INSTRUCTOR
        )
        c = MoodleConfiguration.load()
        c.base_url, c.token = 'https://real.moodlecloud.com', 'REAL-SECRET-TOKEN'
        c.save()

    def test_instructors_cannot_change_institution_wide_settings(self):
        """Repointing the whole institution's Moodle is an admin action."""
        self.client.force_authenticate(user=self.instructor)
        self.assertIn(self.client.get('/api/v1/moodle/config/').status_code, (401, 403))
        res = self.client.put(
            '/api/v1/moodle/config/', {'base_url': 'https://evil.example.com'}, format='json'
        )
        self.assertIn(res.status_code, (401, 403))
        self.assertEqual(MoodleConfiguration.load().base_url, 'https://real.moodlecloud.com')

    def test_cannot_send_stored_token_to_an_attacker_supplied_host(self):
        """base_url without a token must be refused, not paired with the stored one."""
        self.client.force_authenticate(user=self.admin)
        with mock.patch('src.common.moodle_client.requests.post') as posted:
            res = self.client.post(
                '/api/v1/moodle/config/test/',
                {'base_url': 'https://attacker.example.com'},
                format='json',
            )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'token_required')
        posted.assert_not_called()  # the real token never left the server

    def test_internal_addresses_are_rejected_on_test(self):
        self.client.force_authenticate(user=self.admin)
        for host in ('http://localhost:8000', 'https://127.0.0.1', 'https://169.254.169.254'):
            with mock.patch('src.common.moodle_client.requests.post') as posted:
                res = self.client.post(
                    '/api/v1/moodle/config/test/',
                    {'base_url': host, 'token': 'whatever'},
                    format='json',
                )
            self.assertEqual(res.status_code, 400, host)
            posted.assert_not_called()

    def test_internal_addresses_are_rejected_on_save(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.put(
            '/api/v1/moodle/config/', {'base_url': 'https://127.0.0.1'}, format='json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(MoodleConfiguration.load().base_url, 'https://real.moodlecloud.com')


class MoodleGradeSubmissionAuthorizationTests(TestCase):
    """A student must not be able to push a grade for anyone else."""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            email='me@example.com', password='p', role=User.Roles.STUDENT
        )
        self.classmate = User.objects.create_user(
            email='someone.else@example.com', password='p', role=User.Roles.STUDENT
        )
        c = MoodleConfiguration.load()
        c.base_url, c.token, c.course_id = 'https://real.moodlecloud.com', 'tok', 9
        c.save()
        self.client.force_authenticate(user=self.student)

    def test_student_cannot_grade_a_classmate(self):
        with mock.patch('src.common.moodle_client.requests.post') as posted:
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2,
                 'grades': [{'email': 'someone.else@example.com', 'grade': 0}]},
                format='json',
            )
        self.assertEqual(res.status_code, 403, res.data)
        posted.assert_not_called()

    def test_student_cannot_bulk_grade_the_cohort(self):
        with mock.patch('src.common.moodle_client.requests.post') as posted:
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2, 'grades': [
                    {'email': 'me@example.com', 'grade': 100},
                    {'email': 'someone.else@example.com', 'grade': 0},
                ]},
                format='json',
            )
        self.assertEqual(res.status_code, 403)
        posted.assert_not_called()

    def test_student_grade_is_computed_server_side_not_asserted(self):
        """A client-supplied grade must be ignored entirely."""
        from src.workspace.models import Lesson, LessonSession

        instructor = User.objects.create_instructor(
            email='teach2@example.com', password='p', role=User.Roles.INSTRUCTOR
        )
        lesson = Lesson.objects.create(title='T', description='d', instructor=instructor)
        session = LessonSession.objects.create(
            lesson=lesson, student=self.student,
            measurements={'readings': [
                # deliberately a poor measurement: 30 where 25 was wanted
                {'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 30.0,
                 'precision': 0.05, 'tolerance': 0.2}
            ]},
        )
        captured = {}

        def fake_post(url, data=None, **kwargs):
            captured.setdefault('calls', []).append(data)
            resp = mock.Mock(status_code=200, is_redirect=False)
            if data.get('wsfunction') == 'core_enrol_get_enrolled_users':
                resp.json.return_value = [{'id': 5, 'email': 'me@example.com'}]
            else:
                resp.json.return_value = {}
            return resp

        with mock.patch('src.common.moodle_client.requests.post', side_effect=fake_post):
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2, 'grades': [
                    {'email': 'me@example.com', 'grade': 100, 'session_id': str(session.id)}
                ]},
                format='json',
            )
        self.assertEqual(res.status_code, 200, res.data)
        graded = [c for c in captured['calls'] if c.get('wsfunction') == 'mod_assign_save_grade']
        self.assertEqual(len(graded), 1)
        # The claimed 100 must not have been used.
        self.assertLess(float(graded[0]['grade']), 100.0)

    def test_student_without_a_session_cannot_submit(self):
        with mock.patch('src.common.moodle_client.requests.post') as posted:
            posted.return_value = mock.Mock(status_code=200, is_redirect=False)
            posted.return_value.json.return_value = [{'id': 5, 'email': 'me@example.com'}]
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2, 'grades': [{'email': 'me@example.com', 'grade': 100}]},
                format='json',
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['results'][0]['code'], 'session_required')

    def test_student_cannot_grade_from_someone_elses_session(self):
        from src.workspace.models import Lesson, LessonSession

        instructor = User.objects.create_instructor(
            email='teach3@example.com', password='p', role=User.Roles.INSTRUCTOR
        )
        lesson = Lesson.objects.create(title='T', description='d', instructor=instructor)
        other_session = LessonSession.objects.create(
            lesson=lesson, student=self.classmate, measurements={'readings': []}
        )
        with mock.patch('src.common.moodle_client.requests.post') as posted:
            posted.return_value = mock.Mock(status_code=200, is_redirect=False)
            posted.return_value.json.return_value = [{'id': 5, 'email': 'me@example.com'}]
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2, 'grades': [
                    {'email': 'me@example.com', 'session_id': str(other_session.id)}
                ]},
                format='json',
            )
        self.assertEqual(res.data['results'][0]['code'], 'session_required')

    def test_untouched_session_does_not_score_full_marks(self):
        """calculate_session_grade returns 100 for no records; don't ship that."""
        from src.workspace.models import Lesson, LessonSession

        instructor = User.objects.create_instructor(
            email='teach4@example.com', password='p', role=User.Roles.INSTRUCTOR
        )
        lesson = Lesson.objects.create(
            title='T', description='d', instructor=instructor,
            procedure={'steps': [{'description': 'one'}, {'description': 'two'}]},
        )
        empty = LessonSession.objects.create(
            lesson=lesson, student=self.student, measurements={'readings': []}
        )
        with mock.patch('src.common.moodle_client.requests.post') as posted:
            posted.return_value = mock.Mock(status_code=200, is_redirect=False)
            posted.return_value.json.return_value = [{'id': 5, 'email': 'me@example.com'}]
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2, 'grades': [
                    {'email': 'me@example.com', 'session_id': str(empty.id)}
                ]},
                format='json',
            )
        self.assertEqual(res.data['results'][0]['code'], 'session_incomplete')
        graded = [c for c in [kw.get('data') or (a[1] if len(a) > 1 else {})
                              for a, kw in posted.call_args_list]
                  if isinstance(c, dict) and c.get('wsfunction') == 'mod_assign_save_grade']
        self.assertEqual(graded, [])

    def test_partially_completed_session_is_rejected(self):
        from src.workspace.models import Lesson, LessonSession

        instructor = User.objects.create_instructor(
            email='teach5@example.com', password='p', role=User.Roles.INSTRUCTOR
        )
        lesson = Lesson.objects.create(
            title='T', description='d', instructor=instructor,
            procedure={'steps': [{'description': 'one'}, {'description': 'two'}]},
        )
        half = LessonSession.objects.create(
            lesson=lesson, student=self.student,
            measurements={'readings': [
                {'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 25.0,
                 'precision': 0.05, 'tolerance': 0.2}
            ]},
        )
        with mock.patch('src.common.moodle_client.requests.post') as posted:
            posted.return_value = mock.Mock(status_code=200, is_redirect=False)
            posted.return_value.json.return_value = [{'id': 5, 'email': 'me@example.com'}]
            res = self.client.post(
                '/api/v1/moodle/grades/assignment/',
                {'assignment_id': 2, 'grades': [
                    {'email': 'me@example.com', 'session_id': str(half.id)}
                ]},
                format='json',
            )
        self.assertEqual(res.data['results'][0]['code'], 'session_incomplete')
        self.assertEqual(res.data['results'][0]['steps_required'], 2)


class MoodleTokenRebindingTests(TestCase):
    """The stored token must never follow the site address to a new host."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_instructor(
            email='admin2@example.com', password='p', role=User.Roles.ADMIN
        )
        self.client.force_authenticate(user=self.admin)

    def test_token_from_settings_still_forces_a_new_token_on_url_change(self):
        """The row may be blank while settings supply the credential."""
        MoodleConfiguration.load()
        with mock.patch('src.common.moodle_client.MOODLE_BASE_URL', 'https://old.moodlecloud.com'), \
             mock.patch('src.common.moodle_client.MOODLE_TOKEN', 'ENV-TOKEN'):
            res = self.client.put(
                '/api/v1/moodle/config/',
                {'base_url': 'https://attacker.example.com'},
                format='json',
            )
        self.assertEqual(res.status_code, 400)
        self.assertIn('token', res.data['errors'])

    def test_clearing_the_address_also_clears_the_token(self):
        c = MoodleConfiguration.load()
        c.base_url, c.token = 'https://old.moodlecloud.com', 'STORED'
        c.save()
        res = self.client.put('/api/v1/moodle/config/', {'base_url': ''}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(MoodleConfiguration.load().token, '')
