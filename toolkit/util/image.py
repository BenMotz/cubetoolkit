import logging
import os.path

import magic
import PIL.Image

logger = logging.getLogger(__name__)


class ThumbnailError(Exception):
    pass


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


def generate_thumbnail(source_file, dest_filename, dimensions):
    """
    source_file must be a file object (or compatible)

    If dest_filename doesn't have the correct extension then it will be
    modified. If file already exists it'll be deleted.

    Return value: actual filename written (with correct extension)
    """

    mimetype = get_mimetype(source_file)

    if not mimetype.startswith("image"):
        # Maybe have a default image for audio/video?
        raise ThumbnailError("Creating thumbnails for non-image files not supported at this time")

    # Delete old thumbnail, if any:
    if os.path.exists(dest_filename):
        try:
            logger.debug("File {0} already exists: deleting".format(dest_filename))
            os.unlink(dest_filename)
        except (IOError, OSError):
            logger.exception(u"Failed deleting old thumbnail")
            raise ThumbnailError(u"Failed deleting old thumbnail")

    # Generate thumbnail:
    try:
        image = PIL.Image.open(source_file)
    except (IOError, OSError) as ioe:
        logger.exception(u"Failed to read image file")
        raise ThumbnailError(u"Failed to read image file")
    try:
        image.thumbnail(dimensions, PIL.Image.ANTIALIAS)
    except MemoryError:
        raise ThumbnailError(
            u"Out of memory trying to create thumbnail for {0}".format(source_file.name)
        )
    except (IOError, OSError) as ioe:
        # Empirically, if this happens the thumbnail still gets generated,
        # albeit with some junk at the end. So just log the error and plow
        # on regardless...
        logger.error(u"Error creating thumbnail: {0}".format(ioe))
    finally:
        try:
            source_file.seek(0)
        except IOError:
            pass

    # Make sure thumbnail file ends in jpg, to avoid confusion:
    if os.path.splitext(dest_filename.lower())[1] not in (u'.jpg', u'.jpeg'):
        dest_filename += ".jpg"
    try:
        # Convert image to RGB (can't save Paletted images as jpgs) and
        # save thumbnail as JPEG:
        image.convert("RGB").save(dest_filename, "JPEG")
        logger.info(u"Generated thumbnail for file '{0}' in '{1}'".format(source_file.name, dest_filename))
    except (IOError, OSError) as ioe:
        logger.exception(u"Failed saving thumbnail")
        if os.path.exists(dest_filename):
            try:
                os.unlink(dest_filename)
            except (IOError, OSError):
                pass
        raise ThumbnailError(u"Failed saving thumbnail")

    return dest_filename
