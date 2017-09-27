# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_basicarticlepage_image_alignment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basicarticlepage',
            name='image_alignment',
            field=models.CharField(default=b'L', max_length=3, choices=[(b'L', b'Left'), (b'R', b'Right')]),
        ),
    ]
