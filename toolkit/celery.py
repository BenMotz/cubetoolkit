from __future__ import absolute_import

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toolkit.settings")

from django.conf import settings  # noqa

app = Celery("toolkit")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERY_RESULT_BACKEND="djcelery.backends.database:DatabaseBackend",
    BROKER_URL="django://",
    # Configure to not use 'pickle' serialisation (which is deprecated):
    CELERY_ACCEPT_CONTENT=["json", "msgpack", "yaml"],
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
)
