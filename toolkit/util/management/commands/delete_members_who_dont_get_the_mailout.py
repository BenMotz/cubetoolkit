# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from toolkit.members.models import Member


def boolean_input(question, default=None):
    result = input("%s " % question)
    if not result and default is not None:
        return default
    while len(result) < 1 or result[0].lower() not in "yn":
        result = input("Please answer yes or no: ")
    return result[0].lower() == "y"


class Command(BaseCommand):
    help = "Delete members who don't get the members mailout"

    def handle(self, *args, **options):

        if not boolean_input("About to delete all members who don't get the mailout. Sure?"):
            return

        dead_wood = Member.objects.exclude(mailout=True)
        vols_found = 0
        active_vols_found = 0
        verbose = False

        self.stdout.write('Deleting...')

        for member in dead_wood:
            try:
                member.volunteer
                self.stdout.write(self.style.WARNING('Not deleting volunteer %s <%s> joined %s' % (
                    member.name,
                    member.email,
                    member.created_at)
                ))
                vols_found = vols_found + 1

                if member.volunteer.active:
                    self.stdout.write(self.style.ERROR('Not deleting active volunteer %s <%s> joined %s' % (
                        member.name,
                        member.email,
                        member.created_at)
                    ))
                    active_vols_found = active_vols_found + 1

            except ObjectDoesNotExist:   # Not a volunteer
                if verbose:
                    self.stdout.write('%s <%s> joined %s, updated %s' % (
                        member.name,
                        member.email,
                        member.created_at,
                        member.updated_at)
                    )
                member.delete()

        self.stdout.write(self.style.SUCCESS(
            '\nDeleted %d members\n' % len(dead_wood)))

        self.stdout.write(self.style.WARNING(
            'Not deleted %d volunteers\n' % vols_found))

        self.stdout.write(self.style.ERROR(
            'Not deleted %d active volunteers\n' % active_vols_found))
