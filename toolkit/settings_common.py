import os.path
import django.core.urlresolvers
import sys

# The following list of IP addresses is used to restrict access to some pages
# (at time of writing, only the 'add a new member' page)
CUBE_IP_ADDRESSES = (
    '10.20.134.1',
    '10.20.134.1',
    '10.20.134.2',
    '10.20.134.3',
    '10.20.134.4',
    '10.20.134.5',
    '10.20.134.6',
    '10.20.134.7',
    '10.20.134.8',
    '10.20.134.9',
    '10.20.134.10',
    '10.20.134.11',
    '10.20.134.12',
    '10.20.134.13',
    '10.20.134.14',
    '10.20.134.15',
    '10.20.134.16',
    '10.20.134.17',
    '10.20.134.18',
    '10.20.134.19',
    '10.20.134.20',
)

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
Additional Info -"""

EDIT_INDEX_DEFAULT_DAYS_AHEAD = 365
EDIT_INDEX_DEFAULT_USE_POPUPS = True

# A soft limit on the max length of copy summary. The hard limit is the size of
# the database field (at time of writing, 4096 characters.) This is (currently)
# only enforced by the EditEvent form (i.e. it'll be ignored if other code
# directly sets and saves some longer text)
PROGRAMME_COPY_SUMMARY_MAX_CHARS = 400
# Max size of uploaded diary media items (enforced by MediaItemForm)
PROGRAMME_MEDIA_MAX_SIZE_MB = 5  # Megabytes (i.e. * 1024 * 1024 bytes)

DEFAULT_MUGSHOT = "/static/members/default_mugshot.gif"

# This is used as the hostname for unsubscribe links in emails (i.e. emails
# will have links added to http://[this]/members/100/unsubscribe)
EMAIL_UNSUBSCRIBE_HOST = "cubecinema.com"

# SMTP host/port settings. For complete list of relevant settings see:
# https://docs.djangoproject.com/en/1.5/ref/settings/#email-backend
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# Default number of days ahead for which to include detailed copy in the
# member's mailout
MAILOUT_DETAILS_DAYS_AHEAD = 9
# Default number of days ahead for which to include listings in the member'sm
# mailout
MAILOUT_LISTINGS_DAYS_AHEAD = 14

# Default address to which reports of a successful mailout delivery are sent:
MAILOUT_DELIVERY_REPORT_TO = u"cubeadmin@cubecinema.com"
# "From" address for mailout
MAILOUT_FROM_ADDRESS = u"mailout@cubecinema.com"

# The maximum number of each type of role that can be assigned to a showing
# (so, for example, can't have more than this number of bar staff)
MAX_COUNT_PER_ROLE = 8

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
            'upscale': 'true',
            'size': (650, 0),
            'crop': 'scale',
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

# Authorisation related settings:
LOGIN_URL = django.core.urlresolvers.reverse_lazy('login')

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    # Don't allow:
    # 'django.contrib.auth.hashers.MD5PasswordHasher',
    # 'django.contrib.auth.hashers.CryptPasswordHasher',
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
    # 'django.contrib.sites',  # Not used
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
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
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
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
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
