import os

from toolkit.settings_common import *

ALLOWED_HOSTS = ["localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ["DB_PORT"],
    }
}

CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# Disable the log file
del LOGGING["handlers"]["file"]
LOGGING["loggers"]["toolkit"]["handlers"] = ["console"]

# Instead enable logging to the console (configured in settings_common.py)
LOGGING["root"] = {
    "handlers": ["console", "mail_admins"],
    "level": "DEBUG",
}

# The following are the lucky recipients of error emails
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

SERVER_EMAIL = "toolkit_errors@cubecinema.com"
