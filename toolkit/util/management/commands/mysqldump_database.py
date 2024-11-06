from __future__ import print_function
import sys
import os.path
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

MYSQLDUMP_BINARY = "/usr/bin/mysqldump"


class Command(BaseCommand):
    help = (
        "Dump database to <output_file> using mysqldump. "
        "Dumps to stdout if <output_file> is 'STDOUT'"
    )

    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument("output_file", type=str)

    def _dump_command(self):
        db_settings = settings.DATABASES["default"]
        if db_settings["ENGINE"] != "django.db.backends.mysql":
            raise CommandError(
                "Application does not use a mysql database (very sensible) - "
                "it uses {0}".format(db_settings["engine"])
            )

        return [
            MYSQLDUMP_BINARY,
            "--single-transaction",  # So LOCK TABLES isn't needed
            "--user=" + db_settings["USER"],
            "--password=" + db_settings["PASSWORD"],
            db_settings["NAME"],
        ]

    def _dump_to_file(self, out_file, log_file):
        if not os.path.isfile(MYSQLDUMP_BINARY):
            raise CommandError(
                "Couldn't find mysqldump binary (looked for {0}".format(
                    MYSQLDUMP_BINARY
                )
            )

        print("Dumping to '{0}'".format(out_file.name), file=log_file)
        returncode = subprocess.call(self._dump_command(), stdout=out_file)

        if returncode != 0:
            raise CommandError("Failed (code {0})".format(returncode))

        print("Done", file=log_file)

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.add_argument(
            "--print-command",
            action="store_true",
            help="Print the mysqldump command, but do not run it",
        )
        return parser

    def handle(self, *args, **options):
        output_filename = options.get("output_file")

        if options.get("print_command"):
            self.stdout.write(" ".join(self._dump_command()))
            return

        if not output_filename or not output_filename.strip():
            raise CommandError("No filename supplied")

        if output_filename == "STDOUT":
            self._dump_to_file(sys.stdout, log_file=sys.stderr)
        elif os.path.exists(output_filename):
            raise CommandError(
                "Dump destination '{0}' already exists".format(output_filename)
            )
        else:
            with open(output_filename, "w") as out_file:
                self._dump_to_file(out_file, log_file=sys.stdout)
