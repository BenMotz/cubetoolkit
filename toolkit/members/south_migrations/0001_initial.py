# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Member'
        db.create_table('Members', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('posttown', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('postcode', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('website', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('altphone', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('mailout', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('mailout_failed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mailout_key', self.gf('django.db.models.fields.CharField')(default='JuiQ1lu6xUArtTbWLY9AUQIhs1gXWaVj', max_length=32)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('members', ['Member'])

        # Adding model 'Volunteer'
        db.create_table('Volunteers', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.OneToOneField')(related_name='volunteer', unique=True, to=orm['members.Member'])),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('portrait', self.gf('django.db.models.fields.files.ImageField')(max_length=256, null=True, blank=True)),
            ('portrait_thumb', self.gf('django.db.models.fields.files.ImageField')(max_length=256, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('members', ['Volunteer'])

        # Adding M2M table for field roles on 'Volunteer'
        db.create_table('Volunteer_Roles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('volunteer', models.ForeignKey(orm['members.volunteer'], null=False)),
            ('role', models.ForeignKey(orm['diary.role'], null=False))
        ))
        db.create_unique('Volunteer_Roles', ['volunteer_id', 'role_id'])


    def backwards(self, orm):
        # Deleting model 'Member'
        db.delete_table('Members')

        # Deleting model 'Volunteer'
        db.delete_table('Volunteers')

        # Removing M2M table for field roles on 'Volunteer'
        db.delete_table('Volunteer_Roles')


    models = {
        'diary.role': {
            'Meta': {'ordering': "['name']", 'object_name': 'Role', 'db_table': "'Roles'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'read_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'standard': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'members.member': {
            'Meta': {'object_name': 'Member', 'db_table': "'Members'"},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'altphone': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailout': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mailout_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mailout_key': ('django.db.models.fields.CharField', [], {'default': "'tgpvDVPtYXjQBnyob0cVSrq5TXvScbz1'", 'max_length': '32'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'posttown': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'members.volunteer': {
            'Meta': {'object_name': 'Volunteer', 'db_table': "'Volunteers'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'volunteer'", 'unique': 'True', 'to': "orm['members.Member']"}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'portrait': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'portrait_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['diary.Role']", 'symmetrical': 'False', 'db_table': "'Volunteer_Roles'", 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['members']