import os.path
import subprocess
import urllib
from django.core.management.base import BaseCommand, CommandError

from toolkit.members.models import Volunteer

server_default = 'cubecinema.com'
list_default = 'volunteers'
mailman_api = 'mailman-subscriber.py'


class Command(BaseCommand):
    help = "Match active volunteers against mailman volunteers list"

    def _get_mailman_vols(self):
        vols = []
        path, filename = os.path.split(__file__)

        server = input("Enter name of server that mailman is running on [%s]: " %
                       server_default)
        if not server:
            server = server_default
        vol_list = input("Enter name of mailman list [%s]: " % list_default)
        if not vol_list:
            vol_list = list_default
        list_pass = input("Enter mailing list password: ")
        if not list_pass:
            self.stdout.write(
                self.style.WARNING('Mailing list password cannot be blank'))
            return vols

        args = '%s %s %s' % (server, vol_list, list_pass)
        shebang = 'python2 %s %s' % (os.path.join(path, mailman_api), args)

        try:
            out = subprocess.check_output(shebang,
                                          shell=True,
                                          stderr=subprocess.STDOUT)
            # out is bytes
            out = str(out, 'utf-8')
            for line in out.splitlines():
                # vols = (Volunteer.objects.filter(active=True)
                # self.stdout.write(self.style.SUCCESS(line))
                vols.append(urllib.parse.unquote_plus(line.rstrip()))
            self.stdout.write(
                self.style.SUCCESS('\n%d vols found in mailman' % len(vols)))
            return vols
        except subprocess.CalledProcessError as e:
                self.stdout.write(
                    self.style.ERROR('%s\n%s' %
                                     (shebang, str(e.output, 'utf-8'))))

    def _readfile(self, filename):
        '''Unused - read vols from a file'''

        vols = []

        with open(filename) as fp:
            vols = [urllib.parse.unquote_plus(line.rstrip()) for line in fp]

        return vols

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Show more detail',
        )

    def handle(self, *args, **options):

        mmvols = self._get_mailman_vols()
        # mmvols = self._readfile(vols_file)
        if not mmvols:
            self.stdout.write(
                self.style.WARNING('No volunteers returned by mailman'))
            return

        vols = (Volunteer.objects.filter(active=True)
                                 .order_by('member__name'))

        self.stdout.write(self.style.SUCCESS(
            '%d active volunteers to check\n' % len(vols)))

        self.stdout.write(
            'Checking volunteers for a matching email in mailman\n\n')

        for vol in vols:
            if vol.member.email.lower() in mmvols:
                if options['verbose']:
                    self.stdout.write(
                        self.style.SUCCESS('%s found in mailman' % vol.member))
            else:
                self.stdout.write(
                    self.style.WARNING('%s <%s> not found in mailman' %
                                       (vol.member, vol.member.email)))

        self.stdout.write(
            '\nChecking mailman for a matching email in volunteers\n\n')

        for mmvol in mmvols:
            matched = (Volunteer.objects.filter(member__email=mmvol)
                                        .filter(active=True))
            if matched:
                if len(matched) > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            'Duplicate entry in vols database found for %s' % mmvol))
                    for match in matched:
                        self.stdout.write(
                            '%s <%s>' %
                            (match.member.name, match.member.email))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '%s not found in volunteers database' % mmvol))
                # Try again, to see if retired
                matched = Volunteer.objects.filter(member__email=mmvol)
                if matched:
                    self.stdout.write('Found retired volunteer')
                    for match in matched:
                        self.stdout.write(
                            '%s <%s>' % (match.member.name,
                                         match.member.email))

        self.stdout.write(self.style.SUCCESS('\nChecks complete\n'))
