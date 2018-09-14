import datetime
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import django.utils.timezone

import MySQLdb

# Adjust to taste
dbuser = 'starshadow'
dbpass = 'ye2EUsSUCYY8ALx7'
dbdb = 'ssarchive'


class Command(BaseCommand):
    help = "import documents from legacy star and shadow django web site"

    def _conn_to_archive_database(self):
        try:
            self.stdout.write('Connecting to database %s...' % dbdb)
            db = MySQLdb.connect("localhost",
                                 dbuser,
                                 dbpass,
                                 dbdb)
            return db
        except MySQLdb.Error as e:
            self.stdout.write(self.style.ERROR(
                'Failed to connect to database %s' % dbdb))

    def _read_archive_db(self, cursor, table):

        # ORDER BY `startDate` DESC"
        sql = "SELECT * FROM `%s`" % table
        rows = cursor.execute(sql)  # returns number of rows
        self.stdout.write('%s: %d rows found' % (table, rows))
        documents = cursor.fetchall()
        # events = events[0:10]
        return documents

    def handle(self, *args, **options):

        db = self._conn_to_archive_database()
        cursor = db.cursor()
        doc_types = []

        if True:
            documents = self._read_archive_db(cursor, 'content_document')

            for document in documents:
                legacy_id = document[0]
                title = document[1]
                title = " ".join(title.split())
                source = document[2]
                source = " ".join(source.split())
                summary = document[3]
                author = document[4].title()
                created = document[5]
                doc_type = document[6]
                body = document[7]

                self.stdout.write('%s "%s" "%s" "%s" %s "%s"' % (
                    legacy_id,
                    title,
                    source,
                    author,
                    created,
                    doc_type
                ))

                if doc_type not in doc_types:
                    doc_types.append(doc_type)

                # continue  # FIXME

        print(doc_types)
        self.stdout.write(self.style.SUCCESS(
                '%d documents imported' % len(documents)))

        db.close()
