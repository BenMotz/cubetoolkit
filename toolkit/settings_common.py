import sys
import os
import datetime

import django.urls

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

VENUE = {
    "name": "Cube",
    "longname": "Cube Microplex",
    "cinemaname": "Cube Cinema",
    "url": "https://www.cubecinema.com",
    "contact_page": "/pages/about/directions/",
    "piwik_id": 3,
    "facebook": "https://www.facebook.com/cubecinema/",
    "instagram": "https://www.instagram.com/cubemicroplex/",
    "mastodon": "https://mastodon.world/@cubecinema",
    "bluesky": "https://bsky.app/profile/cubecinema.com",
    "flickr": "https://flickr.com/groups/cubemicroplex/",
    "vimeo": "https://vimeo.com/cubemicroplex/",
    "youtube": "https://www.youtube.com/user/cubelog",
    "nav_menu_img": "",
    "internal_header_img": "content/logo.gif",
    "wagtale_admin_img": "/static/content/logo.gif",
    "favicon": "/static/favicon/favicon_cube.ico",
    "font_h2": "",
    # This is used as the hostname for unsubscribe links in emails
    # i.e. emails will have links added to
    # this]/members/100/unsubscribe)
    "email_unsubscribe_host": "https://cubecinema.com",
    # Default address to which reports of a successful mailout
    # delivery are sent:
    "mailout_delivery_report_to": "cubeadmin@cubecinema.com",
    # "From" address for mailout
    "mailout_from_address": "mailout@cubecinema.com",
    # email address shown when volunteer removes themselves from rota
    "vols_email": "rota@cubecinema.com",
    # List of people to get notifications when new vols are added
    "vols_admin_address": ["volunteers-owner@cubecinema.com"],
    "show_user_management": False,
}

# The following list of IP addresses is used to restrict access to some pages
# (at time of writing, only the 'add a new member' page)
CUBE_IP_ADDRESSES = tuple("10.1.1.%d" % n for n in range(33, 255))

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

# If an event has a tag matching one of those in this set then the
# PROGRAMME_EVENT_TERMS_MIN_WORDS check will be ignored
TAGS_WITHOUT_TERMS = {
    "meeting", "training"
}


EDIT_INDEX_DEFAULT_DAYS_AHEAD = 365
EDIT_INDEX_DEFAULT_USE_POPUPS = False

# A soft limit on the max length of copy summary. The hard limit is the size of
# the database field (at time of writing, 4096 characters.) This is (currently)
# only enforced by the EditEvent form (i.e. it'll be ignored if other code
# directly sets and saves some longer text)
PROGRAMME_COPY_SUMMARY_MAX_CHARS = 450
# Minimum number of words required in the event copy to confirm an event
PROGRAMME_EVENT_TERMS_MIN_WORDS = 3
# Max size of uploaded diary media items (enforced by MediaItemForm)
PROGRAMME_MEDIA_MAX_SIZE_MB = 5  # Megabytes (i.e. * 1024 * 1024 bytes)

DEFAULT_MUGSHOT = "/static/members/default_mugshot.gif"

# SMTP host/port settings. For complete list of relevant settings see:
# https://docs.djangoproject.com/en/1.5/ref/settings/#email-backend
EMAIL_HOST = "localhost"
EMAIL_PORT = 25
# TODO add username and password

# Default number of days ahead for which to include detailed copy in the
# member's mailout
MAILOUT_DETAILS_DAYS_AHEAD = 9
# Default number of days ahead for which to include listings in the member's
# mailout
MAILOUT_LISTINGS_DAYS_AHEAD = 14

# The maximum number of each type of role that can be assigned to a showing
# (so, for example, can't have more than this number of bar staff)
MAX_COUNT_PER_ROLE = 8

# Probably don't want to change these: subdirectories of MEDIA directory where
# volunteer images get saved:
VOLUNTEER_PORTRAIT_DIR = "volunteers"

# Currently only used for setting an outer limit on what year printed
# programmes can be uploaded
DAWN_OF_TIME = 1998

# Used to indicate if volunteer/member added dates are when they were actually
# added, vs. if they were bulk imported from the old toolkit
DAWN_OF_TOOLKIT = datetime.date(year=2014, month=2, day=12)

DEFAULT_TRAINING_EXPIRY_MONTHS = 12

# Colour used for the calendar view if multiroom isn't enabled:
CALENDAR_DEFAULT_COLOUR = "#33CC33"
# Parameters to tweak colour by:
CALENDAR_HISTORIC_LIGHTER = 0.75
CALENDAR_HISTORIC_SHADIER = 1.0

###############################################################################

# Enable/disable some lumps of functionality that the Cube doesn't (currently)
# use but the Star + Shadow (probably) does:
MULTIROOM_ENABLED = False
HTML_MAILOUT_ENABLED = True
MEMBERSHIP_EXPIRY_ENABLED = False
MEMBERSHIP_LENGTH_DAYS = 365

###############################################################################
#
# Wagtail settings

WAGTAIL_SITE_NAME = "The Cube Microplex"

# Don't show fields to change user passwords (for other users, in admin)
WAGTAILUSERS_PASSWORD_ENABLED = False

# Don't allow user to change their own password
WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = False

# Disable password reset function
WAGTAIL_PASSWORD_RESET_ENABLED = False

# Don't automatically check for (and notify) new Wagtail versions:
WAGTAIL_ENABLE_UPDATE_CHECK = False

# Disable use of remote avatars
WAGTAIL_GRAVATAR_PROVIDER_URL = None

# Restricting these lists to single items hides the configuration option:
WAGTAILADMIN_PERMITTED_LANGUAGES = [("en", "English")]
# TODO: use the value of "TIME_ZONE", which is unfortunately defined further
# down :-(
WAGTAIL_USER_TIME_ZONES = ["Europe/London"]

# This is the base URL used by the Wagtail admin site. It is typically used for
# generating URLs to include in notification emails.
#
# If this setting is not present, Wagtail will try to fall back to
# request.site.root_url or to the request’s host name.
WAGTAILADMIN_BASE_URL = "https://cubecinema.com/cms"

###############################################################################
#
# Celery settings
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

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
    "members.Volunteer.portrait": {
        "portrait": {
            "size": (75, 200),
        },
    },
    "diary.MediaItem": {
        "indexview": {"size": (600, 0), "quality": 45},
        "eventdetail": {
            "size": (800, 800),
        },
        "editpreview": {
            "size": (250, 250),
        },
    },
    "wagtailimages.Image.file": {
        "indexview": {"size": (600, 0), "quality": 45},
    },
}

# Custom tweaks:
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
APPEND_SLASH = True

# Django settings for cube project.
ALLOWED_HOSTS = [
    ".cubecinema.com",
]
DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

# Authorisation related settings:
LOGIN_URL = django.urls.reverse_lazy("login")
LOGIN_REDIRECT_URL = django.urls.reverse_lazy("toolkit-index")

PASSWORD_HASHERS = (
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
    "django.contrib.auth.hashers.SHA1PasswordHasher",
    # Don't allow:
    # 'django.contrib.auth.hashers.MD5PasswordHasher',
    # 'django.contrib.auth.hashers.CryptPasswordHasher',
)

# Ref; https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "Europe/London"

# Enable timezone support
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-gb"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False  # True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Following are defined in settings_*.py
# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
#
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = "/media/"
#
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = "/static/admin/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, "toolkit", "static_common"),
)

# Where to store messages:
MESSAGE_STORAGE = "django.contrib.messages.storage.fallback.FallbackStorage"

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

SECURE_CONTENT_TYPE_NOSNIFF = True

# Generates some errors in Chrome?
SECURE_BROWSER_XSS_FILTER = True

# Setting DENY breaks iframes in the calendar view:
X_FRAME_OPTIONS = "SAMEORIGIN"

# Setting True breaks members mailout, as JS relies on loading the cookie
# CSRF_COOKIE_HTTPONLY = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Look for template source files inside installed applications:
        "APP_DIRS": True,
        # Put strings here, like "/home/html/django_templates" or
        # "C:/www/django/templates".  Always use forward slashes, even on
        # Windows.
        # Don't forget to use absolute paths, not relative paths.
        "DIRS": (os.path.join(BASE_DIR, "templates"),),
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": (
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "toolkit.util.context_processors.venue",
                "toolkit.diary.context_processors.diary_settings",
                "toolkit.diary.context_processors.promoted_tags",
            ),
            # May be worth enabling for improved performance?
            # 'loaders':
            #    ('django.template.loaders.cached.Loader', (
            #        'django.template.loaders.filesystem.Loader',
            #        'django.template.loaders.app_directories.Loader',
            #    )),
        },
    }
]

ROOT_URLCONF = "toolkit.urls"

INSTALLED_APPS = (
    "toolkit.diary",
    "toolkit.members",
    "toolkit.toolkit_auth",
    "toolkit.index",
    "toolkit.util",
    "toolkit.content",
    "easy_thumbnails",
    "django.contrib.auth",
    "django.contrib.contenttypes",  # Needed by auth framework
    # Sessions framework: used to store preferences and login details
    "django.contrib.sessions",
    # 'django.contrib.sites',  # Not used
    # Messages: Used to transfer informative text and notifications between
    # pages
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    # Wagtail + support:
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "wagtail.contrib.forms",
    "modelcluster",
    "taggit",
    "crispy_forms",
)

CRISPY_TEMPLATE_PACK = "bootstrap4"

# Common logging config. Different settings files can tweak this.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(name)s %(levelname)s %(message)s",
        },
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            # Args:
            "stream": sys.stderr,
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",  # really?
            "formatter": "verbose",
            # Args:
            "filename": "debug.log",  # overridden in other settings files
            "mode": "a",
            "maxBytes": 10485760,
            "backupCount": 5,
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        # 'null': {
        #     'level': 'DEBUG',
        #     'class': 'logging.NullHandler',
        #     'formatter': 'simple',
        # }
    },
    "loggers": {
        "django": {
            "propagate": True,
            "level": "INFO",
        },
        "toolkit": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
    },
    # Don't configure a root logger or any other logging config; each settings
    # file should do that
}
