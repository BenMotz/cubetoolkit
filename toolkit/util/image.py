import colorsys
import logging
import re

import magic

logger = logging.getLogger(__name__)


def get_mimetype(source_file):
    """
    source_file must be a file object (or compatible)

    returns mimetype, or "application/octet-stream" if there's an error
    """

    # Default:
    mimetype = "application/octet-stream"

    magic_wrapper = magic.Magic(mime=True)

    try:
        source_file.seek(0)
        mimetype = magic_wrapper.from_buffer(source_file.read(0xFFF))
    except IOError:
        logger.exception(
            "Failed to determine mimetype of file {0}".format(source_file.name)
        )
    else:
        try:
            source_file.seek(0)
        except IOError:
            pass

    logger.debug(
        "Mime type for {0} detected as {1}".format(source_file.name, mimetype)
    )

    return mimetype


_cached_adjustments = {}


def adjust_colour(colour, lighter_fraction, grayer_fraction):
    result = _cached_adjustments.get(
        (colour, lighter_fraction, grayer_fraction), None
    )
    if result:
        return result

    match = re.match(
        r"^#([A-Fa-f0-9]{2})([A-Fa-f0-9]{2})([A-Fa-f0-9]{2})$", colour
    )
    r, g, b = (int(v, 16) for v in match.groups())
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    new_l = lighter_fraction * (1.0 - l) + l
    s *= grayer_fraction
    r, g, b = colorsys.hls_to_rgb(h, new_l, s)
    result = "#%02X%02X%02X" % (int(r * 0xFF), int(g * 0xFF), int(b * 0xFF))

    _cached_adjustments[(colour, lighter_fraction, grayer_fraction)] = result
    return result
