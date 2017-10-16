# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0002_add_room'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='colour',
            field=models.CharField(default='#33CC33', max_length=9),
        ),
    ]
