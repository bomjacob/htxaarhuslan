# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-08 09:02
from __future__ import unicode_literals

from django.db import migrations
import main.models
import main.storage
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_auto_20161205_2209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='photo',
            field=sorl.thumbnail.fields.ImageField(blank=True, storage=main.storage.OverwriteStorage(), upload_to=main.models.profile_picture_path, verbose_name='billede'),
        ),
    ]
