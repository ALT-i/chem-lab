"""Repoint merge-result images that 404.

Lesson procedures reference the image shown when two items combine -- the
moment an experiment pays off. 12 of the 17 distinct images point at
/media/substances/ on the app server, which has an ephemeral filesystem, so
the uploads are gone and 17 of 18 lessons render a broken image.

Four of them have a genuine equivalent already on Cloudinary, verified to
return 200. Those are repointed here. The remaining eight have no replacement
anywhere, so they are left alone; the desktop client falls back to a
placeholder on image error rather than showing a broken icon.
"""
from django.db import migrations


DEAD_IMAGE_REPLACEMENTS = {
    'https://chem-lab-backend.onrender.com/media/substances/250mLBeaker_mgEbP3x.svg':
        'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371560/apparatus/250mLBeaker_nijm7r.svg',
    'https://chem-lab-backend.onrender.com/media/substances/250mLFlask_DtizFfV.svg':
        'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371500/apparatus/250mLFlask_vs6nkb.svg',
    'https://chem-lab-backend.onrender.com/media/substances/50mLBurette_kH9ugGL.svg':
        'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371194/apparatus/50mLBurette_lk0oac.svg',
    'https://chem-lab-backend.onrender.com/media/substances/noun-wire-259240.svg':
        'https://res.cloudinary.com/dl1qqgbdw/image/upload/v1716371878/apparatus/noun-wire-259240_wngwgu.svg',
}


def _repoint(procedure, mapping):
    """Rewrite result images in place. Returns True if anything changed."""
    if not isinstance(procedure, dict):
        return False
    steps = procedure.get('steps')
    if not isinstance(steps, list):
        return False

    changed = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        for rule in step.get('mergeRules') or []:
            if not isinstance(rule, dict):
                continue
            result = rule.get('result')
            if not isinstance(result, dict):
                continue
            replacement = mapping.get(result.get('image'))
            if replacement:
                result['image'] = replacement
                changed = True
    return changed


def forwards(apps, schema_editor):
    Lesson = apps.get_model('workspace', 'Lesson')
    for lesson in Lesson.objects.exclude(procedure=None):
        if _repoint(lesson.procedure, DEAD_IMAGE_REPLACEMENTS):
            lesson.save(update_fields=['procedure'])


def backwards(apps, schema_editor):
    Lesson = apps.get_model('workspace', 'Lesson')
    reverse_map = {v: k for k, v in DEAD_IMAGE_REPLACEMENTS.items()}
    for lesson in Lesson.objects.exclude(procedure=None):
        if _repoint(lesson.procedure, reverse_map):
            lesson.save(update_fields=['procedure'])


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0017_auto_20260930_1611'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
