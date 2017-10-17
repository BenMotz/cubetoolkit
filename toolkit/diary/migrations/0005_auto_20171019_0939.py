# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0004_eventtag_promoted'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventtag',
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.AddField(
            model_name='eventtag',
            name='sort_order',
            field=models.IntegerField(null=True, editable=False, blank=True),
        ),
    ]
