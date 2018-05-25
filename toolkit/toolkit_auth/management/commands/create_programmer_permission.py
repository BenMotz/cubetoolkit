from toolkit.diary.models import Role
from django.contrib.auth.models import Group
import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

from django.core.management.base import BaseCommand, CommandError


group_name = 'Programmers'
role_name = 'Programmer'


def _create_programme_role(self):
    '''Check the Programmer role exists and set it read only'''

    role = Role.objects.filter(name=role_name).first()
    if role:
        self.stdout.write(self.style.WARNING(
            '%s role already exists' % role_name))
    else:
        role = Role.objects.create(name=role_name)
        self.stdout.write(self.style.SUCCESS(
            'Creating %s role and setting it read-only' % role_name))
    role.read_only = True
    role.save()


def _create_programme_group(self):
    '''Create the permission group'''

    if Group.objects.filter(name=group_name):
        self.stdout.write(self.style.WARNING(
            '%s group exists already' % group_name))
    else:
        Group.objects.create(name=group_name)
        self.stdout.write(self.style.SUCCESS(
            'Created %s group' % group_name))


def _create_programme_permission():
    '''Set the appropriate permisions to the programme group'''

    # Create dummy ContentType:
    ct = contenttypes.models.ContentType.objects.get_or_create(
        model='',
        app_label='toolkit'
    )[0]

    # Create 'write' permission:
    programmer_permissions = \
        auth_models.Permission.objects.get_or_create(
            name='Write access to showing, events and ideas',
            content_type=ct,
            codename='programmer'
        )[0]

    programmers = Group.objects.filter(name=group_name).first()
    programmers.permissions.add(programmer_permissions)


class Command(BaseCommand):
    args = ''
    help = 'Create programmer group and permissions'

    can_import_settings = True
    requires_system_checks = True

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Wasn't actually expecting any arguments")

        _create_programme_role(self)
        _create_programme_group(self)
        _create_programme_permission()

        self.stdout.write(self.style.SUCCESS(
             'Permissions for %s group set' % group_name))
