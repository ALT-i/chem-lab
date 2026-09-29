# Generated manually for moodle_assignment_id field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0014_alter_lesson_instructor'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='moodle_assignment_id',
            field=models.IntegerField(blank=True, null=True, help_text='Moodle assignment ID for grade submission'),
        ),
    ]
