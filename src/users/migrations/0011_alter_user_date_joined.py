# Generated by Django 3.2.12 on 2024-05-21 01:10

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_alter_user_date_joined'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='date_joined',
            field=models.CharField(default=datetime.datetime(2024, 5, 21, 1, 9, 21, 345341), max_length=50, null=True),
        ),
    ]