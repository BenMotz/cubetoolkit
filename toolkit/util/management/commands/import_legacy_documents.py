'''Not strictly part of this django suite but appearing in this repo for
completeness.
Suck documents from the psimonkey era Star and Shadow django database
and use wp-cli to load documents as posts in wordpress.
Run initially with --inspect to get a list of document types and authors.
Create the document types as categories and create the wordpress users with
matching names.

'''
import datetime
import os
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import django.utils.timezone
from django.utils.html import strip_tags

import MySQLdb

# Adjust to taste
dbuser = 'starshadow'
dbpass = 'ye2EUsSUCYY8ALx7'
dbdb = 'ssarchive'
wordpress_server = 'xtreamlab.net'
wordpress_path = '/home/marcus/websites/dev.marcusv.org'


class Command(BaseCommand):
    help = "Migrate documents from legacy Star and Shadow web site into wordpress"

    def _conn_to_archive_database(self):
        try:
            self.stdout.write('Connecting to database %s...' % dbdb)
            db = MySQLdb.connect("localhost",
                                 dbuser,
                                 dbpass,
                                 dbdb,
                                 charset='utf8')
            return db
        except MySQLdb.Error as e:
            self.stdout.write(self.style.ERROR(
                'Failed to connect to database %s' % dbdb))

    def _read_archive_db(self, cursor, table):

        # ORDER BY `startDate` DESC"
        sql = "SELECT * FROM `%s`" % table
        # sql = "SELECT * FROM `%s`"#  LIMIT 10" % table
        # sql = "SELECT * FROM `%s` ORDER BY `created` DESC LIMIT 10 OFFSET 10" % table
        rows = cursor.execute(sql)  # returns number of rows
        self.stdout.write('%s: %d rows found' % (table, rows))
        documents = cursor.fetchall()
        return documents

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--inspect',
            action='store_true',
            dest='inspect',
            default=False,
            help='Dry-run, list authors and document types',
        )

        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Spew out more detail',
        )

    def handle(self, *args, **options):

        db = self._conn_to_archive_database()
        cursor = db.cursor()
        doc_types = []
        authors = []

        documents = self._read_archive_db(cursor, 'content_document')

        for document in documents:
            legacy_id = document[0]
            title = document[1]
            title = " ".join(title.split())
            source = document[2]
            source = " ".join(source.split())
            summary = document[3]
            author = document[4].title()
            author = " ".join(author.split())
            created = document[5]
            doc_type = document[6]
            body = document[7]

            # Fix authors
            if author in ['A Neatrour',
                          'Adriin Neatrour',
                          'Adrin Neatrour',
                          'Adrin Netarour',
                          'Adrinneatrour']:
                author = 'Adrin Neatrour'

            if not options['inspect']:
                self.stdout.write('%s "%s" "%s" "%s" %s "%s"' % (
                    legacy_id,
                    title,
                    source,
                    author,
                    created,
                    doc_type
                ))

            body = body.replace("’", "'")
            body = strip_tags(body)

            newbody = ''
            paras = body.split("&nbsp;\n\n")
            for idx, para in enumerate(paras):
                para = para.strip()
                para = para.replace('&nbsp;', ' ')
                if idx != 0:
                    para = ' '.join(para.splitlines())
                if para:
                    # print('Paragraph %d\n\n%s\n' % (idx, para))
                    newbody = ('%s\n\n%s' % (newbody, para))
            # print(newbody)

            shebang = ("wp post create \
                --post_content=\"%s\" \
                --post_date='%s 18:00:00' \
                --post_title='%s' \
                --post_status=Publish \
                --post_excerpt='%s' \
                --user='%s' \
                --post_category=['%s'] \
                --post_mime_type='text/html' \
                --ssh=%s \
                --path=%s" % (
                    newbody,
                    created,
                    title,
                    summary,
                    author,
                    doc_type,
                    wordpress_server,
                    wordpress_path,
                    ))

            if not options['inspect']:
                try:
                    out = subprocess.check_output(shebang,
                                                  shell=True,
                                                  stderr=subprocess.STDOUT)
                    # out is bytes
                    out = str(out, 'utf-8')
                    for line in out.splitlines():
                        print(line)
                except subprocess.CalledProcessError as e:
                    print('%s: %s' % (shebang, str(e.output, 'utf-8')))
                    continue

            if doc_type not in doc_types:
                doc_types.append(doc_type)
            if author not in authors:
                authors.append(author)

        if options['inspect']:

            body = body.replace("’", "'")
            body = strip_tags(body)
            newbody = ''
            paras = body.split("&nbsp;\n\n")
            for idx, para in enumerate(paras):
                para = para.strip()
                para = para.replace('&nbsp;', ' ')
                if idx != 0:
                    para = ' '.join(para.splitlines())
                if para:
                    if options['verbose']:
                        self.stdout.write('\nParagraph %d\n\n%s\n' %
                                          (idx, para))
                    newbody = ('%s\n\n%s' % (newbody, para))

            self.stdout.write('doc types: %s' % doc_types)
            self.stdout.write('Authors: %s' % sorted(authors))

        self.stdout.write(self.style.SUCCESS(
                '%d documents imported' % len(documents)))

        db.close()
