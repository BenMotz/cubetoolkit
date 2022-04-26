# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-23 21:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("diary", "0006_auto_20171107_1609"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="notes",
            field=models.TextField(
                blank=True,
                max_length=4096,
                null=True,
                verbose_name="Programmer's notes",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="terms",
            field=models.TextField(
                blank=True,
                default="Contacts-\nCompany-\nAddress-\nEmail-\nPh No-\nHire Fee (inclusive of VAT, if applicable) -\nFinancial Deal (%/fee/split etc)-\nDeposit paid before the night (p/h only) -\nAmount needed to be collected (p/h only) -\nSpecial Terms -\nTech needed -\nAdditional Info -",
                max_length=4096,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="mediaitem",
            name="media_file",
            field=models.ImageField(
                blank=True,
                max_length=256,
                null=True,
                upload_to="diary",
                verbose_name="Image file",
            ),
        ),
        migrations.AlterField(
            model_name="printedprogramme",
            name="programme",
            field=models.FileField(
                max_length=256,
                upload_to="printedprogramme",
                verbose_name="Programme PDF",
            ),
        ),
        migrations.AlterField(
            model_name="role",
            name="standard",
            field=models.BooleanField(
                default=False,
                help_text="Should this role be presented in the main list of roles for events",
            ),
        ),
    ]
