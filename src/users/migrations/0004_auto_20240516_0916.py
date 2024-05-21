# Generated by Django 3.2.12 on 2024-05-16 09:16

import datetime
from django.db import migrations, models
import src.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20230730_0522'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='profile_image',
        ),
        migrations.AddField(
            model_name='user',
            name='image',
            field=models.CharField(blank=True, default='default.png', max_length=256, null=True, validators=[src.users.models.validate_image_file_extension]),
        ),
        migrations.AlterField(
            model_name='user',
            name='date_joined',
            field=models.CharField(default=datetime.datetime(2024, 5, 16, 9, 16, 45, 151298), max_length=50, null=True),
        ),
    ]
