import os
from toolkit.settings_common import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
        "CONN_MAX_AGE": 10,  # Allow DB connections to persist for 10 seconds
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ["SECRET_KEY"]

LOGGING["loggers"]["PIL"] = {"level": "INFO"}

# Enable logging to the console (configured in settings_common.py)
LOGGING["root"] = {
    "handlers": ["console", "mail_admins"],
    "level": "DEBUG",
}

# The following are the lucky recipients of error emails
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
    # ('Ben Motz', 'ben@cubecinema.com'),
    # ('Marcus Valentine', 'marcus@marcusv.org'),
    ("Alan Harris", "email@alanoharris.com"),
)

SERVER_EMAIL = "toolkit_errors@cubecinema.com"

# SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# This breaks the calendar
# See https://docs.djangoproject.com/en/1.11/ref/clickjacking/ for a fix
# X_FRAME_OPTIONS = 'DENY'

EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

CSRF_TRUSTED_ORIGINS = [
    "https://cubecinema.com",
    "https://www.cubecinema.com",
]
