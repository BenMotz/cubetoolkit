from django.db import models, migrations
import toolkit.util


class Migration(migrations.Migration):

    dependencies = [
        ("diary", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Member",
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
                ("number", models.CharField(max_length=10, editable=False)),
                ("name", models.CharField(max_length=64)),
                (
                    "email",
                    models.EmailField(max_length=64, null=True, blank=True),
                ),
                (
                    "address",
                    models.CharField(max_length=128, null=True, blank=True),
                ),
                (
                    "posttown",
                    models.CharField(max_length=64, null=True, blank=True),
                ),
                (
                    "postcode",
                    models.CharField(max_length=16, null=True, blank=True),
                ),
                (
                    "country",
                    models.CharField(max_length=32, null=True, blank=True),
                ),
                (
                    "website",
                    models.CharField(max_length=128, null=True, blank=True),
                ),
                (
                    "phone",
                    models.CharField(max_length=64, null=True, blank=True),
                ),
                (
                    "altphone",
                    models.CharField(max_length=64, null=True, blank=True),
                ),
                ("notes", models.TextField(null=True, blank=True)),
                ("is_member", models.BooleanField(default=True)),
                ("mailout", models.BooleanField(default=True)),
                ("mailout_failed", models.BooleanField(default=False)),
                (
                    "mailout_key",
                    models.CharField(
                        default=toolkit.util.generate_random_string,
                        max_length=32,
                        editable=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "Members",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Volunteer",
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
                ("notes", models.TextField(null=True, blank=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "portrait",
                    models.ImageField(
                        max_length=256,
                        null=True,
                        upload_to=b"volunteers",
                        blank=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "member",
                    models.OneToOneField(
                        related_name="volunteer",
                        to="members.Member",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "roles",
                    models.ManyToManyField(
                        to="diary.Role", db_table="Volunteer_Roles", blank=True
                    ),
                ),
            ],
            options={
                "db_table": "Volunteers",
            },
            bases=(models.Model,),
        ),
    ]
