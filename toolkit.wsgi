import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'cube.settings'
sys.path.append(os.path.dirname((os.path.abspath(os.path.dirname(__file__))))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


