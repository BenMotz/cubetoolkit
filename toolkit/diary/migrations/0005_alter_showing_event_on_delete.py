# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("diary", "0004_eventtag_ordering_and_promoted"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="template",
            field=models.ForeignKey(
                related_name="template",
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name="Event Type",
                blank=True,
                to="diary.EventTemplate",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="showing",
            name="room",
            field=models.ForeignKey(
                related_name="showings",
                on_delete=django.db.models.deletion.SET_NULL,
                to="diary.Room",
                null=True,
            ),
        ),
    ]
