# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-07 16:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0002_trainingrecord"),
    ]

    operations = [
        migrations.AlterField(
            model_name="member",
            name="address",
            field=models.CharField(blank=True, default="", max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="altphone",
            field=models.CharField(blank=True, default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="country",
            field=models.CharField(blank=True, default="", max_length=32),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="email",
            field=models.EmailField(blank=True, default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="notes",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="postcode",
            field=models.CharField(blank=True, default="", max_length=16),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="posttown",
            field=models.CharField(blank=True, default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="member",
            name="website",
            field=models.CharField(blank=True, default="", max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="volunteer",
            name="notes",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
    ]
