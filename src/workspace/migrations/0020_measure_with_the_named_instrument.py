"""Route measurements through the instrument each method actually names.

Running the procedure audit across all 18 lessons, after the client began
crediting a delivering pipette, burette or measuring cylinder as the
instrument, left three content problems the client cannot fix on its own.

Experiment 5B (lesson 9) says "Pipette 25.0 cm3 of the NaOH solution into a
clean conical flask", but the lesson had no pipette among its apparatus, so
the bench measured the 25 cm3 with the conical flask (+/-5). The pipette is
attached and the step becomes the two it describes: draw 25 cm3 into the
pipette, then transfer it to the flask. The transfer keeps the original
result name, so every later step still matches.

Experiment 9A (lesson 15) says "Transfer 80 cm3 of distilled water (use a
measuring cylinder) to the calorimeter", but the bench measured with the
calorimeter itself. The measuring cylinder is attached and the step becomes:
measure 80 cm3 in the cylinder, then pour it into the calorimeter. Again the
transfer keeps the original result name.

Experiment 5A (lesson 8) step 2 carried two alternative rules, for
"Sodium Carbonate" and "Sodium Carbonate(soda ash)". Only the second is a
real catalogue item; the first can never match anything. It is removed.

Each change applies only if the lesson still has the shape described above.
"""
import copy

from django.db import migrations


PIPETTE = '5ml Pippette'
CYLINDER = '100cm3 Measuring Cylinder'
PIPETTE_IMG = 'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371222/apparatus/10mLPipette_vovml2.svg'
CYLINDER_IMG = 'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371761/apparatus/50mLBurette_su7inw.svg'


def _first_rule(step):
    rules = (step or {}).get('mergeRules') or []
    return rules[0] if rules else {}


def _with(rule):
    return (rule or {}).get('with') or {}


def _fix_5b(lesson, Apparatus):
    steps = list((lesson.procedure or {}).get('steps') or [])
    if not steps:
        return False
    rule = _first_rule(steps[0])
    w = _with(rule)
    if not (w.get('apparatus') == '250cm3 Conical Flask' and w.get('substance') == 'Sodium Hydroxide'):
        return False

    transfer_result = copy.deepcopy(rule.get('result') or {'name': 'Sodium Hydroxide solution'})
    draw = {
        'description': 'Using a pipette, draw 25.0 cm³ of the NaOH solution.',
        'apparatus': [{'name': PIPETTE, 'action': 'add'}],
        'substances': [{'name': 'Sodium Hydroxide', 'action': 'add', 'volume': '25 cm³'}],
        'mergeRules': [{
            'with': {'apparatus': PIPETTE, 'substance': 'Sodium Hydroxide'},
            'result': {'name': 'Pipette with 25cm3 Sodium Hydroxide', 'image': PIPETTE_IMG},
            'targetVolume': 25,
            'tolerance': 0.5,
        }],
    }
    transfer = {
        'description': 'Transfer the 25.0 cm³ of NaOH from the pipette into a clean conical flask.',
        'apparatus': [{'name': '250cm3 Conical Flask', 'action': 'add'}],
        'substances': [{'name': 'Pipette with 25cm3 Sodium Hydroxide', 'action': 'pour', 'volume': '25 cm³'}],
        'mergeRules': [{
            'with': {'apparatus': '250cm3 Conical Flask', 'substance': 'Pipette with 25cm3 Sodium Hydroxide'},
            'result': transfer_result,
            'targetVolume': 25,
            'tolerance': 0.5,
        }],
    }
    lesson.procedure = {**(lesson.procedure or {}), 'steps': [draw, transfer] + steps[1:]}
    pipette = Apparatus.objects.filter(name=PIPETTE).first()
    if pipette is not None:
        lesson.tools.add(pipette)
    return True


def _fix_9a(lesson, Apparatus):
    steps = list((lesson.procedure or {}).get('steps') or [])
    if not steps:
        return False
    rule = _first_rule(steps[0])
    w = _with(rule)
    if not (w.get('apparatus') == 'Calorimeter' and w.get('substance') == 'Distilled Water'):
        return False

    transfer_result = copy.deepcopy(rule.get('result') or {'name': 'Calorimeter with Distilled water'})
    measure = {
        'description': 'Measure 80 cm³ of distilled water using the measuring cylinder.',
        'apparatus': [{'name': CYLINDER, 'action': 'add'}],
        'substances': [{'name': 'Distilled Water', 'action': 'add', 'volume': '80 cm³'}],
        'mergeRules': [{
            'with': {'apparatus': CYLINDER, 'substance': 'Distilled Water'},
            'result': {'name': 'Distilled Water in Measuring Cylinder', 'image': CYLINDER_IMG},
            'targetVolume': 80,
            'tolerance': 0.5,
        }],
    }
    pour = {
        'description': 'Pour the 80 cm³ of water from the cylinder into the calorimeter.',
        'apparatus': [{'name': 'Calorimeter', 'action': 'add'}],
        'substances': [{'name': 'Distilled Water in Measuring Cylinder', 'action': 'pour', 'volume': '80 cm³'}],
        'mergeRules': [{
            'with': {'apparatus': 'Calorimeter', 'substance': 'Distilled Water in Measuring Cylinder'},
            'result': transfer_result,
            'targetVolume': 80,
            'tolerance': 0.5,
        }],
    }
    lesson.procedure = {**(lesson.procedure or {}), 'steps': [measure, pour] + steps[1:]}
    cylinder = Apparatus.objects.filter(name=CYLINDER).first()
    if cylinder is not None:
        lesson.tools.add(cylinder)
    return True


def _fix_5a(lesson):
    steps = list((lesson.procedure or {}).get('steps') or [])
    if len(steps) < 2:
        return False
    rules = steps[1].get('mergeRules') or []
    kept = [r for r in rules if _with(r).get('substance') != 'Sodium Carbonate']
    if len(kept) == len(rules) or not kept:
        return False  # nothing to remove, or it would leave the step uncompletable
    steps[1] = {**steps[1], 'mergeRules': kept}
    lesson.procedure = {**(lesson.procedure or {}), 'steps': steps}
    return True


def forwards(apps, schema_editor):
    Lesson = apps.get_model('workspace', 'Lesson')
    Apparatus = apps.get_model('workbench', 'Apparatus')

    for pk, fix in ((9, lambda l: _fix_5b(l, Apparatus)),
                    (15, lambda l: _fix_9a(l, Apparatus)),
                    (8, _fix_5a)):
        lesson = Lesson.objects.filter(pk=pk).first()
        if lesson is not None and fix(lesson):
            lesson.save(update_fields=['procedure'])


def backwards(apps, schema_editor):
    """Not reversed: the original steps measured with the wrong instrument."""


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0019_experiment_2a_follow_the_method'),
        ('workbench', '0011_add_measuring_cylinder'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
