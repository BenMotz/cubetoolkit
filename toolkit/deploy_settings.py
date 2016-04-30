from toolkit.settings import *

# This settings file is used by the deploy script for running various manage.py
# commands: it's needed because the user which the deploy script runs as
# doesn't necessarily have write permissions to the usual system logfile
LOGGING['handlers']['file']['filename'] = os.path.join(
        BASE_DIR, 'deploy.log'
    )
