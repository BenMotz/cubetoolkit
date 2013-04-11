from toolkit.settings_common import *

APP_ROOT = '/home/ben/data/python/cube'

EMAIL_UNSUBSCRIBE_HOST = "localhost:8000"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = 'http://toolkit/media/'
# MEDIA_ROOT = '/var/www_toolkit/site/media'

# Enable Debug mode, add in Django toolbar:
DEBUG = True

# Django toolbar things:
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False, }

MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.append('debug_toolbar')

# Enable logging of *everything* to the console:
LOGGING['root'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
}

import warnings
warnings.filterwarnings('error', r"DateTimeField received a naive datetime",
                        RuntimeWarning, r'django\.db\.models\.fields')
