import logging

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
        logger.exception(u"Failed to determine mimetype of file {0}".format(source_file.name))
    else:
        try:
            source_file.seek(0)
        except IOError:
            pass

    logger.debug(u"Mime type for {0} detected as {1}".format(source_file.name, mimetype))

    return mimetype
