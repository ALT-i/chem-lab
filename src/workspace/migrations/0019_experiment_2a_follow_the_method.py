"""Make Experiment 2A's bench procedure follow its own written method.

The lesson text gives a six-step method, then a separate "Simulator
procedure" of three drags that used a 400 cm3 beaker for everything and
stopped after the first dilution. A student reading the method expected to
measure with a cylinder, use the 250 cm3 volumetric flask, and make up to
the mark -- none of which the bench offered.

The bench now performs the method's actual bench actions, in order:

  1. measure 20 cm3 of HCl in the measuring cylinder        (method step 1)
  2. put ~100 cm3 of distilled water in the volumetric flask  (method step 2)
  3. pour the acid from the cylinder into the flask           (method step 2)
  4. make up to the 250 cm3 mark with distilled water         (method step 4)

Shaking, stoppering and cooling (steps 3 and 5) are not bench actions and
remain written instructions; standardisation (step 6) is its own experiment.
The "Simulator procedure" text is rewritten to say exactly this, so the panel
and the step tracker agree.

The measuring cylinder is added to the lesson's apparatus. Only lesson 3 is
touched, and only if it still carries the original two-step procedure.
"""
from django.db import migrations


FLASK_IMG = 'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371500/apparatus/250mLFlask_vs6nkb.svg'
CYLINDER_IMG = 'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371761/apparatus/50mLBurette_su7inw.svg'

NEW_PROCEDURE = {
    'steps': [
        {
            'description': 'Measure accurately 20 cm³ of concentrated HCl using the dry measuring cylinder.',
            'apparatus': [{'name': '100cm3 Measuring Cylinder', 'action': 'add'}],
            'substances': [{'name': 'Hydrochloric Acid', 'action': 'add', 'volume': '20 cm³'}],
            'mergeRules': [{
                'with': {'apparatus': '100cm3 Measuring Cylinder', 'substance': 'Hydrochloric Acid'},
                'result': {'name': 'Hydrochloric Acid', 'image': CYLINDER_IMG},
                'targetVolume': 20,
                'tolerance': 0.5,
            }],
        },
        {
            'description': 'Pour about 100 cm³ of distilled water into the 250 cm³ volumetric flask.',
            'apparatus': [{'name': '250cm3 Volumetric Flask', 'action': 'add'}],
            'substances': [{'name': 'Distilled Water', 'action': 'pour', 'volume': '100 cm³'}],
            'mergeRules': [{
                'with': {'apparatus': '250cm3 Volumetric Flask', 'substance': 'Distilled Water'},
                'result': {'name': 'Distilled Water', 'image': FLASK_IMG},
                'targetVolume': 100,
                'tolerance': 10,
            }],
        },
        {
            'description': 'Pour the acid from the cylinder into the flask of water, gradually but gently.',
            'apparatus': [{'name': 'Distilled Water', 'action': 'add'}],
            'substances': [{'name': 'Hydrochloric Acid', 'action': 'pour', 'volume': '20 cm³'}],
            'mergeRules': [{
                # `apparatus` names the vessel that receives the pour: the flask,
                # whose merged item is called "Distilled Water" at this point.
                'with': {'apparatus': 'Distilled Water', 'substance': 'Hydrochloric Acid'},
                'result': {'name': 'Diluted Acid Solution', 'image': FLASK_IMG},
                'targetVolume': 20,
                'tolerance': 0.5,
            }],
        },
        {
            'description': 'Make up to the 250 cm³ mark with more distilled water, then shake thoroughly.',
            'apparatus': [{'name': 'Diluted Acid Solution', 'action': 'add'}],
            'substances': [{'name': 'Distilled Water', 'action': 'pour', 'volume': '130 cm³'}],
            'mergeRules': [{
                'with': {'apparatus': 'Diluted Acid Solution', 'substance': 'Distilled Water'},
                'result': {'name': 'Standard HCl Solution', 'image': FLASK_IMG},
                # 250 - (100 + 20); the flask's 250 cm3 capacity stops overfilling
                'targetVolume': 130,
                'tolerance': 10,
            }],
        },
    ]
}

OLD_SIMULATOR_SECTION_MARKER = 'Simulator procedure:'

NEW_SIMULATOR_HTML = """<p style="font-weight: bold;font-size: larger;"><strong>Simulator procedure:</strong></p>
<p>The bench performs the method's measuring and pouring steps. Shaking, stoppering and cooling are done as written, and standardisation is the next experiment.</p>
<ol style="list-style: decimal !important;">
  <li>Drag the <strong>Measuring Cylinder</strong> onto the bench, then drag <strong>Hydrochloric Acid</strong> onto it and enter <strong>20 cm<sup>3</sup></strong>.</li>
  <li>Drag the <strong>250cm<sup>3</sup> Volumetric Flask</strong> onto the bench, then drag <strong>Distilled Water</strong> onto it and enter about <strong>100 cm<sup>3</sup></strong>.</li>
  <li>Drag the <strong>cylinder of acid</strong> onto the <strong>flask of water</strong> and pour in the 20 cm<sup>3</sup>.</li>
  <li>Drag <strong>Distilled Water</strong> onto the flask once more and make up to the <strong>250 cm<sup>3</sup></strong> mark. <em>The End.</em></li>
</ol>"""


def _is_original_two_step(procedure):
    steps = (procedure or {}).get('steps') or []
    if len(steps) != 2:
        return False
    first = (steps[0].get('mergeRules') or [{}])[0].get('with', {})
    return first.get('apparatus') == '400cm3 Beaker' and first.get('substance') == 'Hydrochloric Acid'


def forwards(apps, schema_editor):
    Lesson = apps.get_model('workspace', 'Lesson')
    Apparatus = apps.get_model('workbench', 'Apparatus')

    lesson = Lesson.objects.filter(pk=3).first()
    if lesson is None or not _is_original_two_step(lesson.procedure):
        return

    lesson.procedure = NEW_PROCEDURE

    cylinder = Apparatus.objects.filter(name='100cm3 Measuring Cylinder').first()
    if cylinder is not None:
        lesson.tools.add(cylinder)

    text = lesson.instructions or ''
    idx = text.find(OLD_SIMULATOR_SECTION_MARKER)
    if idx != -1:
        # back up to the start of the <p> that holds the heading
        p_start = text.rfind('<p', 0, idx)
        lesson.instructions = text[: p_start if p_start != -1 else idx] + NEW_SIMULATOR_HTML
    lesson.save(update_fields=['procedure', 'instructions'])


def backwards(apps, schema_editor):
    """Not reversed: the original procedure described the wrong instrument."""


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0018_repoint_dead_mergerule_images'),
        ('workbench', '0011_add_measuring_cylinder'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
