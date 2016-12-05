from toolkit.settings_common import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'toolkit',
        'USER': 'toolkit',
        # Substitute password for your local test database here:
        'PASSWORD': 'devserver_db_password',
        'HOST': '',  # Set to empty string for localhost.
        'PORT': '',  # Set to empty string for default.
        'CONN_MAX_AGE': 10, # Allow DB connections to persist for 10 seconds
    }
}

# Different to the key used in production!
SECRET_KEY = '*@t05l5a7+uos5*9=c7ph1t#s(l*tlcdx(n(isztw^4w2c&mu-'

LOGGING['handlers']['file']['filename'] = 'django_test.log'

# Enable logging of *everything* to the console:
LOGGING['root'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
}

EMAIL_UNSUBSCRIBE_HOST = "localhost:8000"

# Enable Debug mode, add in Django toolbar:
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

# Undefine ALLOWED_HOSTS to ensure default loopback addresses work:
del ALLOWED_HOSTS

# Django toolbar things:
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False, }

MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.append('debug_toolbar')

import warnings
warnings.filterwarnings('error', r"DateTimeField received a naive datetime",
                        RuntimeWarning, r'django\.db\.models\.fields')
