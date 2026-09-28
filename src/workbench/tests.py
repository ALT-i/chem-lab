from django.test import TestCase
from rest_framework.test import APIClient

from src.users.models import User
from src.workbench.models import Apparatus, Substance
from src.workspace.models import Lesson


class SubstancePrecisionTests(TestCase):
    """phValue and volume must hold fractional values (e.g. pH 7.4, 12.5 cm3)."""

    def setUp(self):
        self.client = APIClient()

    def test_create_substance_with_fractional_ph_and_volume(self):
        response = self.client.post(
            '/api/v1/workbench/substance/',
            {'name': 'Blood Plasma Buffer', 'formula': 'NaHCO3', 'volume': 12.5, 'phValue': 7.4, 'molarity': 0.025},
            format='json',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['data']['phValue'], 7.4)
        self.assertEqual(response.data['data']['volume'], 12.5)

    def test_fractional_values_survive_a_database_round_trip(self):
        substance = Substance.objects.create(name='Buffer', phValue=7.4, volume=12.5)
        substance.refresh_from_db()

        self.assertEqual(substance.phValue, 7.4)
        self.assertEqual(substance.volume, 12.5)

    def test_whole_number_values_still_accepted(self):
        response = self.client.post(
            '/api/v1/workbench/substance/',
            {'name': 'Hydrochloric Acid', 'formula': 'HCl', 'volume': 500, 'phValue': 1, 'molarity': 0.1},
            format='json',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['data']['phValue'], 1)
        self.assertEqual(response.data['data']['volume'], 500)

    def test_ph_and_volume_remain_optional(self):
        response = self.client.post('/api/v1/workbench/substance/', {'name': 'Universal Indicator'}, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data['data']['phValue'])
        self.assertIsNone(response.data['data']['volume'])


class LessonPayloadTests(TestCase):
    """The desktop app reads substance and apparatus properties straight from the lesson payload."""

    def setUp(self):
        instructor = User.objects.create_instructor(email='instructor@example.com', password='x', role=User.Roles.INSTRUCTOR)
        self.lesson = Lesson.objects.create(title='Titration', description='d', instructor=instructor)
        self.lesson.substances.add(
            Substance.objects.create(name='Buffer', phValue=7.4, volume=12.5, molarity=0.1, thermal_properties='Stable')
        )
        self.lesson.tools.add(Apparatus.objects.create(name='250 mL Beaker', volume=250))

    def test_lesson_includes_substance_properties(self):
        response = APIClient().get(f'/api/v1/workspace/lessons/{self.lesson.id}/')

        substance = response.data['data']['substances'][0]
        self.assertEqual(substance['phValue'], 7.4)
        self.assertEqual(substance['volume'], 12.5)
        self.assertEqual(substance['molarity'], 0.1)
        self.assertEqual(substance['thermal_properties'], 'Stable')

    def test_lesson_includes_apparatus_capacity(self):
        response = APIClient().get(f'/api/v1/workspace/lessons/{self.lesson.id}/')

        self.assertEqual(response.data['data']['tools'][0]['volume'], 250)
