#!/usr/bin/env python
import os
import sys
#import datetime
#import re
import logging
#import shutil
#
#import pytz

from toolkit.index.models import IndexLink, IndexCategory

logger = logging.getLogger('toolkit.import')
logger.setLevel(logging.INFO)

def add_link(link, description, category):
    #category = IndexCategory.objects.get_or_create(name=category)[0]
    cat_obj = IndexCategory.objects.get_or_create(name=category)[0]
    index_obj, created = IndexLink.objects.get_or_create(
        text=description,
        link=link,
        category=cat_obj
    )
    if created:
        logger.debug("Added link {0} to category {1}".format(link, category))
    else:
        logger.debug("Link {0} already in category {1}".format(link, category))


def import_index(index_filename):
    total = 0
    with open(index_filename, "r") as index_file:
        for count, index_entry in enumerate(index_file):
            parts = index_entry.strip().split("|")
            if len(parts) != 3:
                logger.error("Line {0}: Unrecognised format / extra '|' symbol:\n{1}"
                             .format(count, index_entry))

            category, link, description = parts
            add_link(link, description, category)
            total = count
    return total


def main():
    if len(sys.argv) == 1:
        print "Usage:{0} [Path to index data file]".format(sys.argv[0])
        sys.exit(1)
    index_file = sys.argv[1]
    if not os.path.isfile(index_file):
        print "{0} is not a valid path to a directory".format(index_file)
        sys.exit(2)

    logger.info("Importing index links from {0}".format(index_file))
    count = import_index(index_file)
    logger.info("Imported {0} links".format(count))


if __name__ == "__main__":
    main()
