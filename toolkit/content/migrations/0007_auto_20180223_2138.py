# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-23 21:38
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0006_change_link_field_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="basicarticlepage",
            name="image_alignment",
            field=models.CharField(
                choices=[("L", "Left"), ("C", "Centre"), ("R", "Right")],
                default="L",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="complexarticlepage",
            name="content",
            field=wagtail.core.fields.StreamField(
                (
                    (
                        "content_block",
                        wagtail.core.blocks.StructBlock(
                            (
                                (
                                    "width",
                                    wagtail.core.blocks.IntegerBlock(
                                        help_text="How many grid columns to occupy in rendered template",
                                        max_value=5,
                                        min_value=1,
                                    ),
                                ),
                                (
                                    "content",
                                    wagtail.core.blocks.StreamBlock(
                                        (
                                            (
                                                "rich_text",
                                                wagtail.core.blocks.RichTextBlock(),
                                            ),
                                            (
                                                "raw_html",
                                                wagtail.core.blocks.RawHTMLBlock(),
                                            ),
                                            (
                                                "image",
                                                wagtail.images.blocks.ImageChooserBlock(),
                                            ),
                                        ),
                                        max_num=1,
                                        min_num=1,
                                    ),
                                ),
                            )
                        ),
                    ),
                )
            ),
        ),
    ]
