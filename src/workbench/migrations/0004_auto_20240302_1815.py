# Generated by Django 3.2.12 on 2024-03-02 18:15

from django.db import migrations, models
import src.workbench.models


class Migration(migrations.Migration):

    dependencies = [
        ('workbench', '0003_alter_substance_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apparatus',
            name='image',
            field=models.FileField(default='default.png', upload_to='substances', validators=[src.workbench.models.validate_file_extension]),
        ),
        migrations.AlterField(
            model_name='substance',
            name='image',
            field=models.FileField(default='default.png', upload_to='substances', validators=[src.workbench.models.validate_file_extension]),
        ),
    ]
