import os

from toolkit.settings_common import *

ALLOWED_HOSTS = ["localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "toolkit"),
        "USER": os.environ.get("DB_USER", "toolkit"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "devserver_db_password"),
        "HOST": os.environ.get("DB_HOST", "mysql"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "CONN_MAX_AGE": 10,  # Allow DB connections to persist for 10 seconds
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

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
