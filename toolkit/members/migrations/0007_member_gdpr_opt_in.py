# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-15 22:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_auto_20180223_2138'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='gdpr_opt_in',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]