import csv
from django.core.management.base import BaseCommand, CommandError

from toolkit.members.models import Volunteer

FILENAME = "export.csv"


def load_data(filename):
    data = []
    with open(filename, "rt") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                data.append(row)
    return data


class Command(BaseCommand):
    help = "Keep the volunteers from the associated CSV, retire everyone else"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dryRun',
            default=False,
            help="Simulate - don't touch the database",
        )

    def try_get_volunteer_by_email(self, email):
        try:
            return Volunteer.objects.get(member__email__iexact=email)
        except Volunteer.MultipleObjectsReturned:
            self.stdout.write(self.style.WARNING(
                "Multiple volunteers with the same email address: {0}".format(email)))
        except Volunteer.DoesNotExist:
            pass
        return None

    def handle(self, *args, **options):

        if options['dryRun']:
            verb = 'Would'
        else:
            verb = 'Will'

        self.stdout.write('Trying to read {0}'.format(FILENAME))
        desired_vols = load_data(FILENAME)
        self.stdout.write(self.style.SUCCESS(
            'Loaded %d vounteers\n' % len(desired_vols)))

        volsToRetire = (Volunteer.objects.filter(active=True)
                                 .order_by('member__name'))

        self.stdout.write(self.style.SUCCESS(
            '\nBeginning with %d active volunteers' % len(volsToRetire)))

        for idx, vol in enumerate(desired_vols):
            if idx == 0:
                continue  # Skip header row
            self.stdout.write('\n%s <%s>' % (vol[1], vol[2]))
            matched_vol = self.try_get_volunteer_by_email(vol[2])
            if matched_vol:
                self.stdout.write(self.style.SUCCESS('%s found' % vol[2]))
                volsToRetire = volsToRetire.exclude(
                    member__volunteer=matched_vol)
                comments = vol[3]
                if comments:
                    self.stdout.write('*** Existing notes ***')
                    self.stdout.write(matched_vol.member.volunteer.notes)
                    self.stdout.write('*** Additional notes ***')
                    self.stdout.write(comments)
                    matched_vol.member.volunteer.notes = (
                        matched_vol.member.volunteer.notes +
                        '\nAugust 2020:\n' +
                        comments)
                    if not options['dryRun']:
                        matched_vol.save()
            else:
                self.stdout.write(self.style.WARNING('%s not found' % vol[2]))

        self.stdout.write(self.style.WARNING(
            '\n%s be retiring the following %d volunteers\n' %
            (verb, len(volsToRetire))))

        for vol in volsToRetire:
            self.stdout.write('%s <%s>' %
                              (vol.member.name,
                               vol.member.email))
            if not options['dryRun']:
                vol.active = False
                vol.save()
        self.stdout.write('\n')
