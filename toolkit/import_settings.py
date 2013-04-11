from toolkit.settings import *

# Following settings are used by the import script, can be discarded when
# switch-over is finalised.

IMPORT_SCRIPT_USER = 'toolkitimport'
IMPORT_SCRIPT_DATABASE = 'toolkitimport'

# Logging setup for import script:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(message)s',
        },
        'verbose': {
            'format': '%(asctime)s %(module)s %(funcName)s %(levelname)s : %(message)s',
        },
    },

    'filters': {
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
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            # Args:
            'filename': '/tmp/toolkit-import.log',
            'mode': 'a',
        },
    },

    'loggers': {
        # Log everything from Django to file...
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Except for database queries (only happens in DEBUG=True mode)
        'django.db.backends': {
            'level': 'INFO',
            'propagate': True,
        },

        # Log toolkit to file/console at INFO and above:
        'toolkit': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },

        # South:
        'south': {
            'level': 'INFO',
            'propagate': True,
        },
    },
    # Anything else, log to both:
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}
