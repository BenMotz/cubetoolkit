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
        ("content", "0003_auto_20171005_1125"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailFormPage",
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
                    "to_address",
                    models.CharField(
                        help_text="Optional - form submissions will be emailed to these addresses. Separate multiple addresses by comma.",
                        max_length=255,
                        verbose_name="to address",
                        blank=True,
                    ),
                ),
                (
                    "from_address",
                    models.CharField(
                        max_length=255, verbose_name="from address", blank=True
                    ),
                ),
                (
                    "subject",
                    models.CharField(
                        max_length=255, verbose_name="subject", blank=True
                    ),
                ),
                ("intro", wagtail.core.fields.RichTextField(blank=True)),
                (
                    "thank_you_text",
                    wagtail.core.fields.RichTextField(blank=True),
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
            name="FormField",
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
                (
                    "label",
                    models.CharField(
                        help_text="The label of the form field",
                        max_length=255,
                        verbose_name="label",
                    ),
                ),
                (
                    "field_type",
                    models.CharField(
                        max_length=16,
                        verbose_name="field type",
                        choices=[
                            ("singleline", "Single line text"),
                            ("multiline", "Multi-line text"),
                            ("email", "Email"),
                            ("number", "Number"),
                            ("url", "URL"),
                            ("checkbox", "Checkbox"),
                            ("checkboxes", "Checkboxes"),
                            ("dropdown", "Drop down"),
                            ("multiselect", "Multiple select"),
                            ("radio", "Radio buttons"),
                            ("date", "Date"),
                            ("datetime", "Date/time"),
                        ],
                    ),
                ),
                (
                    "required",
                    models.BooleanField(default=True, verbose_name="required"),
                ),
                (
                    "choices",
                    models.TextField(
                        help_text="Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.",
                        verbose_name="choices",
                        blank=True,
                    ),
                ),
                (
                    "default_value",
                    models.CharField(
                        help_text="Default value. Comma separated values supported for checkboxes.",
                        max_length=255,
                        verbose_name="default value",
                        blank=True,
                    ),
                ),
                (
                    "help_text",
                    models.CharField(
                        max_length=255, verbose_name="help text", blank=True
                    ),
                ),
                (
                    "page",
                    modelcluster.fields.ParentalKey(
                        related_name="form_fields", to="content.EmailFormPage"
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "abstract": False,
            },
        ),
    ]
