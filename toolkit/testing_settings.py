import os.path
import logging.config

from toolkit.settings_common import *

APP_ROOT = '/var/www_toolkit/site'
LOGGING_CONFIG_FILE = 'logging.conf'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

logging.config.fileConfig(os.path.join(APP_ROOT, LOGGING_CONFIG_FILE))
