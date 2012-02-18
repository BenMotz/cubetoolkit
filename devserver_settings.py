import os.path
import logging
import logging.config

from settings_common import *

APP_ROOT = '/home/ben/data/python/cube'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(APP_ROOT,'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = 'http://toolkit/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(APP_ROOT,'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = 'http://toolkit/static/'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(APP_ROOT, 'templates'),
)

# Enable Debug mode, add in Django toolbar:
DEBUG = True

# Django toolbar things:
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = { 'INTERCEPT_REDIRECTS' : False, }

MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.append('debug_toolbar')

# Following settings are used by the import script, can be discarded when
# switch-over is finalised.
IMPORT_SCRIPT_USER='cube-import'
IMPORT_SCRIPT_DATABASE='toolkit'

# Enable logging to the console:
logging.basicConfig(
#    level = logging.DEBUG,
    level = logging.INFO,
    format = '%(asctime)s %(levelname)s %(message)s',
)
