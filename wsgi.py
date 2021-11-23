import os

# celery should now be available (on the virtualenv path)
import djcelery

djcelery.setup_loader()

# Point Django to settings file:
os.environ["DJANGO_SETTINGS_MODULE"] = "toolkit.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
