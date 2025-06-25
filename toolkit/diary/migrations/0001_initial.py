from django.db import models, migrations
import toolkit.diary.models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DiaryIdea",
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
                ("month", models.DateField(editable=False)),
                (
                    "ideas",
                    models.TextField(max_length=16384, null=True, blank=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "DiaryIdeas",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Event",
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
                ("name", models.CharField(max_length=256)),
                ("pre_title", models.CharField(max_length=256, blank=True)),
                ("post_title", models.CharField(max_length=256, blank=True)),
                (
                    "legacy_id",
                    models.CharField(
                        max_length=256, null=True, editable=False
                    ),
                ),
                ("duration", models.TimeField(null=True)),
                ("outside_hire", models.BooleanField(default=False)),
                ("private", models.BooleanField(default=False)),
                ("pricing", models.CharField(max_length=256, blank=True)),
                ("ticket_link", models.URLField(max_length=256, blank=True)),
                (
                    "film_information",
                    models.CharField(max_length=256, blank=True),
                ),
                (
                    "copy",
                    models.TextField(max_length=8192, null=True, blank=True),
                ),
                (
                    "copy_summary",
                    models.TextField(max_length=4096, null=True, blank=True),
                ),
                (
                    "legacy_copy",
                    models.BooleanField(default=False, editable=False),
                ),
                (
                    "terms",
                    models.TextField(
                        default=b"Contacts-\nCompany-\nAddress-\nEmail-\nPh No-\nHire Fee (inclusive of VAT, if applicable) -\nFinancial Deal (%/fee/split etc)-\nDeposit paid before the night (p/h only) -\nAmount needed to be collected (p/h only) -\nSpecial Terms -\nTech needed -\nAdditional Info -",
                        max_length=4096,
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        max_length=4096,
                        null=True,
                        verbose_name=b"Programmer's notes",
                        blank=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "Events",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="EventTag",
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
                ("name", models.CharField(unique=True, max_length=32)),
                ("slug", models.SlugField(unique=True)),
                (
                    "read_only",
                    models.BooleanField(default=False, editable=False),
                ),
            ],
            options={
                "ordering": ["name"],
                "db_table": "EventTags",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="EventTemplate",
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
                ("name", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("pricing", models.CharField(max_length=256, blank=True)),
            ],
            options={
                "ordering": ["name"],
                "db_table": "EventTemplates",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MediaItem",
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
                    "media_file",
                    models.ImageField(
                        max_length=256,
                        upload_to=b"diary",
                        null=True,
                        verbose_name=b"Image file",
                        blank=True,
                    ),
                ),
                ("mimetype", models.CharField(max_length=64, editable=False)),
                (
                    "credit",
                    models.CharField(
                        default=b"Internet scavenged",
                        max_length=256,
                        null=True,
                        verbose_name=b"Image credit",
                        blank=True,
                    ),
                ),
                (
                    "caption",
                    models.CharField(max_length=256, null=True, blank=True),
                ),
            ],
            options={
                "db_table": "MediaItems",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PrintedProgramme",
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
                ("month", models.DateField(unique=True, editable=False)),
                (
                    "programme",
                    models.FileField(
                        upload_to=b"printedprogramme",
                        max_length=256,
                        verbose_name=b"Programme PDF",
                    ),
                ),
                (
                    "designer",
                    models.CharField(max_length=256, null=True, blank=True),
                ),
                (
                    "notes",
                    models.TextField(max_length=8192, null=True, blank=True),
                ),
            ],
            options={
                "db_table": "PrintedProgrammes",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Role",
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
                ("name", models.CharField(unique=True, max_length=64)),
                (
                    "standard",
                    models.BooleanField(
                        default=False,
                        help_text=b"Should this role be presented in the main list of roles for events",
                    ),
                ),
                ("read_only", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["name"],
                "db_table": "Roles",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="RotaEntry",
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
                ("required", models.BooleanField(default=True)),
                ("rank", models.IntegerField(default=1)),
                ("name", models.TextField(max_length=256, blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "role",
                    models.ForeignKey(
                        to="diary.Role", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "ordering": ["role", "rank"],
                "db_table": "RotaEntries",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Showing",
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
                    "start",
                    toolkit.diary.models.FutureDateTimeField(db_index=True),
                ),
                ("booked_by", models.CharField(max_length=64)),
                (
                    "extra_copy",
                    models.TextField(max_length=4096, null=True, blank=True),
                ),
                (
                    "extra_copy_summary",
                    models.TextField(max_length=4096, null=True, blank=True),
                ),
                ("confirmed", models.BooleanField(default=False)),
                ("hide_in_programme", models.BooleanField(default=False)),
                ("cancelled", models.BooleanField(default=False)),
                ("discounted", models.BooleanField(default=False)),
                ("sold_out", models.BooleanField(default=False)),
                ("rota_notes", models.TextField(max_length=1024, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.ForeignKey(
                        related_name="showings",
                        to="diary.Event",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "roles",
                    models.ManyToManyField(
                        to="diary.Role", through="diary.RotaEntry"
                    ),
                ),
            ],
            options={
                "ordering": ["start"],
                "db_table": "Showings",
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="rotaentry",
            name="showing",
            field=models.ForeignKey(
                to="diary.Showing", on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="eventtemplate",
            name="roles",
            field=models.ManyToManyField(
                to="diary.Role", db_table="EventTemplates_Roles"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="eventtemplate",
            name="tags",
            field=models.ManyToManyField(
                to="diary.EventTag", db_table="EventTemplate_Tags", blank=True
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="event",
            name="media",
            field=models.ManyToManyField(
                to="diary.MediaItem", db_table="Event_MediaItems"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="event",
            name="tags",
            field=models.ManyToManyField(
                to="diary.EventTag", db_table="Event_Tags", blank=True
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="event",
            name="template",
            field=models.ForeignKey(
                related_name="template",
                verbose_name=b"Event Type",
                blank=True,
                to="diary.EventTemplate",
                null=True,
                on_delete=models.SET_NULL,
            ),
            preserve_default=True,
        ),
    ]
