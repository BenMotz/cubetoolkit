from toolkit.devserver_settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/tmp/test.db",  # Path to database file
        "USER": "",  # Not used with sqlite3.
        "PASSWORD": "",  # Not used with sqlite3.
        "HOST": "",  # Not used with sqlite3.
        "PORT": "",  # Not used with sqlite3.
    }
}

# Different to the key used in production!
SECRET_KEY = "*@t04l3a7+uos5*7=c4ph1t#s(l*tlcdx(n(isztw^4w2c&mu-"

MEDIA_ROOT = "/tmp"

PASSWORD_HASHERS = (
    # For testing use insecure, but much faster, MD5 password hasher:
    "django.contrib.auth.hashers.MD5PasswordHasher",
)

# Minimal logging configuration, that should eat almost everything
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        # NullHandler would be better, but that requires python 2.7
        "console": {
            "level": "CRITICAL",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "CRITICAL",
    },
}
