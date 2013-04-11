from toolkit.settings_common import *

APP_ROOT = '/home/users/cubetoolkit/site'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

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

# Enable logging to the logfile (configured in settings_common.py)
LOGGING['root'] = {
    'handlers': ['file'],
    'level': 'DEBUG',
}
