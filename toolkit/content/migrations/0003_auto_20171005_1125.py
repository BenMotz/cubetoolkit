from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0002_auto_20171002_1052"),
    ]

    operations = [
        migrations.AlterField(
            model_name="basicarticlepage",
            name="image_alignment",
            field=models.CharField(
                default=b"L",
                max_length=3,
                choices=[(b"L", b"Left"), (b"C", b"Centre"), (b"R", b"Right")],
            ),
        ),
    ]
