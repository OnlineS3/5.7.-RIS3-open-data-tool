# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-06-19 15:12
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('OpenDataTool', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='organisation',
            old_name='organizationID',
            new_name='id',
        ),
    ]
