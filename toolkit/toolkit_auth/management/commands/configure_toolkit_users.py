from __future__ import print_function
import getpass
import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

from django.core.management.base import BaseCommand, CommandError


def _get_password(use):
    print("*" * 80)
    password = ""
    check_password = None

    while check_password != password:
        password = getpass.getpass("Please enter password for {0}: "
                                   .format(use))
        check_password = getpass.getpass("Please re-enter for confirmation: ")
        if check_password != password:
            print("Passwords don't match; please try again...")

    return password


def _create_or_update_user(
        name,
        email,
        permissions,
        is_superuser=False,
        is_staff=False):
    if not auth_models.User.objects.filter(username=name).exists():
        password = _get_password(name)
        user = auth_models.User.objects.create_user(name, email, password)
    else:
        print("User '{0}' exists: not changing password".format(name))
        user = auth_models.User.objects.get(username=name)

    # Remove all permissions:
    user.user_permissions.clear()

    # Set to requested:
    for permission in permissions:
        user.user_permissions.add(permission)

    user.is_superuser = is_superuser
    user.is_staff = is_staff
    user.save()


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

    # Create 'read' permission:
    read_permission = auth_models.Permission.objects.get_or_create(
        name='Read access to all toolkit content',
        content_type=ct,
        codename='read'
    )[0]

    # retrieve permission for editing diary.models.RotaEntry rows:
    diary_content_type = contenttypes.models.ContentType.objects.get(
        app_label='diary',
        model='rotaentry',
    )

    edit_rota_permission = auth_models.Permission.objects.get(
        codename='change_rotaentry',
        content_type=diary_content_type
    )

    # Configure "admin" user with the read and write permissions:
    _create_or_update_user(
        "admin", 'toolkit_admin@localhost',
        [write_permission, read_permission, edit_rota_permission],
        # Mark admin as staff, to get wagtail superuser control:
        is_superuser=True,
        is_staff=True)

    # Read only (and write to the rota) user:
    _create_or_update_user(
        "volunteer", 'toolkit_admin_readonly@localhost',
        [edit_rota_permission])


class Command(BaseCommand):
    args = ''
    help = 'Configure standard cube toolkit users'

    can_import_settings = True
    requires_system_checks = True

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Wasn't expecting any arguments")

        _configure_users()
