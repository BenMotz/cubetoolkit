from toolkit.devserver_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/test.db',          # Path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

MEDIA_ROOT = '/tmp'

# Enable logging to the console:
LOGGING['root'] = {
    # 'handlers': ['console'],
    # 'level': 'WARNING',
}

PASSWORD_HASHERS = (
    # For testing use insecure, but much faster, MD5 password hasher:
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
