from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MoodleConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_url', models.URLField(blank=True, default='', help_text='Moodle site root, e.g. https://your-site.moodlecloud.com (no trailing /webservice path)')),
                ('token', models.CharField(blank=True, default='', help_text='Web service token generated in Moodle under Site administration > Server > Web services > Manage tokens', max_length=255)),
                ('course_id', models.IntegerField(blank=True, help_text="Moodle course ID that the lab's experiments belong to", null=True)),
                ('default_assignment_id', models.IntegerField(blank=True, help_text='Fallback assignment ID used only when a lesson has none of its own', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Uncheck to disable the Moodle integration without deleting the credentials')),
                ('last_verified_at', models.DateTimeField(blank=True, null=True)),
                ('last_verification_error', models.TextField(blank=True, default='')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Moodle configuration',
                'verbose_name_plural': 'Moodle configuration',
            },
        ),
    ]
