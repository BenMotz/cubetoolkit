import os.path
import django.core.urlresolvers
import sys


DEFAULT_TERMS_TEXT = """Contacts-
Company-
Address-
Email-
Ph No-
Hire Fee (inclusive of VAT, if applicable) -
Financial Deal (%/fee/split etc)-
Deposit paid before the night (p/h only) -
Amount needed to be collected (p/h only) -
Special Terms -
Tech needed -
Additonal Info -"""

DEFAULT_MUGSHOT = "/static/members/default_mugshot.gif"

# This is used as the hostname for unsubscribe links in emails (i.e. emails
# will have links added to http://[this]/members/100/unsubscribe)
EMAIL_UNSUBSCRIBE_HOST = "cubecinema.com"

# SMTP host/port settings. For complete list of relevant settings see:
# https://docs.djangoproject.com/en/1.5/ref/settings/#email-backend
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# Default address to which reports of a successful mailout delivery are sent:
MAILOUT_DELIVERY_REPORT_TO = u"cubeadmin@cubecinema.com"
# "From" address for mailout
MAILOUT_FROM_ADDRESS = u"mailout@cubecinema.com"

# The maximum number of each type of role that can be assigned to a showing
# (so, for example, can't have more than this number of bar staff)
MAX_COUNT_PER_ROLE = 6

# Probably don't want to change these: subdirectories of MEDIA directory where
# volunteer images get saved:
VOLUNTEER_PORTRAIT_DIR = 'volunteers'

# Currently only used for setting an outer limit on what year printed
# programmes can be uploaded
DAWN_OF_TIME = 1998

###############################################################################
#
# Below here are Django settings
#

# Thumbnails will be stored in a subdirectory (called "thumbnails") of where
# the original image is stored:
THUMBNAIL_SUBDIR = "thumbnails"

THUMBNAIL_DEBUG = True

# Settings for easy_thumbnails:
THUMBNAIL_ALIASES = {
    'members.Volunteer.portrait': {
        'portrait': {
            'size': (75, 200),
        },
    },
    'diary.MediaItem': {
        'indexview': {
            'size': (500, 300),
            'crop': 'smart',
            'background': '#FFFFFF',
        },
        'eventdetail': {
            'size': (800, 800),
        },
        'editpreview': {
            'size': (250, 250),
        }
    },
}
SOUTH_MIGRATION_MODULES = {
    'easy_thumbnails': 'easy_thumbnails.south_migrations',
}



# Custom tweaks:
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
APP_ROOT_DETECTED = os.path.abspath(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), ".."))

APPEND_SLASH = True

# Celery
BROKER_URL = 'django://'
CELERY_RESULT_BACKEND = 'database'
CELERY_RESULT_DBURI = "django://"


# Django settings for cube project.
ALLOWED_HOSTS = ['.cubecinema.com', ]
DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

## Authorisation related settings:
LOGIN_URL = django.core.urlresolvers.reverse_lazy('login')

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    #   Don't allow:
    #    'django.contrib.auth.hashers.MD5PasswordHasher',
    #    'django.contrib.auth.hashers.CryptPasswordHasher',
)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Enable timezone support
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False  # True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Following are defined in settings_*.py
## Absolute filesystem path to the directory that will hold user-uploaded files.
## Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(APP_ROOT_DETECTED, 'media')
#
## URL that handles the media served from MEDIA_ROOT. Make sure to use a
## trailing slash.
## Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'
#
## Absolute path to the directory static files should be collected to.
## Don't put anything in this directory yourself; store your static files
## in apps' "static/" subdirectories and in STATICFILES_DIRS.
## Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(APP_ROOT_DETECTED, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

 # Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(APP_ROOT_DETECTED, 'toolkit', 'static_common'),
)

# Where to store messages:
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.static',
)

ROOT_URLCONF = 'toolkit.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(APP_ROOT_DETECTED, 'templates'),
)

INSTALLED_APPS = (
    'toolkit.diary',
    'toolkit.members',
    'toolkit.auth',
    'toolkit.index',
    'toolkit.util',
    'easy_thumbnails',
    'django.contrib.auth',
    'django.contrib.contenttypes',  # Needed by auth framework
    # Sessions framework: used to store preferences and login details
    'django.contrib.sessions',
    #'django.contrib.sites',  # Not used
    # Messages: Used to transfer informative text and notifications between pages
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    # Django databaes migration tool:
    'south',

    # Enabled use of database as 'message bus' to celery:
    'kombu.transport.django',
    # Django-celery
    'djcelery',
)

# Common logging config. Different settings files can tweak this.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'simple': {
            'format': '%(name)s %(levelname)s %(message)s',
        },
        'verbose': {
            'format': '%(asctime)s %(module)s %(funcName)s %(levelname)s : %(message)s',
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            # Args:
            'stream': sys.stderr,
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # really?
            'formatter': 'verbose',
            # Args:
            'filename': 'debug.log',  # overridden in other settings files
            'mode': 'a',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        # 'null': {
        #     'level': 'DEBUG',
        #     'class': 'logging.NullHandler',
        #     'formatter': 'simple',
        # }
    },

    'loggers': {
        'django': {
            'propagate': True,
            'level': 'INFO',
        },
    },

    # Don't configure a root logger or any other logging config; each settings
    # file should do that
}
