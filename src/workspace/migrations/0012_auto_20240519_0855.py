# Generated by Django 3.2.12 on 2024-05-19 08:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import src.workspace.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workspace', '0011_auto_20240516_0916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='instructor',
            field=models.ForeignKey(blank=True, default='1768f29f-a9a1-427f-8145-0be7882af329', on_delete=django.db.models.deletion.CASCADE, to='users.user', validators=[src.workspace.models.validate_instructor]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='lesson',
            name='parameters',
            field=models.CharField(blank=True, default='cm3', max_length=250),
        ),
    ]
