# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0005_alter_showing_event_on_delete'),
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True,
                                        primary_key=True)),
                ('training_date', models.DateField(
                    default=datetime.date.today)),
                ('trainer', models.CharField(max_length=128)),
                ('notes', models.TextField(blank=True)),
                ('role', models.ForeignKey(
                    related_name='training_records', to='diary.Role')),
                ('volunteer', models.ForeignKey(
                    related_name='training_records', to='members.Volunteer')),
            ],
            options={
                'ordering': ['role', 'training_date', 'volunteer'],
                'db_table': 'TrainingRecords',
            },
        ),
    ]
