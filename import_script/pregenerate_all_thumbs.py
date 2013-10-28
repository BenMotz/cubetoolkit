#!/usr/bin/env python
import sys
import logging

from easy_thumbnails.files import generate_all_aliases
from easy_thumbnails.exceptions import InvalidImageFormatError

from toolkit.diary.models import MediaItem
from toolkit.members.models import Volunteer

logger = logging.getLogger('toolkit.import')
logger.setLevel(logging.DEBUG)


def print_percent(pc):
    print ("\x1b[5D%3d%%" % int(pc)),
    sys.stdout.flush()


def gen_catch_exc(field):
    try:
        generate_all_aliases(field, True)
    except InvalidImageFormatError as iife:
        logger.error("Couldn't generate thumbnail(s) for {0}: {1}".format(
            field, iife))


def gen_mediaitem_thumbs():
    items = MediaItem.objects.all()
    total = items.count() / 100.0
    print "Generating thumbnail images for {0} media items".format(total)
    for count, media_item in enumerate(MediaItem.objects.all()):
        if media_item.media_file:
            gen_catch_exc(media_item.media_file)
        else:
            logger.error("Media item without media_file!")
        print_percent(count / total)

def gen_vol_thumbs():
    volunteers = Volunteer.objects.all()
    total = volunteers.count()
    print "Generating thumbnail images for {0} volunteers images".format(total)
    total = total / 100.0
    for count, volunteer in enumerate(volunteers):
        if volunteer.portrait:
            gen_catch_exc(volunteer.portrait)
        print_percent(count / total)


def main():
    gen_vol_thumbs()
    gen_mediaitem_thumbs()

if __name__ == "__main__":
    main()
