# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-08 12:05
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20161106_1720'),
    ]

    operations = [
        migrations.AddField(
            model_name='lan',
            name='open',
            field=models.DateTimeField(default=datetime.datetime(2016, 12, 1, 0, 0)),
        ),
    ]
