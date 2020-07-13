# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/
from django.core.management.base import BaseCommand
from django.utils.six.moves import input

from toolkit.members.models import Member


def boolean_input(question, default=None):
    result = input("%s " % question)
    if not result and default is not None:
        return default
    while len(result) < 1 or result[0].lower() not in "yn":
        result = input("Please answer yes or no: ")
    return result[0].lower() == "y"


class Command(BaseCommand):
    help = "Delete all members"

    def handle(self, *args, **options):

        if boolean_input('About to delete all of the members. Sure?'):

            members = Member.objects.all()

            self.stdout.write('Deleting...\n')

            for member in members:
                self.stdout.write('%s <%s> joined %s, updated %s' % (
                    member.name,
                    member.email,
                    member.created_at,
                    member.updated_at)
                    )
                member.delete()

            self.stdout.write(self.style.SUCCESS(
                '\nDeleted %d members\n' % len(members)))
