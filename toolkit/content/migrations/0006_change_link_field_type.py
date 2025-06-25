from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0005_complexarticlepage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sectionlink",
            name="link",
            field=models.CharField(max_length=1024),
        ),
    ]
