# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0019_delete_filter'),
        ('wagtailcore', '0040_page_draft_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasicArticlePage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('body', wagtail.wagtailcore.fields.RichTextField()),
                ('image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailimages.Image', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
