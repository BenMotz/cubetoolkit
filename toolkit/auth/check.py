import logging
import bcrypt

import django.conf

logger = logging.getLogger(__name__)

def _check_credentials(user, password, authtype):
    """Check the username and password against the supplied authtype.
    authtype is expected to be a tuple:
    ('auth_type' , ('username bcrypt hash', 'password bcrypt hash'))

    Returns True if the user/pw matches, otherwise False.
    """
    if authtype not in django.conf.settings.CUBE_AUTH:
        logger.error("Illegal authtype %s", authtype)
        return False
    logger.info("Credential check for %s with username %s", authtype, user)

    u_hash, p_hash = django.conf.settings.CUBE_AUTH[authtype]

    if p_hash == bcrypt.hashpw(password, p_hash) and u_hash == bcrypt.hashpw(user, u_hash):
        logger.info("Login sucess")
        return True
    else:
        logger.info("Login failed")
        return False

def _set_auth_from_credentials(request, user, password):
    """For the given user/password, set session variables
    for all auth types that match
    (ie. will set read_auth if user/pw matches "read" user/pw)"""
    for credentials in django.conf.settings.CUBE_AUTH:
        if _check_credentials(user, password, credentials):
            session_key = credentials + '_auth'
            request.session[session_key] = True

def _has_auth_any(request, auth_types):
    """Accepts string list/tuple 'auth_types', and checks if the user session
    has auth for any of them.
    Returns True/False
    """
    auth = False
    for auth_type in auth_types:
        session_key = auth_type + '_auth'
        auth = auth or request.session.get(session_key, False)
    return auth

def _has_auth_all(request, auth_types):
    """Accepts string list/tuple 'auth_types', and checks if the user session
    has auth for all of them.
    Returns True/False
    """
    auth = True
    for auth_type in auth_types:
        session_key = auth_type + '_auth'
        auth = auth and request.session.get(session_key, False)
    return auth
