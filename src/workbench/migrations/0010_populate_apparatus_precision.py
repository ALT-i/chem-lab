"""Give measuring apparatus a real reading precision, and a capacity.

Tier 1 added Apparatus.precision but left every row NULL, so grading had no
instrument tolerance to score a measurement against and the lab could not
tell a burette from a beaker.

Values are the usual tolerances for Class B student glassware, in cm3:
a burette is read to half a scale division, a beaker is barely a measuring
vessel at all. Items that do not measure volume (burners, thermometers,
metal strips) are intentionally left NULL.
"""
from django.db import migrations


# name -> (precision cm3, capacity cm3 or None to leave alone)
APPARATUS_PRECISION = {
    '50ml Burrette': (0.05, 50),          # read to half a 0.1 division
    '5ml Pippette': (0.01, 5),            # bulb pipette, very precise
    '250cm3 Volumetric Flask': (0.15, None),
    '500cm3 Volumetric Flask': (0.25, None),
    '1 litre Flask': (0.40, None),
    '250cm3 Conical Flask': (5.0, None),  # titration vessel, not a measure
    '400cm3 Beaker': (25.0, None),        # graduations are nominal only
    '100cm3 Beaker': (5.0, 100),
    'Test Tube': (0.5, 20),
    'Polystyrene Cup': (5.0, 200),        # calorimetry cup
    'Calorimeter': (1.0, 250),
    'Watch Glass': (None, 50),
    'Evaporating Dish': (None, 100),
    'Funnel': (None, 75),
}


def populate(apps, schema_editor):
    Apparatus = apps.get_model('workbench', 'Apparatus')

    for item in Apparatus.objects.all():
        props = APPARATUS_PRECISION.get(item.name)
        if props is None:
            continue
        precision, capacity = props
        changed = []

        if precision is not None and item.precision is None:
            item.precision = precision
            changed.append('precision')
        if capacity is not None and item.volume is None:
            item.volume = capacity
            changed.append('volume')

        if changed:
            item.save(update_fields=changed)


def noop(apps, schema_editor):
    """Deliberately not reversed: we cannot tell which values were ours."""


class Migration(migrations.Migration):

    dependencies = [
        ('workbench', '0009_populate_substance_properties'),
    ]

    operations = [
        migrations.RunPython(populate, noop),
    ]
