import uuid
from django.test import TestCase
from rest_framework.test import APIClient

from src.users.models import User
from src.workspace.models import Lesson, LessonSession
from src.workspace.grading import calculate_session_grade, evaluate_measurement_step


class LessonSessionModelTests(TestCase):
    """Tier 3: Session & Measurement Persistence data model tests."""

    def setUp(self):
        self.instructor = User.objects.create_instructor(
            email='instructor@example.com', password='pass', role=User.Roles.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='student@example.com', password='pass', role=User.Roles.STUDENT
        )
        self.lesson = Lesson.objects.create(
            title='Acid-Base Titration',
            description='Titration of HCl with NaOH',
            instructor=self.instructor,
        )

    def test_lesson_session_creation_with_measurements(self):
        telemetry = {
            'steps': [
                {
                    'stepIndex': 0,
                    'targetVolume': 25.0,
                    'measuredVolume': 24.95,
                    'precision': 0.05,
                    'tolerance': 0.1,
                }
            ],
            'notes': 'Carefully reached the pale pink endpoint',
        }
        session = LessonSession.objects.create(
            lesson=self.lesson,
            student=self.student,
            measurements=telemetry,
        )
        self.assertIsNotNone(session.id)
        session.refresh_from_db()
        self.assertEqual(session.measurements['steps'][0]['measuredVolume'], 24.95)
        self.assertIn('Acid-Base Titration', str(session))

    def test_lesson_session_default_uuid(self):
        s1 = LessonSession.objects.create(lesson=self.lesson, student=self.student)
        s2 = LessonSession.objects.create(lesson=self.lesson, student=self.student)
        self.assertNotEqual(s1.id, s2.id)
        self.assertIsInstance(s1.id, uuid.UUID)

    def test_titration_experiment_model_removed(self):
        import src.workspace.models as models
        self.assertFalse(hasattr(models, 'TitrationExperiment'))


class LessonSessionAPITests(TestCase):
    """Tier 3: Session & Measurement Persistence REST API tests."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = User.objects.create_instructor(
            email='instructor@example.com', password='pass', role=User.Roles.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='student@example.com', password='pass', role=User.Roles.STUDENT
        )
        self.lesson = Lesson.objects.create(
            title='Volumetric Analysis',
            description='Standardization of HCl',
            instructor=self.instructor,
        )

    def test_create_and_retrieve_session_with_measurements(self):
        self.client.force_authenticate(user=self.student)
        payload = {
            'lesson': self.lesson.id,
            'student': self.student.id,
            'measurements': {
                'readings': [
                    {'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 25.0, 'precision': 0.05, 'tolerance': 0.2},
                    {'stepIndex': 1, 'targetVolume': 20.0, 'measuredVolume': 19.9, 'precision': 0.05, 'tolerance': 0.2},
                ]
            }
        }
        res = self.client.post('/api/v1/workspace/sessions/', payload, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        session_id = res.data['id']

        # Retrieve
        get_res = self.client.get(f'/api/v1/workspace/sessions/{session_id}/')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.data['lesson_title'], 'Volumetric Analysis')
        self.assertEqual(get_res.data['student_email'], 'student@example.com')
        self.assertIsNotNone(get_res.data['grade_evaluation'])
        self.assertGreaterEqual(get_res.data['grade_evaluation']['overall_grade'], 90.0)

    def test_evaluate_grade_endpoint(self):
        self.client.force_authenticate(user=self.student)
        session = LessonSession.objects.create(
            lesson=self.lesson,
            student=self.student,
            measurements={
                'measurements': [
                    {'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 24.8, 'precision': 0.05, 'tolerance': 0.5}
                ]
            }
        )
        res = self.client.get(f'/api/v1/workspace/sessions/{session.id}/evaluate-grade/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('evaluation', res.data)
        self.assertIn('overall_grade', res.data['evaluation'])

        # Update telemetry via POST to evaluate-grade
        update_res = self.client.post(
            f'/api/v1/workspace/sessions/{session.id}/evaluate-grade/',
            {
                'measurements': [
                    {'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 25.0, 'precision': 0.05, 'tolerance': 0.1}
                ]
            },
            format='json'
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.data['evaluation']['overall_grade'], 100.0)


class LessonSessionAccessControlTests(TestCase):
    """Regression tests for the session access-control fix.

    Before this fix LessonSessionViewSet declared no permission_classes and
    DEFAULT_PERMISSION_CLASSES is not set, so every one of these operations
    was possible unauthenticated.
    """

    def setUp(self):
        self.client = APIClient()
        self.instructor = User.objects.create_instructor(
            email='instructor@example.com', password='pass', role=User.Roles.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='owner@example.com', password='pass', role=User.Roles.STUDENT
        )
        self.other = User.objects.create_user(
            email='other@example.com', password='pass', role=User.Roles.STUDENT
        )
        self.lesson = Lesson.objects.create(
            title='Volumetric Analysis', description='x', instructor=self.instructor
        )
        self.session = LessonSession.objects.create(
            lesson=self.lesson,
            student=self.student,
            measurements={'measurements': [
                {'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 24.8,
                 'precision': 0.05, 'tolerance': 0.5}
            ]},
        )

    def test_anonymous_cannot_list_or_read_sessions(self):
        self.assertIn(self.client.get('/api/v1/workspace/sessions/').status_code, (401, 403))
        self.assertIn(
            self.client.get(f'/api/v1/workspace/sessions/{self.session.id}/').status_code,
            (401, 403),
        )

    def test_anonymous_cannot_overwrite_measurements_via_evaluate_grade(self):
        res = self.client.post(
            f'/api/v1/workspace/sessions/{self.session.id}/evaluate-grade/',
            {'measurements': [{'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 25.0,
                               'precision': 0.05, 'tolerance': 0.1}]},
            format='json',
        )
        self.assertIn(res.status_code, (401, 403))
        self.session.refresh_from_db()
        self.assertEqual(self.session.measurements['measurements'][0]['measuredVolume'], 24.8)

    def test_student_only_sees_own_sessions(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.get('/api/v1/workspace/sessions/')
        self.assertEqual(res.status_code, 200)
        returned = res.data['data'] if isinstance(res.data, dict) and 'data' in res.data else res.data
        results = returned['results'] if isinstance(returned, dict) and 'results' in returned else returned
        self.assertEqual([r for r in results if str(r['id']) == str(self.session.id)], [])

    def test_student_cannot_read_another_students_session(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.get(f'/api/v1/workspace/sessions/{self.session.id}/')
        self.assertIn(res.status_code, (403, 404))

    def test_student_cannot_tamper_with_another_students_grade(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.post(
            f'/api/v1/workspace/sessions/{self.session.id}/evaluate-grade/',
            {'measurements': [{'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 25.0,
                               'precision': 0.05, 'tolerance': 0.1}]},
            format='json',
        )
        self.assertIn(res.status_code, (403, 404))
        self.session.refresh_from_db()
        self.assertEqual(self.session.measurements['measurements'][0]['measuredVolume'], 24.8)

    def test_student_cannot_forge_session_attribution(self):
        """Posting someone else's id must still bind the session to the caller."""
        self.client.force_authenticate(user=self.other)
        res = self.client.post(
            '/api/v1/workspace/sessions/',
            {'lesson': self.lesson.id, 'student': str(self.student.id), 'measurements': {}},
            format='json',
        )
        self.assertEqual(res.status_code, 201, res.data)
        created = LessonSession.objects.get(id=res.data['id'])
        self.assertEqual(created.student_id, self.other.id)

    def test_instructor_can_read_any_session(self):
        self.client.force_authenticate(user=self.instructor)
        res = self.client.get(f'/api/v1/workspace/sessions/{self.session.id}/')
        self.assertEqual(res.status_code, 200)


class CatalogueWritePermissionTests(TestCase):
    """Reads stay open for released desktop clients; writes are staff-only."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = User.objects.create_instructor(
            email='instructor@example.com', password='pass', role=User.Roles.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='student@example.com', password='pass', role=User.Roles.STUDENT
        )
        self.lesson = Lesson.objects.create(
            title='Keep Me', description='x', instructor=self.instructor
        )

    def test_anonymous_can_still_read_lessons(self):
        # Released clients call this with no Authorization header.
        self.assertEqual(self.client.get('/api/v1/workspace/lessons/').status_code, 200)

    def test_anonymous_cannot_delete_a_lesson(self):
        res = self.client.delete(f'/api/v1/workspace/lessons/{self.lesson.id}/')
        self.assertIn(res.status_code, (401, 403))
        self.assertTrue(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_student_cannot_delete_a_lesson(self):
        self.client.force_authenticate(user=self.student)
        res = self.client.delete(f'/api/v1/workspace/lessons/{self.lesson.id}/')
        self.assertIn(res.status_code, (401, 403))
        self.assertTrue(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_anonymous_cannot_write_substances(self):
        res = self.client.post(
            '/api/v1/workbench/substance/', {'name': 'Injected', 'formula': 'XX'}, format='json'
        )
        self.assertIn(res.status_code, (401, 403))


class DynamicGradingTests(TestCase):
    """Tier 3: Dynamic grading evaluation of precision and target adherence."""

    def test_perfect_measurement_gives_perfect_grade(self):
        eval_res = evaluate_measurement_step(
            measured_volume=25.0, target_volume=25.0, precision=0.05, tolerance=0.1
        )
        self.assertEqual(eval_res['step_grade'], 100.0)
        self.assertEqual(eval_res['target_adherence'], 100.0)
        self.assertEqual(eval_res['precision_adherence'], 100.0)
        self.assertTrue(eval_res['is_within_tolerance'])

    def test_near_target_within_tolerance_gives_high_grade(self):
        # 0.04 mL deviation within 0.1 tolerance and 0.05 precision
        eval_res = evaluate_measurement_step(
            measured_volume=25.04, target_volume=25.0, precision=0.05, tolerance=0.1
        )
        self.assertGreaterEqual(eval_res['step_grade'], 90.0)
        self.assertTrue(eval_res['is_within_tolerance'])

    def test_measurement_outside_tolerance_penalized(self):
        eval_res = evaluate_measurement_step(
            measured_volume=27.0, target_volume=25.0, precision=0.05, tolerance=0.5
        )
        self.assertLess(eval_res['step_grade'], 50.0)
        self.assertFalse(eval_res['is_within_tolerance'])

    def test_session_wide_multi_step_grading(self):
        telemetry = [
            {'stepIndex': 0, 'targetVolume': 25.0, 'measuredVolume': 25.0, 'precision': 0.05, 'tolerance': 0.2},
            {'stepIndex': 1, 'targetVolume': 10.0, 'measuredVolume': 10.05, 'precision': 0.05, 'tolerance': 0.2},
        ]
        result = calculate_session_grade(telemetry)
        self.assertGreaterEqual(result['overall_grade'], 95.0)
        self.assertEqual(len(result['step_evaluations']), 2)
        self.assertIn('Dynamic Grade', result['feedback'])
