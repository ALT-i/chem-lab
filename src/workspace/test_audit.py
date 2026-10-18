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
        self.flask = Apparatus.objects.create(name='250cm3 Conical Flask', volume=250, precision=5)
        self.apparatus_names = {self.beaker.name, self.cylinder.name, self.flask.name}
        self.precision = {self.beaker.name: 25.0, self.cylinder.name: 0.5, self.flask.name: 5.0}
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
        report = audit_lesson(lesson, self.apparatus_names, self.substance_names, self.precision)
        self.assertEqual(report['method_steps'], 3)
        self.assertEqual(report['bench_steps'], 1)
        # a step-count gap is advisory: most extra method steps are not bench actions
        self.assertIn('method has 3 steps but the bench tracks 1', ' | '.join(report['warnings']))
        self.assertNotIn('method has', ' | '.join(report['problems']))
        joined = ' | '.join(report['problems'])
        self.assertIn('method measures 20 cm3 with a measuring cylinder, but the bench measures it without one', joined)
        # and the beaker cannot measure a +/-0.5 step
        self.assertIn('400cm3 Beaker (+/-25.0) cannot measure a +/-0.5 step', joined)

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


    def test_pipette_transfer_into_a_flask_is_not_flagged(self):
        # mirrors the client: the pipette measured it, not the flask
        lesson = self._lesson(
            {'steps': [
                {'mergeRules': [self._rule('5ml Pippette', 'Hydrochloric Acid', result='Pipette with 25cm3 HCl', targetVolume=25, tolerance=0.5)]},
                {'mergeRules': [self._rule('250cm3 Conical Flask', 'Pipette with 25cm3 HCl', result='Z', targetVolume=25, tolerance=0.5)]},
            ]},
            '<ol><li>a</li><li>b</li></ol>', tools=[self.flask], substances=[self.hcl],
        )
        problems = audit_lesson(lesson, self.apparatus_names | {'5ml Pippette'}, self.substance_names, self.precision)['problems']
        self.assertFalse([p for p in problems if 'cannot measure' in p], problems)

    def test_a_flask_measuring_on_its_own_is_flagged(self):
        lesson = self._lesson(
            {'steps': [{'mergeRules': [self._rule('250cm3 Conical Flask', 'Hydrochloric Acid', targetVolume=25, tolerance=0.5)]}]},
            '<ol><li>a</li></ol>', tools=[self.flask], substances=[self.hcl],
        )
        joined = ' | '.join(audit_lesson(lesson, self.apparatus_names, self.substance_names, self.precision)['problems'])
        self.assertIn('250cm3 Conical Flask (+/-5.0) cannot measure a +/-0.5 step', joined)


    def test_cylinder_named_for_a_step_the_bench_skips_is_not_flagged(self):
        # Experiment 2B quotes 2A's preparation ("measure 20 cm3 ... measuring
        # cylinder") but its bench starts from the prepared acid and never
        # measures 20 cm3 at all.
        lesson = self._lesson(
            {'steps': [{'mergeRules': [self._rule('250cm3 Conical Flask', 'Pipette with 25cm3 HCl', targetVolume=25, tolerance=0.5)]}]},
            '<ol><li>Measure accurately 20cm<sup>3</sup> of HCl using a dry measuring cylinder.</li></ol>',
            tools=[self.flask], substances=[self.hcl],
        )
        joined = ' | '.join(audit_lesson(lesson, self.apparatus_names, self.substance_names, self.precision)['problems'])
        self.assertNotIn('measuring cylinder', joined)

    def test_cylinder_rule_is_satisfied_once_the_bench_uses_one(self):
        # 9A after re-authoring: 80 cm3 is measured in the cylinder, then poured
        lesson = self._lesson(
            {'steps': [
                {'mergeRules': [self._rule('100cm3 Measuring Cylinder', 'Hydrochloric Acid', result='Acid In Cylinder', targetVolume=80, tolerance=0.5)]},
                {'mergeRules': [self._rule('250cm3 Conical Flask', 'Acid In Cylinder', targetVolume=80, tolerance=0.5)]},
            ]},
            '<ol><li>Transfer 80cm3 of water (use a measuring cylinder) to the flask.</li><li>b</li></ol>',
            tools=[self.cylinder, self.flask], substances=[self.hcl],
        )
        joined = ' | '.join(audit_lesson(lesson, self.apparatus_names, self.substance_names, self.precision)['problems'])
        self.assertNotIn('measuring cylinder', joined)
