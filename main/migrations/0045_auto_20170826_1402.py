# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-26 12:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0044_profile_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lan',
            name='payment_manager_id',
            field=models.CharField(blank=True, help_text='Unik token som indentificerer hvorbetalingsforespørgelser skal sendes.', max_length=255, null=True, verbose_name='Payment Manager id'),
        ),
    ]