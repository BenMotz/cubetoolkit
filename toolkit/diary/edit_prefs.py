import logging

logger = logging.getLogger(__name__)

KNOWN_PREFS = { 'popups' : True, }

PREF_MAP = { 'false' : False, 'true' : True }

def get_preferences(session):
    edit_prefs = {}
    for pref, default in KNOWN_PREFS.iteritems():
        value = session.get('editpref_' + pref, default)
        if value:
            edit_prefs[pref] = value
    return edit_prefs

def set_preferences(session, prefs_requested):
    for pref in KNOWN_PREFS:
        value = prefs_requested.get(pref, None)
        if value:
            value = str(value)[:10] # limit length of stored value
            logger.debug("User set pref %s = %s", pref, value)
            session['editpref_' + pref] = value

