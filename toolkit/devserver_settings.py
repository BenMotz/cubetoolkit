import warnings
from toolkit.settings_common import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "toolkit",
        "USER": "toolkit",
        # Substitute password for your local test database here:
        "PASSWORD": "devserver_db_password",
        "HOST": "",  # Set to empty string for localhost.
        "PORT": "",  # Set to empty string for default.
        "CONN_MAX_AGE": 10,  # Allow DB connections to persist for 10 seconds
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Different to the key used in production!
SECRET_KEY = "*@t05l5a7+uos5*9=c7ph1t#s(l*tlcdx(n(isztw^4w2c&mu-"

LOGGING["handlers"]["file"]["filename"] = "django_test.log"

# Enable logging of *everything* to the console:
LOGGING["root"] = {
    "handlers": ["console"],
    "level": "DEBUG",
}

# Override setting in settings_common
VENUE["email_unsubcribe_host"] = "localhost:8000"

# Enable Debug mode, add in Django toolbar:
DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = True

ALLOWED_HOSTS = ("127.0.0.1", "localhost", "0.0.0.0")

# Django toolbar things:
INTERNAL_IPS = ("127.0.0.1",)
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
