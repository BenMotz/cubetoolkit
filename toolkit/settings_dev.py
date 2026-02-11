import os
import warnings
from toolkit.settings_common import *

# environment values are passed in from docker

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "toolkit"),
        "USER": os.environ.get("DB_USER", "toolkit"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "devserver_db_password"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "CONN_MAX_AGE": 10,  # Allow DB connections to persist for 10 seconds
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "*@t05l5a7+uos5*9=c7ph1t#s(l*tlcdx(n(isztw^4w2c&mu-"
)

# Override setting in settings_common
VENUE["email_unsubcribe_host"] = "localhost:8000"

# Enable Debug mode, add in Django toolbar:
DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = True

ALLOWED_HOSTS = ("127.0.0.1", "localhost")

# Django toolbar things:
INTERNAL_IPS = (
    "127.0.0.1",
)  # this doesn't work when running through a docker container. TODO.
DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
}

MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.append("debug_toolbar")

CRISPY_FAIL_SILENTLY = False

warnings.filterwarnings(
    "error",
    r"DateTimeField received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)


# The following are the lucky recipients of error emails
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

SERVER_EMAIL = "toolkit_errors@cubecinema.com"
