import logging

from django.template import Library

from easy_thumbnails.files import get_thumbnailer

logger = logging.getLogger(__file__)

register = Library()


def thumbnail_url(source, alias):
    """
    Return the thumbnail url for a source file using an aliased set of
    thumbnail options.

    If no matching alias is found, returns an empty string.

    Example usage::

        <img src="{{ person.photo|thumbnail_url:'small' }}" alt="">
    """
    try:
        thumb = get_thumbnailer(source)[alias]
    except Exception:
        logger.exception("Failed generating thumbnail for {0}, {1}"
                         .format(source, alias))
        return ''
    return thumb.url

register.filter(thumbnail_url)
