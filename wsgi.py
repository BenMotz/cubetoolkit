import os
import sys
import site

VIRTUALENV="venv"

# Get site root from this file's location:
SITE_ROOT=os.path.abspath(os.path.dirname(__file__))

# Add virtualenv path to site package root:
site.addsitedir(os.path.join(SITE_ROOT, VIRTUALENV, "lib/python2.7/site-packages"))
site.addsitedir(os.path.join(SITE_ROOT, VIRTUALENV, "lib/python2.6/site-packages"))

# Add site package root to start of pythonpath:
sys.path.insert(0, SITE_ROOT)

# celery should now be available (on the virtualenv path)
import djcelery
djcelery.setup_loader()

# Point Django to settings file:
os.environ['DJANGO_SETTINGS_MODULE'] = 'toolkit.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
