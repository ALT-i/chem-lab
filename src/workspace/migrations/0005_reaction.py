# Generated by Django 3.2.12 on 2023-12-10 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0004_delete_reaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('substance', models.JSONField()),
                ('volume', models.JSONField()),
            ],
        ),
    ]
