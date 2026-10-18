"""Add a measuring cylinder to the apparatus catalogue.

Experiment 2A's written method says "measure accurately 20 cm3 ... using a
dry measuring cylinder", but no measuring cylinder existed anywhere in the
catalogue, so the lesson paired the step with a 400 cm3 beaker. A beaker
reads to about +/-25 cm3; the step asks for +/-0.5. Students were being
graded on an instrument that cannot do the job the method describes.

A 100 cm3 Class B measuring cylinder reads to +/-0.5 cm3, which is what the
step actually needs. Idempotent: skipped if one already exists.

The image is the burette artwork as a stand-in -- the closest shape on hand
(a tall graduated tube). Replace with a proper cylinder SVG when one is drawn.
"""
from django.db import migrations


CYLINDER = {
    'name': '100cm3 Measuring Cylinder',
    'image': 'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371761/apparatus/50mLBurette_su7inw.svg',
    'type': '',
    'category': 'GLASSWARE',
    'material': 'GLASS',
    'volume': 100,
    'precision': 0.5,
    'thermal_properties': '',
}


def forwards(apps, schema_editor):
    Apparatus = apps.get_model('workbench', 'Apparatus')
    if Apparatus.objects.filter(name__icontains='measuring cylinder').exists():
        return
    Apparatus.objects.create(**CYLINDER)


def backwards(apps, schema_editor):
    Apparatus = apps.get_model('workbench', 'Apparatus')
    Apparatus.objects.filter(name=CYLINDER['name']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('workbench', '0010_populate_apparatus_precision'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
