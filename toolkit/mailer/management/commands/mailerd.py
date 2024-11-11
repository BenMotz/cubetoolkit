from django.core.management.base import BaseCommand

from toolkit.mailer.mailerd import run


class Command(BaseCommand):
    help = "Run toolkit mailerd"

    def handle(self, *args, **options):
        run()
