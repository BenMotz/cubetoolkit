import os.path
import logging
import logging.config

from settings_common import *

APP_ROOT = '/home/users/cubetoolkit/site'
LOGGING_CONFIG_FILE = 'logging.conf'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(APP_ROOT,'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(APP_ROOT,'static')

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(APP_ROOT, 'templates'),
)

logging.config.fileConfig(os.path.join(APP_PATH,LOGGING_CONFIG_FILE))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cubetoolkit',
        'USER': 'cubetoolkit',
        'PASSWORD': 'hialpabg',
        'HOST': '',
        'PORT': '',
    }
}

# Following settings are used by the import script, can be discarded when
# switch-over is finalised.
IMPORT_SCRIPT_USER='toolkitimport'
IMPORT_SCRIPT_DATABASE='toolkitimport'

