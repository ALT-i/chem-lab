"""Report where a lesson's written method and its bench procedure disagree.

Experiment 2A listed a six-step method while the bench tracked two, and
paired a "measuring cylinder" step with a beaker. Both were invisible until
someone walked the experiment as a student. This surfaces every such gap
across the catalogue so content can be corrected deliberately:

    python manage.py audit_lesson_procedures
    python manage.py audit_lesson_procedures --json

Exit status is 1 if any lesson has a problem, so it can gate a release.
"""
import json
import re

from django.core.management.base import BaseCommand

from src.workbench.models import Apparatus, Substance
from src.workspace.models import Lesson


OL_RE = re.compile(r'<ol\b.*?</ol>', re.I | re.S)
LI_SPLIT_RE = re.compile(r'<li\b[^>]*>', re.I)
TAG_RE = re.compile(r'<[^>]+>')


def method_steps(instructions):
    """Numbered steps of the written method: <li> items in the first <ol>."""
    if not instructions:
        return []
    blocks = OL_RE.findall(instructions)
    if not blocks:
        return []
    items = LI_SPLIT_RE.split(blocks[0])[1:]
    return [TAG_RE.sub('', item).split('</li>')[0].strip() for item in items]


def _produced_by(steps, upto, name):
    """True if any step up to and including `upto` produces an item called `name`."""
    for step in steps[: upto + 1]:
        for rule in (step.get('mergeRules') or []):
            if ((rule or {}).get('result') or {}).get('name') == name:
                return True
    return False


def audit_lesson(lesson, apparatus_names, substance_names):
    procedure = lesson.procedure or {}
    steps = procedure.get('steps') if isinstance(procedure, dict) else None
    steps = steps if isinstance(steps, list) else []
    method = method_steps(lesson.instructions)
    problems = []

    if not steps:
        problems.append('no bench procedure at all')
    if method and steps and len(steps) < len(method):
        problems.append('method has %d steps but the bench tracks %d' % (len(method), len(steps)))

    lesson_tools = set(lesson.tools.values_list('name', flat=True))
    lesson_subs = set(lesson.substances.values_list('name', flat=True))

    for i, step in enumerate(steps):
        rules = step.get('mergeRules') if isinstance(step, dict) else None
        if not rules:
            problems.append('step %d: no mergeRules, cannot be completed on the bench' % (i + 1))
            continue
        for rule in rules:
            with_ = (rule or {}).get('with') or {}
            for key in ('apparatus', 'substance'):
                name = with_.get(key)
                if not name:
                    continue
                known = name in apparatus_names or name in substance_names
                produced = _produced_by(steps, i, name)
                if not known and not produced:
                    problems.append(
                        'step %d: "%s" is not in the catalogue and no earlier step produces it' % (i + 1, name)
                    )
                elif known and name not in lesson_tools and name not in lesson_subs and not produced:
                    problems.append(
                        'step %d: "%s" is in the catalogue but not attached to this lesson' % (i + 1, name)
                    )
            image = ((rule or {}).get('result') or {}).get('image') or ''
            if '/media/' in image:
                problems.append("step %d: result image points at the app server's ephemeral /media/ path" % (i + 1))
            if rule.get('targetVolume') is not None and rule.get('tolerance') is None:
                problems.append('step %d: targetVolume without a tolerance' % (i + 1))

    # The method names an instrument the bench does not offer.
    text = ' '.join(method).lower()
    if 'measuring cylinder' in text and not any('cylinder' in t.lower() for t in lesson_tools):
        problems.append('method says "measuring cylinder" but the lesson has no cylinder among its apparatus')

    return {
        'id': lesson.id,
        'title': lesson.title,
        'method_steps': len(method),
        'bench_steps': len(steps),
        'problems': problems,
    }


class Command(BaseCommand):
    help = 'Report lessons whose written method and bench procedure disagree.'

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', help='machine-readable output')

    def handle(self, *args, **options):
        apparatus_names = set(Apparatus.objects.values_list('name', flat=True))
        substance_names = set(Substance.objects.values_list('name', flat=True))
        report = [
            audit_lesson(lesson, apparatus_names, substance_names)
            for lesson in Lesson.objects.order_by('id')
        ]
        bad = [r for r in report if r['problems']]

        if options['json']:
            self.stdout.write(json.dumps(report, indent=2))
        else:
            for r in report:
                flag = 'OK ' if not r['problems'] else '!! '
                self.stdout.write(
                    '%s[%2d] method=%d bench=%d  %s'
                    % (flag, r['id'], r['method_steps'], r['bench_steps'], r['title'][:70])
                )
                for problem in r['problems']:
                    self.stdout.write('        - ' + problem)
            self.stdout.write('\n%d of %d lessons need attention' % (len(bad), len(report)))

        if bad:
            raise SystemExit(1)
