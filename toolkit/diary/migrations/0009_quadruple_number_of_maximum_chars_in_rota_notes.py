# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-01-14 19:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0008_remove_terms_from_event_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='showing',
            name='rota_notes',
            field=models.TextField(blank=True, max_length=4096),
        ),
    ]