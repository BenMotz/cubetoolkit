# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.core.fields
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0019_delete_filter"),
        ("wagtailcore", "0040_page_draft_title"),
    ]

    operations = [
        migrations.CreateModel(
            name="BasicArticlePage",
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
                ("body", wagtail.core.fields.RichTextField()),
                (
                    "image_alignment",
                    models.CharField(
                        default=b"L",
                        max_length=3,
                        choices=[(b"L", b"Left"), (b"R", b"Right")],
                    ),
                ),
                (
                    "image",
                    models.ForeignKey(
                        related_name="+",
                        on_delete=django.db.models.deletion.SET_NULL,
                        blank=True,
                        to="wagtailimages.Image",
                        null=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="ImageGalleryImage",
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
                (
                    "sort_order",
                    models.IntegerField(null=True, editable=False, blank=True),
                ),
                ("caption", models.CharField(max_length=255, blank=True)),
                (
                    "image",
                    models.ForeignKey(
                        related_name="+",
                        to="wagtailimages.Image",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ImageGalleryPage",
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
                ("intro_text", wagtail.core.fields.RichTextField(blank=True)),
                ("footer_text", wagtail.core.fields.RichTextField(blank=True)),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.AddField(
            model_name="imagegalleryimage",
            name="page",
            field=modelcluster.fields.ParentalKey(
                related_name="gallery_images", to="content.ImageGalleryPage"
            ),
        ),
    ]
