# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-27 16:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OpenDataTool', '0004_auto_20170427_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisation',
            name='projectRcn',
            field=models.IntegerField(),
        ),
    ]
