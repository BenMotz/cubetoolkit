# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/
# https://stackoverflow.com/questions/8989221/django-select-only-rows-with-duplicate-field-values
# TODO ignore vols

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Count

from toolkit.members.models import Member


class Command(BaseCommand):
    help = "Find members with duplicated email addresses"

    def handle(self, *args, **options):

        self.stdout.write('Members with duplicated email addresses...')

        dupes = (Member.objects.values('email')
                               .exclude(email='')
                               .annotate(Count('id'))
                               .order_by()
                               .filter(id__count__gt=1))

        members = Member.objects.filter(email__in=[item['email'] for item in dupes])
        members = members.order_by('name')

        for member in members:
            self.stdout.write('%s <%s> joined %s' % (
                member.name,
                member.email,
                member.created_at)
            )
            # member.delete()

        self.stdout.write(self.style.SUCCESS(
            '\nFound %d email duplicates' % len(dupes)))

        self.stdout.write(self.style.SUCCESS(
            'from %d members\n' % len(members)))
