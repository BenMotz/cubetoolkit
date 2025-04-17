# Generated by Django 4.2.20 on 2025-04-17 16:53

from django.db import migrations
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_alter_complexarticlepage_content_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complexarticlepage",
            name="content",
            field=wagtail.fields.StreamField(
                [("content_block", 5)],
                block_lookup={
                    0: (
                        "wagtail.blocks.IntegerBlock",
                        (),
                        {
                            "help_text": "How many grid columns to occupy in rendered template",
                            "max_value": 5,
                            "min_value": 1,
                        },
                    ),
                    1: ("wagtail.blocks.RichTextBlock", (), {}),
                    2: ("wagtail.blocks.RawHTMLBlock", (), {}),
                    3: ("wagtail.images.blocks.ImageBlock", [], {}),
                    4: (
                        "wagtail.blocks.StreamBlock",
                        [[("rich_text", 1), ("raw_html", 2), ("image", 3)]],
                        {"max_num": 1, "min_num": 1},
                    ),
                    5: (
                        "wagtail.blocks.StructBlock",
                        [[("width", 0), ("content", 4)]],
                        {},
                    ),
                },
            ),
        ),
    ]
