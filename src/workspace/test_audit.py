from django.test import TestCase

from src.users.models import User
from src.workbench.models import Apparatus, Substance
from src.workspace.management.commands.audit_lesson_procedures import audit_lesson, method_steps
from src.workspace.models import Lesson


class MethodStepParsingTests(TestCase):
    def test_reads_numbered_steps_from_the_first_list_only(self):
        html = (
            '<ol><li><strong>Measure</strong> 20 cm<sup>3</sup>.</li><li>Pour.</li></ol>'
            '<p>Simulator procedure:</p><ol><li>Drag beaker</li></ol>'
        )
        self.assertEqual(method_steps(html), ['Measure 20 cm3.', 'Pour.'])

    def test_empty_or_listless_text_gives_no_steps(self):
        self.assertEqual(method_steps(''), [])
        self.assertEqual(method_steps(None), [])
        self.assertEqual(method_steps('<p>just prose</p>'), [])


class LessonProcedureAuditTests(TestCase):
    """The audit must catch exactly the gaps found by walking Experiment 2A."""

    def setUp(self):
        self.instructor = User.objects.create_instructor(
            email='audit.teacher@example.com', password='p', role=User.Roles.INSTRUCTOR
        )
        self.beaker = Apparatus.objects.create(name='400cm3 Beaker', volume=400, precision=25)
        self.cylinder = Apparatus.objects.create(name='100cm3 Measuring Cylinder', volume=100, precision=0.5)
        self.hcl = Substance.objects.create(name='Hydrochloric Acid', formula='HCl')
        self.apparatus_names = {self.beaker.name, self.cylinder.name}
        self.substance_names = {self.hcl.name}

    def _lesson(self, procedure, instructions, tools=(), substances=()):
        lesson = Lesson.objects.create(
            title='T', description='d', instructor=self.instructor,
            procedure=procedure, instructions=instructions,
        )
        lesson.tools.set(tools)
        lesson.substances.set(substances)
        return lesson

    def _rule(self, apparatus, substance, result='X', image='https://x/y.svg', **extra):
        rule = {'with': {'apparatus': apparatus, 'substance': substance}, 'result': {'name': result, 'image': image}}
        rule.update(extra)
        return rule

    def test_flags_method_longer_than_bench_and_missing_cylinder(self):
        lesson = self._lesson(
            {'steps': [{'mergeRules': [self._rule('400cm3 Beaker', 'Hydrochloric Acid', targetVolume=20, tolerance=0.5)]}]},
            '<ol><li>Measure 20 cm3 using a dry measuring cylinder.</li><li>Pour.</li><li>Shake.</li></ol>',
            tools=[self.beaker], substances=[self.hcl],
        )
        report = audit_lesson(lesson, self.apparatus_names, self.substance_names)
        self.assertEqual(report['method_steps'], 3)
        self.assertEqual(report['bench_steps'], 1)
        joined = ' | '.join(report['problems'])
        self.assertIn('method has 3 steps but the bench tracks 1', joined)
        self.assertIn('no cylinder among its apparatus', joined)

    def test_flags_unknown_names_ephemeral_images_and_missing_tolerance(self):
        lesson = self._lesson(
            {'steps': [{'mergeRules': [self._rule(
                'Unicorn Flask', 'Hydrochloric Acid',
                image='https://chem-lab-backend.onrender.com/media/substances/a.svg',
                targetVolume=20,
            )]}]},
            '<ol><li>one</li></ol>', tools=[], substances=[self.hcl],
        )
        joined = ' | '.join(audit_lesson(lesson, self.apparatus_names, self.substance_names)['problems'])
        self.assertIn('"Unicorn Flask" is not in the catalogue', joined)
        self.assertIn('ephemeral /media/ path', joined)
        self.assertIn('targetVolume without a tolerance', joined)

    def test_catalogue_item_not_attached_to_lesson_is_flagged(self):
        lesson = self._lesson(
            {'steps': [{'mergeRules': [self._rule('400cm3 Beaker', 'Hydrochloric Acid', targetVolume=20, tolerance=0.5)]}]},
            '<ol><li>one</li></ol>', tools=[], substances=[self.hcl],
        )
        joined = ' | '.join(audit_lesson(lesson, self.apparatus_names, self.substance_names)['problems'])
        self.assertIn('"400cm3 Beaker" is in the catalogue but not attached to this lesson', joined)

    def test_a_name_produced_by_an_earlier_step_is_not_flagged(self):
        lesson = self._lesson(
            {'steps': [
                {'mergeRules': [self._rule('100cm3 Measuring Cylinder', 'Hydrochloric Acid', result='Acid In Cylinder', targetVolume=20, tolerance=0.5)]},
                {'mergeRules': [self._rule('Acid In Cylinder', 'Hydrochloric Acid', result='Z', targetVolume=20, tolerance=0.5)]},
            ]},
            '<ol><li>a</li><li>b</li></ol>', tools=[self.cylinder], substances=[self.hcl],
        )
        self.assertEqual(audit_lesson(lesson, self.apparatus_names, self.substance_names)['problems'], [])

    def test_lesson_with_no_procedure_is_flagged(self):
        lesson = self._lesson({}, '<ol><li>a</li></ol>')
        self.assertIn('no bench procedure at all', audit_lesson(lesson, self.apparatus_names, self.substance_names)['problems'])
