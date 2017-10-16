# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0003_room_colour'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventtag',
            name='promoted',
            field=models.BooleanField(default=False),
        ),
    ]
