# mysite_uwsgi.ini file
# http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
[uwsgi]

# Django-related settings
# the base directory (full path)
chdir           = /home/users/starandshadow/star_site

# Django's wsgi file
module          = wsgi
# the virtualenv (full path)
home            = /home/users/starandshadow/star_site/venv

env             = DJANGO_SETTINGS_MODULE=toolkit.settings

# process-related settings
# master
master          = true
# maximum number of worker processes
processes       = 2
# the socket (use the full path to be saf)e
socket          = /tmp/starandshadow_django.sock
# TODO work out permission to run in /var/run
#socket          = /var/run/ed_django.sock
# Socket  permissions. Was 664, then 666. 660 works now
chmod-socket    = 660
# clear environment on exit
vacuum          = true

uid             = www-data
gid             = www-data

enable-threads  = true
# http://uwsgi-docs.readthedocs.io/en/latest/articles/SerializingAccept.html
thunder-lock    = true

#harakiri = 20    # respawn processes taking more than 20 seconds
# limit the project to 128 MB
limit-as = 512

# Enable stats
stats = 127.0.0.1:9194

safe-pidfile    = /tmp/star_shadow_django.pid
daemonize       = /var/log/starandshadow/star_django.log
