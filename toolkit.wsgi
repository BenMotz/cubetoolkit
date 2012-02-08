import os
import sys
import site

VIRTUALENV="venv"

# Get site root from this file's location:
SITE_ROOT=os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Add virtualenv path to site package root:
site.addsitedir(os.path.join(SITE_ROOT, VIRTUALENV))

# Add site package root to start of pythonpath:
sys.path.insert(0, SITE_ROOT)

# Point Django to settings file:
os.environ['DJANGO_SETTINGS_MODULE'] = 'toolkit.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


