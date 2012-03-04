"""Decorators that can be applied to view methods to restrict access"""
import logging
import functools

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import toolkit.auth.check as check

# Use these decorators on view methods to restrict access as indicated.
#
# If authorisation has not been acquired, stores the original request path 
# and redirects to the login page.

logger = logging.getLogger(__name__)

def require_auth_any(*auth_types):
    """Decorator to apply to views, to check if current session has any of the
    required auth_types (auth_types is a list).
    If not, redirects to login page (storing the current request URL, but not
    POST parameters, to use if auth succeeds)
    """
    def wrapper_generator(function):
        @functools.wraps(function)
        def check_auth_wrapper(request, *args, **kwargs):
            auth = False
            auth = check._has_auth_any(request, auth_types)
            if auth:
                return function(request, *args, **kwargs)
            else:
                logger.info("Access denied (unauthorised for %s) to %s.", ",".join(auth_types), function.__name__)
                # Store the original destination, before redirecting to the auth
                request.session['next'] = request.path
                return HttpResponseRedirect(reverse('auth', kwargs={'atype' : ",".join(auth_types)}))
        return check_auth_wrapper
    return wrapper_generator

def require_read_auth(function):
    """Decorator to apply to views that require the user to have provided the
    "read" password"""
    return require_auth_any('read')

def require_write_auth(function):
    """Decorator to apply to views that require the user to have provided the
    "write" password"""
    return require_auth_any('write')

def require_read_or_write_auth(function):
    """Decorator to apply to views that require the user to have provided
    either the "read" or "write" password"""
    return require_auth_any('read', 'write')

