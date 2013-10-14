import os.path
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

MYSQLDUMP_BINARY = "/usr/bin/mysqldump"


class Command(BaseCommand):
    args = '<output_file>'
    help = 'Dump database to <output_file> using mysqldump'

    can_import_settings = True
    requires_model_validation = True

    def _dump_to_filename(self, filename):
        if os.path.exists(filename):
            raise CommandError("Dump destination '{0}' already exists"
                               .format(filename))

        if not os.path.isfile(MYSQLDUMP_BINARY):
            raise CommandError("Couldn't find mysqldump binary (looked for {0}"
                               .format(MYSQLDUMP_BINARY))

        db_settings = settings.DATABASES['default']
        if db_settings['ENGINE'] != 'django.db.backends.mysql':
            raise CommandError("Application does not use a mysql database (very"
                               " sensible) - it uses {0}".format(db_settings['engine']))

        with open(filename, "w") as out_file:
            print "Dumping to '{0}'".format(filename)
            returncode = subprocess.call([
                MYSQLDUMP_BINARY,
                "--single-transaction",  # So LOCK TABLES isn't needed
                "--user=" + db_settings['USER'],
                "--password=" + db_settings['PASSWORD'],
                db_settings['NAME'],
            ], stdout=out_file)

        if returncode != 0:
            raise CommandError("Failed (code {0})".format(returncode))

        print "Done"

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("Only expecting one argument")
        elif len(args) == 0:
            raise CommandError("No filename supplied")

        output_filename = args[0]

        self._dump_to_filename(output_filename)
