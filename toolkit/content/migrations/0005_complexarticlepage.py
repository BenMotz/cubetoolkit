# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.fields
import wagtail.wagtailcore.blocks


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0040_page_draft_title"),
        ("content", "0004_emailformpage_formfield"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplexArticlePage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "content",
                    wagtail.wagtailcore.fields.StreamField(
                        [
                            (
                                b"content_block",
                                wagtail.wagtailcore.blocks.StructBlock(
                                    [
                                        (
                                            b"width",
                                            wagtail.wagtailcore.blocks.IntegerBlock(
                                                help_text=b"How many grid columns to occupy in rendered template",
                                                max_value=5,
                                                min_value=1,
                                            ),
                                        ),
                                        (
                                            b"content",
                                            wagtail.wagtailcore.blocks.StreamBlock(
                                                [
                                                    (
                                                        b"rich_text",
                                                        wagtail.wagtailcore.blocks.RichTextBlock(),
                                                    ),
                                                    (
                                                        b"raw_html",
                                                        wagtail.wagtailcore.blocks.RawHTMLBlock(),
                                                    ),
                                                    (
                                                        b"image",
                                                        wagtail.wagtailimages.blocks.ImageChooserBlock(),
                                                    ),
                                                ],
                                                min_num=1,
                                                max_num=1,
                                            ),
                                        ),
                                    ]
                                ),
                            )
                        ]
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
    ]
