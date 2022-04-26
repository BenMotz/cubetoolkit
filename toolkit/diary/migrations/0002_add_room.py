# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("diary", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Room",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=64)),
            ],
            options={
                "db_table": "Rooms",
            },
        ),
        migrations.AddField(
            model_name="showing",
            name="room",
            field=models.ForeignKey(
                related_name="showings",
                to="diary.Room",
                null=True,
                on_delete=models.SET_NULL,
            ),
        ),
    ]
