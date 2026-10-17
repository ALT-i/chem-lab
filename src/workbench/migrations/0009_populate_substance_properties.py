"""Fill in realistic physical properties for the stock substances.

Almost every Substance row had volume / phValue / molarity left NULL, so the
lab had nothing real to show or check a measurement against. These are the
concentrations a teaching lab actually keeps on the shelf, with the pH that
such a solution really has (not the pH of the pure compound).

Only NULL fields are filled, so any value an instructor has already entered
is left alone. The one exception is noted inline: a molarity of 84 mol/L is
not physically possible and is corrected.
"""
from django.db import migrations


# name -> (stock volume cm3, pH of that solution, molarity mol/dm3)
# None means "leave whatever is there".
SUBSTANCE_PROPERTIES = {
    # --- strong acids -------------------------------------------------
    'Hydrochloric Acid': (500, 1.1, 0.1),
    'Tetraoxosulphate (VI)': (500, 0.9, 0.1),      # H2SO4, first proton strong
    'Trioxonitrate': (500, 1.0, 0.1),              # HNO3
    # --- weak acid ----------------------------------------------------
    'Oxalic Acid Solution': (500, 1.3, 0.1),
    # --- strong bases -------------------------------------------------
    'Sodium Hydroxide': (500, 13.0, 0.1),
    'Potassium Hydroxide': (500, 13.0, 0.1),
    # --- weak base ----------------------------------------------------
    'Ammonia Solution': (500, 11.1, 0.1),          # NH3(aq)
    # --- basic salts (hydrolysis) -------------------------------------
    'Sodium TriOxoCarbonate': (None, 11.6, 0.1),   # Na2CO3
    'Sodium Carbonate(soda ash)': (None, 11.6, 0.1),
    'Sodium Carbonate (soda ash)': (None, 11.6, None),
    'Sodium Carbonate Solution': (None, 11.6, 0.1),
    'Potassium Trioxocarbonate VI': (500, 11.6, 0.1),   # K2CO3
    'Sodium Hydrogen Carbonate': (None, 8.3, 0.1),      # NaHCO3
    # --- acidic / near-neutral salts ----------------------------------
    'Copper Sulphate': (500, 4.0, 0.1),
    'Ferrous Sulfate': (500, 3.5, 0.1),
    'Ferrous Sulphate Heptahydrate': (500, 3.5, 0.1),
    'Zinc Nitrate': (500, 5.3, 0.1),
    'Silver Nitrate': (250, 5.5, 0.1),
    'Silver Trioxonitrate': (250, 5.5, 0.1),
    'Lead Trioxonitrate': (250, 4.0, 0.1),
    'Barium Chloride': (500, 7.0, 0.1),
    'Potassium Permanganate': (500, 6.8, 0.02),    # standard titration strength
    # --- solvent ------------------------------------------------------
    'Distilled Water': (None, 7.0, None),          # molarity is meaningless here
    # --- indicators (dilute solutions, not titrants) ------------------
    'Methyl Orange': (100, 6.0, 0.003),            # ~0.1% w/v
    'Phenolphthalein': (None, 7.0, 0.03),          # ~1% in ethanol
    # 'Unknown Compound' is deliberately left blank: identifying it is the
    # point of the qualitative analysis experiments.
}


def populate(apps, schema_editor):
    Substance = apps.get_model('workbench', 'Substance')

    for substance in Substance.objects.all():
        props = SUBSTANCE_PROPERTIES.get(substance.name)
        if props is None:
            continue
        volume, ph, molarity = props
        changed = []

        if volume is not None and substance.volume is None:
            substance.volume = volume
            changed.append('volume')
        if ph is not None and substance.phValue is None:
            substance.phValue = ph
            changed.append('phValue')
        if molarity is not None and substance.molarity is None:
            substance.molarity = molarity
            changed.append('molarity')

        # 84 mol/dm3 is not a possible concentration -- it is the molar mass
        # of NaHCO3 entered into the wrong field. Nothing can be 84 molar.
        if substance.molarity is not None and substance.molarity > 20:
            substance.molarity = molarity if molarity is not None else None
            changed.append('molarity')

        if changed:
            substance.save(update_fields=list(set(changed)))


def noop(apps, schema_editor):
    """Deliberately not reversed: we cannot tell which values were ours."""


class Migration(migrations.Migration):

    dependencies = [
        ('workbench', '0008_apparatus_precision'),
    ]

    operations = [
        migrations.RunPython(populate, noop),
    ]
