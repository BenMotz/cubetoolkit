import os

from toolkit.settings_common import *

ALLOWED_HOSTS=["localhost"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

LOGGING['handlers']['file']['filename'] = '/var/log/cubetoolkit/debug.log'

# Enable logging to the logfile (configured in settings_common.py)
LOGGING['root'] = {
    'handlers': ['file', 'mail_admins'],
    'level': 'DEBUG',
}

# The following are the lucky recipients of error emails
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

SERVER_EMAIL = "toolkit_errors@cubecinema.com"

