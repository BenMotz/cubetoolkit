# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Role'
        db.create_table('Roles', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('standard', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('read_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('diary', ['Role'])

        # Adding model 'MediaItem'
        db.create_table('MediaItems', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('media_file', self.gf('django.db.models.fields.files.FileField')(max_length=256, null=True, blank=True)),
            ('mimetype', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=256, null=True, blank=True)),
            ('credit', self.gf('django.db.models.fields.CharField')(default='Internet scavenged', max_length=256, null=True, blank=True)),
            ('caption', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
        ))
        db.send_create_signal('diary', ['MediaItem'])

        # Adding model 'EventTag'
        db.create_table('EventTags', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('read_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('diary', ['EventTag'])

        # Adding model 'Event'
        db.create_table('Events', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('legacy_id', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='template', null=True, to=orm['diary.EventTemplate'])),
            ('duration', self.gf('django.db.models.fields.TimeField')(null=True)),
            ('cancelled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('outside_hire', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('private', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('copy', self.gf('django.db.models.fields.TextField')(max_length=8192, null=True, blank=True)),
            ('copy_summary', self.gf('django.db.models.fields.TextField')(max_length=4096, null=True, blank=True)),
            ('legacy_copy', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('terms', self.gf('django.db.models.fields.TextField')(default='Contacts-\nCompany-\nAddress-\nEmail-\nPh No-\nHire Fee (inclusive of VAT, if applicable) -\nFinancial Deal (%/fee/split etc)-\nDeposit paid before the night (p/h only) -\nAmount needed to be collected (p/h only) -\nSpecial Terms -\nTech needed -\nAdditonal Info -', max_length=4096, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(max_length=4096, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('diary', ['Event'])

        # Adding M2M table for field tags on 'Event'
        db.create_table('Event_Tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('event', models.ForeignKey(orm['diary.event'], null=False)),
            ('eventtag', models.ForeignKey(orm['diary.eventtag'], null=False))
        ))
        db.create_unique('Event_Tags', ['event_id', 'eventtag_id'])

        # Adding M2M table for field media on 'Event'
        db.create_table('Event_MediaItems', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('event', models.ForeignKey(orm['diary.event'], null=False)),
            ('mediaitem', models.ForeignKey(orm['diary.mediaitem'], null=False))
        ))
        db.create_unique('Event_MediaItems', ['event_id', 'mediaitem_id'])

        # Adding model 'Showing'
        db.create_table('Showings', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='showings', to=orm['diary.Event'])),
            ('start', self.gf('toolkit.diary.models.FutureDateTimeField')()),
            ('booked_by', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('extra_copy', self.gf('django.db.models.fields.TextField')(max_length=4096, null=True, blank=True)),
            ('extra_copy_summary', self.gf('django.db.models.fields.TextField')(max_length=4096, null=True, blank=True)),
            ('confirmed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('hide_in_programme', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('cancelled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('discounted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('diary', ['Showing'])

        # Adding model 'DiaryIdea'
        db.create_table('DiaryIdeas', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('month', self.gf('django.db.models.fields.DateField')()),
            ('ideas', self.gf('django.db.models.fields.TextField')(max_length=16384, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('diary', ['DiaryIdea'])

        # Adding model 'EventTemplate'
        db.create_table('EventTemplates', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('diary', ['EventTemplate'])

        # Adding M2M table for field roles on 'EventTemplate'
        db.create_table('EventTemplates_Roles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eventtemplate', models.ForeignKey(orm['diary.eventtemplate'], null=False)),
            ('role', models.ForeignKey(orm['diary.role'], null=False))
        ))
        db.create_unique('EventTemplates_Roles', ['eventtemplate_id', 'role_id'])

        # Adding M2M table for field tags on 'EventTemplate'
        db.create_table('EventTemplate_Tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eventtemplate', models.ForeignKey(orm['diary.eventtemplate'], null=False)),
            ('eventtag', models.ForeignKey(orm['diary.eventtag'], null=False))
        ))
        db.create_unique('EventTemplate_Tags', ['eventtemplate_id', 'eventtag_id'])

        # Adding model 'RotaEntry'
        db.create_table('RotaEntries', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diary.Role'])),
            ('showing', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['diary.Showing'])),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('rank', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('diary', ['RotaEntry'])


    def backwards(self, orm):
        # Deleting model 'Role'
        db.delete_table('Roles')

        # Deleting model 'MediaItem'
        db.delete_table('MediaItems')

        # Deleting model 'EventTag'
        db.delete_table('EventTags')

        # Deleting model 'Event'
        db.delete_table('Events')

        # Removing M2M table for field tags on 'Event'
        db.delete_table('Event_Tags')

        # Removing M2M table for field media on 'Event'
        db.delete_table('Event_MediaItems')

        # Deleting model 'Showing'
        db.delete_table('Showings')

        # Deleting model 'DiaryIdea'
        db.delete_table('DiaryIdeas')

        # Deleting model 'EventTemplate'
        db.delete_table('EventTemplates')

        # Removing M2M table for field roles on 'EventTemplate'
        db.delete_table('EventTemplates_Roles')

        # Removing M2M table for field tags on 'EventTemplate'
        db.delete_table('EventTemplate_Tags')

        # Deleting model 'RotaEntry'
        db.delete_table('RotaEntries')


    models = {
        'diary.diaryidea': {
            'Meta': {'object_name': 'DiaryIdea', 'db_table': "'DiaryIdeas'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ideas': ('django.db.models.fields.TextField', [], {'max_length': '16384', 'null': 'True', 'blank': 'True'}),
            'month': ('django.db.models.fields.DateField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'diary.event': {
            'Meta': {'object_name': 'Event', 'db_table': "'Events'"},
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'copy': ('django.db.models.fields.TextField', [], {'max_length': '8192', 'null': 'True', 'blank': 'True'}),
            'copy_summary': ('django.db.models.fields.TextField', [], {'max_length': '4096', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.TimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_copy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'legacy_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'media': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['diary.MediaItem']", 'db_table': "'Event_MediaItems'", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'notes': ('django.db.models.fields.TextField', [], {'max_length': '4096', 'null': 'True', 'blank': 'True'}),
            'outside_hire': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['diary.EventTag']", 'symmetrical': 'False', 'db_table': "'Event_Tags'", 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'template'", 'null': 'True', 'to': "orm['diary.EventTemplate']"}),
            'terms': ('django.db.models.fields.TextField', [], {'default': "'Contacts-\\nCompany-\\nAddress-\\nEmail-\\nPh No-\\nHire Fee (inclusive of VAT, if applicable) -\\nFinancial Deal (%/fee/split etc)-\\nDeposit paid before the night (p/h only) -\\nAmount needed to be collected (p/h only) -\\nSpecial Terms -\\nTech needed -\\nAdditonal Info -'", 'max_length': '4096', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'diary.eventtag': {
            'Meta': {'object_name': 'EventTag', 'db_table': "'EventTags'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'read_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'diary.eventtemplate': {
            'Meta': {'object_name': 'EventTemplate', 'db_table': "'EventTemplates'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['diary.Role']", 'db_table': "'EventTemplates_Roles'", 'symmetrical': 'False'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['diary.EventTag']", 'symmetrical': 'False', 'db_table': "'EventTemplate_Tags'", 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'diary.mediaitem': {
            'Meta': {'object_name': 'MediaItem', 'db_table': "'MediaItems'"},
            'caption': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'credit': ('django.db.models.fields.CharField', [], {'default': "'Internet scavenged'", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'diary.role': {
            'Meta': {'ordering': "['name']", 'object_name': 'Role', 'db_table': "'Roles'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'read_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'standard': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'diary.rotaentry': {
            'Meta': {'object_name': 'RotaEntry', 'db_table': "'RotaEntries'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['diary.Role']"}),
            'showing': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['diary.Showing']"})
        },
        'diary.showing': {
            'Meta': {'object_name': 'Showing', 'db_table': "'Showings'"},
            'booked_by': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'discounted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'showings'", 'to': "orm['diary.Event']"}),
            'extra_copy': ('django.db.models.fields.TextField', [], {'max_length': '4096', 'null': 'True', 'blank': 'True'}),
            'extra_copy_summary': ('django.db.models.fields.TextField', [], {'max_length': '4096', 'null': 'True', 'blank': 'True'}),
            'hide_in_programme': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['diary.Role']", 'through': "orm['diary.RotaEntry']", 'symmetrical': 'False'}),
            'start': ('toolkit.diary.models.FutureDateTimeField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['diary']