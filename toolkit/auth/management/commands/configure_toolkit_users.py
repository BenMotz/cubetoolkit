import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

from django.core.management.base import BaseCommand, CommandError


def _get_password(use):
    print "*" * 80
    password = raw_input("Please enter string to use as {0} password: "
                         .format(use))
    check_password = None

    while check_password != password:
        print
        check_password = raw_input("Please re-enter for confirmation: ")

    return password


def _create_or_update_user(name, email, permissions):
    if not auth_models.User.objects.filter(username=name).exists():
        password = _get_password(name)
        user = auth_models.User.objects.create_user(name, email, password)
    else:
        print "User '{0}' exists: not changing password".format(name)
        user = auth_models.User.objects.get(username=name)

    # Remove all permissions:
    user.user_permissions.clear()

    # Set to requested:
    for permission in permissions:
        user.user_permissions.add(permission)


def _configure_users():
    # Create dummy ContentType:
    ct = contenttypes.models.ContentType.objects.get_or_create(
        model='',
        app_label='toolkit'
    )[0]

    # Create 'write' permission:
    write_permission = auth_models.Permission.objects.get_or_create(
        name='Write access to all toolkit content',
        content_type=ct,
        codename='write'
    )[0]

    # Configure "admin" user with the write permission:
    _create_or_update_user("admin", 'toolkit_admin@localhost',
                           [write_permission])


class Command(BaseCommand):
    args = ''
    help = 'Configure standard cube toolkit users'

    can_import_settings = True
    requires_model_validation = True

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Wasn't expecting any arguments")

        _configure_users()
