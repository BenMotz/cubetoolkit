# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0003_room_colour'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventtag',
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.AddField(
            model_name='eventtag',
            name='promoted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='eventtag',
            name='sort_order',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
