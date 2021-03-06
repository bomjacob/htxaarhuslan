# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-17 20:45
from __future__ import unicode_literals

from django.db import migrations, models
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_auto_20161110_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='grade',
            field=models.CharField(choices=[('16xaa', '16xaa'), ('16xab', '16xab'), ('16xac', '16xac'), ('16xad', '16xad'), ('16xar', '16xar'), ('16xaj', '16xaj'), ('13xa', '13xa'), ('14xaa', '14xaa'), ('14xab', '14xab'), ('14xac', '14xac'), ('14xad', '14xad'), ('14xar', '14xar'), ('14xaj', '14xaj'), ('15xaa', '15xaa'), ('15xab', '15xab'), ('15xac', '15xac'), ('15xad', '15xad'), ('15xar', '15xar'), ('15xaj', '15xaj'), ('teacher', 'Lærer'), ('none', 'Ukendt')], default='none', max_length=32, verbose_name='klasse'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='photo',
            field=models.ImageField(blank=True, upload_to=main.models.profile_picture_path, verbose_name='billede'),
        ),
    ]
