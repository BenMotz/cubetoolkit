# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.core.fields
import wagtail.core.blocks


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
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "content",
                    wagtail.core.fields.StreamField(
                        [
                            (
                                b"content_block",
                                wagtail.core.blocks.StructBlock(
                                    [
                                        (
                                            b"width",
                                            wagtail.core.blocks.IntegerBlock(
                                                help_text=b"How many grid columns to occupy in rendered template",
                                                max_value=5,
                                                min_value=1,
                                            ),
                                        ),
                                        (
                                            b"content",
                                            wagtail.core.blocks.StreamBlock(
                                                [
                                                    (
                                                        b"rich_text",
                                                        wagtail.core.blocks.RichTextBlock(),
                                                    ),
                                                    (
                                                        b"raw_html",
                                                        wagtail.core.blocks.RawHTMLBlock(),
                                                    ),
                                                    (
                                                        b"image",
                                                        wagtail.images.blocks.ImageChooserBlock(),
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
