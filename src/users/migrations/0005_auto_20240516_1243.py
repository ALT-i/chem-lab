# Generated by Django 3.2.12 on 2024-05-16 12:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20240516_0916'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='office',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='title',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='date_joined',
            field=models.CharField(default=datetime.datetime(2024, 5, 16, 12, 43, 27, 420470), max_length=50, null=True),
        ),
    ]
