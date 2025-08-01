# Generated by Django 1.11.7 on 2017-11-22 17:14

from django.db import migrations, models
import toolkit.members.models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0003_auto_20171107_1609"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="membership_expires",
            field=models.DateField(
                blank=True,
                default=toolkit.members.models.get_default_membership_expiry,
                null=True,
            ),
        ),
    ]
