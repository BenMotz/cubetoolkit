#!/usr/bin/python

import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

def get_password():
    print "*" * 80
    password = raw_input("Please enter string to use as admin password: ")
    check_password = None

    while check_password != password:
        print
        check_password = raw_input("Please re-enter for confirmation: ")

    return password


def main():
    # Read only user:
    # auth_models.User.objects.create_user('cube', 'toolkit_admin_readonly@localhost', '********')
    # Read/write user:
    cube_password = get_password()
    user_rw = auth_models.User.objects.create_user('admin', 'toolkit_admin@localhost', cube_password)
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
    # Give "admin" user the write permission:
    user_rw.user_permissions.add(write_permission)

if __name__ == "__main__":
    main()
