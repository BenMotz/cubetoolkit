#!/usr/bin/python

import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes


def get_password(use):
    print "*" * 80
    password = raw_input("Please enter string to use as {0} password: "
                         .format(use))
    check_password = None

    while check_password != password:
        print
        check_password = raw_input("Please re-enter for confirmation: ")

    return password


def create_or_update_user(name, email, permissions):
    if not auth_models.User.objects.filter(username=name).exists():
        password = get_password(name)
        user = auth_models.User.objects.create_user(name, email, password)
    else:
        print "User '{0}' exists: not changing password".format(name)
        user = auth_models.User.objects.get(username=name)

    # Remove all permissions:
    user.user_permissions.clear()

    # Set to requested:
    for permission in permissions:
        user.user_permissions.add(permission)


def main():
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
    create_or_update_user("admin", 'toolkit_admin@localhost',
        [write_permission, read_permission, edit_rota_permission])

    # Read only (and write to the rota) user:
    create_or_update_user("volunteer", 'toolkit_admin_readonly@localhost',
        [edit_rota_permission])


if __name__ == "__main__":
    main()
