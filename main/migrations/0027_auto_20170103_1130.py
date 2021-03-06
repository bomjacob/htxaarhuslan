# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-03 10:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_auto_20161215_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='lan',
            name='show_calendar',
            field=models.BooleanField(default=False, help_text='Hvorvidt en kalender skal vises på forsiden. Slå kun dette til hvis turneringer og andre events efterhånden er ved at være klar.', verbose_name='Vis kalender'),
        ),
        migrations.AddField(
            model_name='tournament',
            name='end',
            field=models.DateTimeField(null=True, verbose_name='Slut'),
        ),
        migrations.AddField(
            model_name='tournament',
            name='start',
            field=models.DateTimeField(null=True, verbose_name='Start'),
        ),
    ]
