# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-10-18 16:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0003_room_colour'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='template', to='diary.EventTemplate', verbose_name='Event Type'),
        ),
        migrations.AlterField(
            model_name='showing',
            name='room',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='showings', to='diary.Room'),
        ),
    ]
