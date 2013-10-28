# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Volunteer.portrait_thumb'
        db.delete_column('Volunteers', 'portrait_thumb')


    def backwards(self, orm):
        # Adding field 'Volunteer.portrait_thumb'
        db.add_column('Volunteers', 'portrait_thumb',
                      self.gf('django.db.models.fields.files.ImageField')(max_length=256, null=True, blank=True),
                      keep_default=False)


    models = {
        u'diary.role': {
            'Meta': {'ordering': "['name']", 'object_name': 'Role', 'db_table': "'Roles'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'read_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'standard': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'members.member': {
            'Meta': {'object_name': 'Member', 'db_table': "'Members'"},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'altphone': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_member': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mailout': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mailout_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mailout_key': ('django.db.models.fields.CharField', [], {'default': "'OE1oxmuSf2esb1XIho0B9RtRfn9vNgfb'", 'max_length': '32'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'posttown': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        u'members.volunteer': {
            'Meta': {'object_name': 'Volunteer', 'db_table': "'Volunteers'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'volunteer'", 'unique': 'True', 'to': u"orm['members.Member']"}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'portrait': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['diary.Role']", 'symmetrical': 'False', 'db_table': "'Volunteer_Roles'", 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['members']