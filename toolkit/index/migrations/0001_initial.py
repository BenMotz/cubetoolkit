# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'IndexLink'
        db.create_table('IndexLinks', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=1024)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='links', to=orm['index.IndexCategory'])),
        ))
        db.send_create_signal(u'index', ['IndexLink'])

        # Adding model 'IndexCategory'
        db.create_table('IndexLinkCategories', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal(u'index', ['IndexCategory'])


    def backwards(self, orm):
        # Deleting model 'IndexLink'
        db.delete_table('IndexLinks')

        # Deleting model 'IndexCategory'
        db.delete_table('IndexLinkCategories')


    models = {
        u'index.indexcategory': {
            'Meta': {'object_name': 'IndexCategory', 'db_table': "'IndexLinkCategories'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'index.indexlink': {
            'Meta': {'ordering': "['category']", 'object_name': 'IndexLink', 'db_table': "'IndexLinks'"},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': u"orm['index.IndexCategory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        }
    }

    complete_apps = ['index']