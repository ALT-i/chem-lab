# Generated by Django 3.2.12 on 2023-07-29 14:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workbench', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=250)),
                ('instructions', models.TextField(blank=True, max_length=5000)),
                ('parameters', models.CharField(blank=True, max_length=250)),
                ('instructor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('substances', models.ManyToManyField(to='workbench.Substance')),
                ('tools', models.ManyToManyField(to='workbench.Apparatus')),
            ],
        ),
        migrations.CreateModel(
            name='LessonSession',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False, verbose_name='session_id')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='workspace.lesson')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
