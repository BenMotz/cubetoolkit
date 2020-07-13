from django.core.management.base import BaseCommand

from toolkit.members.models import Volunteer


class Command(BaseCommand):
    help = "Show active volunteers"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--names',
            action='store_true',
            dest='names',
            default=False,
            help='Show names as well as emails',
        )

    def handle(self, *args, **options):

        vols = (Volunteer.objects.filter(active=True)
                                 .order_by('member__name'))

        for vol in vols:
            if options['names']:
                self.stdout.write('%s <%s>' %
                                  (vol.member.name,
                                   vol.member.email))
            else:
                self.stdout.write('%s' %
                                  vol.member.email)

        self.stdout.write(self.style.SUCCESS(
            '\n%d active members' % len(vols)))
