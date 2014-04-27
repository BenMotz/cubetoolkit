import logging

logger = logging.getLogger(__name__)

# Set of known preferences and default values:
KNOWN_PREFS = {
    'popups': 'true',
    'daysahead': '90',
}


def get_preferences(session):
    edit_prefs = dict(
        (pref, session.get('editpref_' + pref, default))
        for pref, default in KNOWN_PREFS.iteritems()
    )
    return edit_prefs


def get_preference(session, name):
    value = None
    if name in KNOWN_PREFS:
        value = session.get('editpref_' + name, KNOWN_PREFS[name])
    return value


def set_preferences(session, prefs_requested):
    for name, value in prefs_requested.iteritems():
        set_preference(session, name, value)


def set_preference(session, name, value):
    if name in KNOWN_PREFS:
        logger.debug("Set pref {0} to '{1}'".format(name, value))
        value = str(value)[:10]  # limit length of stored value
        session['editpref_' + name] = value
