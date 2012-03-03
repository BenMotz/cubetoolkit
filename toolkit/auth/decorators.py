"""Decorators that can be applied to view methods to restrict access"""
import logging
import functools

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

# Use these decorators on view methods to restrict access as indicated.
#
# If authorisation has not been acquired, stores the original request path 
# and redirects to the login page.

logger = logging.getLogger(__name__)

def require_read_auth(function):
    """Decorator to apply to views that require the user to have provided the
    "read" (or write) password"""
    @functools.wraps(function)
    def req_read_auth_wrapper(request, *args, **kwargs):
        # Read *or* write auth:
        auth = request.session.get('read_auth', False) or request.session.get('write_auth', False)
        if auth:
            return function(request, *args, **kwargs)
        else:
            logger.info("Read access denied to %s.", function.__name__)
            # Store the original destination, before redirecting to the auth
            request.session['next'] = request.path
            return HttpResponseRedirect(reverse('auth', kwargs={'atype' : 'read'}))
    return req_read_auth_wrapper

def require_write_auth(function):
    """Decorator to apply to views that require the user to have provided the
    "write" password"""
    @functools.wraps(function)
    def req_write_auth_wrapper(request, *args, **kwargs):
        auth = request.session.get('write_auth', False)
        if auth:
            return function(request, *args, **kwargs)
        else:
            logger.info("Write access denied to %s.", function.__name__)
            # Store the original destination, before redirecting to the auth
            request.session['next'] = request.path
            return HttpResponseRedirect(reverse('auth', kwargs={'atype' : 'write'}))
    return req_write_auth_wrapper

