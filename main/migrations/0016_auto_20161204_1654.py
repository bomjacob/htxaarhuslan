# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-04 15:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_auto_20161202_1807'),
    ]

    operations = [
        migrations.AddField(
            model_name='lanprofile',
            name='paid',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='lanprofile',
            name='paytype',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='betalingstype'),
        ),
        migrations.AlterField(
            model_name='lan',
            name='paytypes',
            field=models.CharField(max_length=255, null=True, verbose_name='betalingstyper'),
        ),
        migrations.AlterField(
            model_name='lan',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True, verbose_name='pris'),
        ),
    ]
