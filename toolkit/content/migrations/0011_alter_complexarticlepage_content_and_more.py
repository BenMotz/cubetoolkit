# Generated by Django 4.0.10 on 2024-11-03 18:37

from django.db import migrations, models
import wagtail.blocks
import wagtail.contrib.forms.models
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0010_basicarticlepage_show_on_programme_page"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complexarticlepage",
            name="content",
            field=wagtail.fields.StreamField(
                [
                    (
                        "content_block",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "width",
                                    wagtail.blocks.IntegerBlock(
                                        help_text="How many grid columns to occupy in rendered template",
                                        max_value=5,
                                        min_value=1,
                                    ),
                                ),
                                (
                                    "content",
                                    wagtail.blocks.StreamBlock(
                                        [
                                            (
                                                "rich_text",
                                                wagtail.blocks.RichTextBlock(),
                                            ),
                                            (
                                                "raw_html",
                                                wagtail.blocks.RawHTMLBlock(),
                                            ),
                                            (
                                                "image",
                                                wagtail.images.blocks.ImageChooserBlock(),
                                            ),
                                        ],
                                        max_num=1,
                                        min_num=1,
                                    ),
                                ),
                            ]
                        ),
                    )
                ],
                use_json_field=True,
            ),
        ),
        migrations.AlterField(
            model_name="emailformpage",
            name="from_address",
            field=models.EmailField(
                blank=True, max_length=255, verbose_name="from address"
            ),
        ),
        migrations.AlterField(
            model_name="emailformpage",
            name="to_address",
            field=models.CharField(
                blank=True,
                help_text="Optional - form submissions will be emailed to these addresses. Separate multiple addresses by comma.",
                max_length=255,
                validators=[wagtail.contrib.forms.models.validate_to_address],
                verbose_name="to address",
            ),
        ),
        migrations.AlterField(
            model_name="formfield",
            name="choices",
            field=models.TextField(
                blank=True,
                help_text="Comma or new line separated list of choices. Only applicable in checkboxes, radio and dropdown.",
                verbose_name="choices",
            ),
        ),
        migrations.AlterField(
            model_name="formfield",
            name="default_value",
            field=models.TextField(
                blank=True,
                help_text="Default value. Comma or new line separated values supported for checkboxes.",
                verbose_name="default value",
            ),
        ),
    ]
