import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath("."))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


