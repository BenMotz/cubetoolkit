from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="IndexCategory",
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
                ("name", models.CharField(max_length=1024)),
            ],
            options={
                "db_table": "IndexLinkCategories",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="IndexLink",
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
                ("text", models.CharField(max_length=1024, blank=True)),
                ("link", models.URLField(max_length=1024)),
                (
                    "category",
                    models.ForeignKey(
                        related_name="links",
                        verbose_name=b"Link category",
                        to="index.IndexCategory",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["category"],
                "db_table": "IndexLinks",
            },
            bases=(models.Model,),
        ),
    ]
