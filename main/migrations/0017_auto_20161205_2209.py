# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-05 21:09
from __future__ import unicode_literals

from django.db import migrations, models
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_auto_20161204_1654'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lan',
            name='paytypes',
            field=main.models.ChoiceArrayField(base_field=models.CharField(choices=[('mp', 'MobilePay'), ('cash', 'Kontant')], max_length=127), null=True, size=None, verbose_name='betalingstyper'),
        ),
        migrations.AlterField(
            model_name='lanprofile',
            name='paid',
            field=models.NullBooleanField(verbose_name='betalt?'),
        ),
        migrations.AlterField(
            model_name='lanprofile',
            name='paytype',
            field=models.CharField(blank=True, choices=[('mp', 'MobilePay'), ('cash', 'Kontant')], max_length=255, null=True, verbose_name='betalingstype'),
        ),
    ]
