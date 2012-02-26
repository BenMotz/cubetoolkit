#!/usr/bin/python
import os
import sys
import datetime
import MySQLdb
import re
import logging

import toolkit.diary.models
import toolkit.members.models
import settings
from django.core.exceptions import ValidationError

FORMATS_PATH="./formats"

SITE_ROOT = ".."
MEDIA_PATH = "media"
EVENT_IMAGES_PATH = "diary"
EVENT_THUMB_IMAGES_PATH = "diary_thumbnails"
VOLUNTEER_IMAGE_PATH = "volunteers"
VOLUNTEER_IMAGE_THUMB_PATH = "volunteers_thumbnails"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Set up logging:
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
logger.addHandler(consoleHandler)

def titlecase(string):
#   return string.title() # Really doesn't cope with apostrophes.
#   return " ".join([ word.capitalize() for word in  "This is the voice".split() ])
    if string is str:
        return re.sub("(^|\s)(\S)", lambda match : match.group(1) + match.group(2).upper(), string)
    else:
        return string

def connect():
    conn = MySQLdb.connect (host = "localhost",
                            user = settings.IMPORT_SCRIPT_USER,
                           passwd = "spanner",
                           db = settings.IMPORT_SCRIPT_DATABASE,
#                           use_unicode = True,
                           )
    return conn

def decode(string):
    if string is str:
        return string.decode('utf-8')
    else:
        return string

def int_def(string, default):
    try:
        return int(string)
    except ValueError:
        return default

def html_ify(string):
    result = None
    if string is not None:
        result = "<p>" + string.strip().replace("\r\n","<br>") + "</p>"
    return result

def markdown_ify(string):
    return string

event_tot = 0

def import_event_roles(connection, showings, legacy_event_id, role_map):
    cursor = connection.cursor()

    # *cough*
    cursor.execute("SELECT * from roles_merged WHERE event_id = %s", legacy_event_id)

    for ev in cursor:
        # event_id = ev[0]
        col_no = 0
        for role_col in ev[1:]:
            if role_col is not None:
                for rank in range(0,role_col):
                    for s in showings:
                        rota_entry = toolkit.diary.models.RotaEntry()
                        rota_entry.role_id = role_map[col_no]
                        rota_entry.rank = rank + 1

                        rota_entry.showing_id = s.id
                        rota_entry.save()
            col_no += 1

    cursor.close()

def import_event_showings(connection, event, legacy_event_id):
    global event_tot
    # Some slightly funky logic to do the mapping:
    #
    aggregate_hire = False
    cancelled_list = []
    private_list = []

    all_showings = []


    cursor = connection.cursor()
    showing_count = cursor.execute("SELECT datetime, event_id, booked_by, confirmed, cancelled, discounted, outside_hire, private_event FROM diary WHERE event_id = '%s' ORDER BY datetime" % legacy_event_id)
    event_tot += showing_count

    results = cursor.fetchall()

    for r in results:

        s = toolkit.diary.models.Showing()
        all_showings.append(s)
        s.event = event
        s.start = r[0]
        if r[2] is not None and r[2].strip() != '':
            s.booked_by = titlecase(decode(r[2]))
        else:
            s.booked_by = 'unknown'

        s.confirmed = bool(r[3])

        if r[4]:
            cancelled_list.append(s)

        s.discounted = bool(r[5])
        aggregate_hire |= bool(r[6])
        if bool(r[7]):
            private_list.append(s)

        s.full_clean()
        s.save()

    if len(cancelled_list) == showing_count:
        event.cancelled = True
    else:
        for cancelled_showing in cancelled_list:
            cancelled_showing.cancelled = True
            cancelled_showing.save()

    if len(private_list) == showing_count:
        event.private = True
    else:
        for hidden_showing in private_list:
            hidden_showing.hide_in_programme = True
            hidden_showing.save()

    event.outside_hire = aggregate_hire

    event.full_clean()
    event.save()

    cursor.close()

    return all_showings

def import_ideas(connection):
    cursor = connection.cursor()
    results = cursor.execute("SELECT date, ideas FROM ideas ORDER BY date")

    for r in cursor.fetchall():
        i, created = toolkit.diary.models.DiaryIdea.objects.get_or_create(month=r[0])
        i.ideas = decode(r[1])
        i.full_clean()
        i.save()

    cursor.close()

def import_events(connection, role_map):
    cursor = connection.cursor()
    results = cursor.execute("SELECT event_id, event_name, copy, copy_summary, duration, image_credits, terms FROM events ORDER BY event_id")

    count = 0
    tenpc = results / 100
    pc = 1
    logger.info("%d events" % (results))
    for r in cursor.fetchall():
        r = [ decode(item) for item in r ]
        e = toolkit.diary.models.Event()
        e.legacy_id = r[0]

        # Name
        e.name = titlecase(r[1])
        if e.name in (None, u''):
            # Looking at the db, it's safe to skip all of these
            logging.error("Skipping event with no/missing name id %s", e.legacy_id)
            continue
        # Copy
        if r[2] is not None:
            e.copy = markdown_ify(r[2])
        else:
            logger.error("Missing copy for event [%s] %s", r[0], e.name)
            e.copy = ''
        # Copy summary
        e.copy_summary = r[3]

        # Duration:
        if r[4] is not None and r[4] != '':
            durn_hour, durn_min  = r[4].split('/')
            durn_hour = int_def(durn_hour,0)
            durn_min = int_def(durn_min,0)
            e.duration = datetime.time(durn_hour, durn_min)
        else:
            e.duration = datetime.time(0,0)

        # Terms
        e.terms = r[6]
        try:
            e.full_clean()
            e.save()
        except ValidationError as verr:
            logger.error("Failed to add event id %s: %s", e.legacy_id, str(verr))
            continue

        # Image
        image_name = r[0].replace(" ","_") + ".jpg"
        image_path = os.path.join(SITE_ROOT, MEDIA_PATH, EVENT_IMAGES_PATH, image_name)
        if os.path.exists(image_path):
            # File exists, change path to relative to media root, as django expects
            image_path = os.path.join(EVENT_IMAGES_PATH, image_name)
        else:
            image_path = None
        # Thumbnail
        image_thumbnail_path = os.path.join(SITE_ROOT, MEDIA_PATH, EVENT_THUMB_IMAGES_PATH, image_name)
        if image_path and os.path.exists(image_thumbnail_path):
            # As above, change path to relative to media root, as django expects
            image_thumbnail_path = os.path.join(EVENT_THUMB_IMAGES_PATH, image_name)
        else:
            image_thumbnail_path = None
        # If either image or thumbnail existed, create media item:
        if image_path or image_thumbnail_path:
            # Image credits
            image_credit = titlecase(r[5])
            media_item = toolkit.diary.models.MediaItem(media_file=image_path, thumbnail=image_thumbnail_path, credit=image_credit)
            media_item.full_clean()
            media_item.save(update_thumbnail=False)
            e.media.add(media_item)

        showings = import_event_showings(connection, e, r[0])
        import_event_roles(connection, showings, r[0], role_map)

        # Print % progress
        count += 1
        if count % tenpc == 0:
            print ("\x1b[5D%3d%%" % pc),
            pc += 1
            sys.stdout.flush()

    cursor.close()

    logger.info("%d events" % event_tot)

def create_roles(connection):
    roles = []
    cursor = connection.cursor()

    count = cursor.execute("SELECT * FROM roles_merged LIMIT 1")
    if count != 1:
        logger.warning("Nothing in the 'roles_merged' table!")
        cursor.close()
        return None

    for column in cursor.description[1:]:
        role = toolkit.diary.models.Role()
        role.name = titlecase(column[0]).replace("_", " ")
        role.save()
        logger.info("%s: %d" % (role.name, role.id))
        roles.append(role.id)

    cursor.close()

    return roles

###############################################################################
# Create event templates using dict { event_template_name : [ list of role names] }
def create_event_types(event_types):
    for e_type, roles in event_types.iteritems():
        e_type_o, created = toolkit.diary.models.EventTemplate.objects.get_or_create(name=e_type)
        if created:
            logger.info("Created event type: %s", e_type)
            e_type_o.shortname = e_type
            e_type_o.save()
        assigned_roles_keys = set([r['pk'] for r in e_type_o.roles.values('pk')])
        for role in roles:
            role = toolkit.diary.models.Role.objects.get(name=role)
            if role.pk not in assigned_roles_keys:
                logger.info("Adding role %s to %s", role, e_type)
                e_type_o.roles.add(role)

# Read event templates from given path
def load_event_templates(path_to_formats):
    def clean(string):
        return string.strip().replace("_", " ")

    type_index = {}
    for root, dirs, files in os.walk(path_to_formats):
        for event_type in files:
            role_list = []
            with open(os.path.join(root, event_type), "r") as role_list_file:
                for line in role_list_file:
                    role_list.append(clean(line))
            type_index[clean(event_type)] = role_list
    logger.info("Loaded %d event types: %s", len(type_index), ",".join(type_index.keys()))
    return type_index

def create_default_tags():
    tags = ('film', 'music', 'party', 'cabaret', 'indymedia', 'talk', 'nanoplex', 'hkkp', 'bluescreen', 'meeting', 'cubeorchestra', 'babycinema')
    for tag in tags:
        t = toolkit.diary.models.EventTag(name=tag, read_only=True)
        t.save()

###############################################################################
# Members + Volunteers...

def import_volunteer_roles(volunteer):
    pass

def import_volunteer(member, active, notes):
    v = toolkit.members.models.Volunteer()
    v.member = member
    v.active = active
    v.notes = notes

    # Image
    image_name = member.legacy_id + ".jpg"
    image_path = os.path.join(SITE_ROOT, MEDIA_PATH, VOLUNTEER_IMAGE_PATH, image_name)
    if os.path.exists(image_path):
        # File exists, change path to relative to media root, as django expects
        image_path = os.path.join(VOLUNTEER_IMAGE_PATH, image_name)
        v.portrait = image_path
    # Thumbnail
    image_thumbnail_path = os.path.join(SITE_ROOT, MEDIA_PATH, VOLUNTEER_IMAGE_THUMB_PATH, image_name)
    if image_path and os.path.exists(image_thumbnail_path):
        # As above, change path to relative to media root, as django expects
        image_thumbnail_path = os.path.join(VOLUNTEER_IMAGE_THUMB_PATH, image_name)
        v.portrait_thumb = image_thumbnail_path

    v.full_clean()
    import_volunteer_roles(v)
    v.save()

def import_members(connection):
    cursor = connection.cursor()
    results = cursor.execute("SELECT members.member_id, name, email, homepage, address, city, postcode, country, landline, mobile, last_updated, refuse_mailshot, status, notes FROM members LEFT JOIN notes ON members.member_id = notes.member_id WHERE members.name != '' ORDER BY member_id")
    # Don't even try to import members with blank names

    count = 0
    tenpc = results / 100
    pc = 1
    logger.info("%d members" % (results))
    for r in cursor.fetchall():
        r = [ decode(item) for item in r ]
        m = toolkit.members.models.Member()
        m.legacy_id = r[0][:10]
        m.name = r[1]
        m.email = r[2]
        m.website = r[3]
        m.address = r[4]
        m.posttown = r[5]
        m.postcode = r[6]
        m.country = r[7]
        m.phone = r[8]
        m.altphone = r[9]
        if r[10] == 'member removed self':
            m.mailout = False
        elif r[10] != None and r[10] != '':
            m.mailout = False
            m.mailout_failed = True
        try:
            m.full_clean()
            m.save()
        except ValidationError as ve:
            logging.error("Failed saving member %s: %s", m.legacy_id, str(ve))

        #   Get everyone who's plausibly a volunteer:
        #        SELECT members.name, members.status, notes.* FROM notes JOIN members on notes.member_id = members.member_id ORDER BY status, name;
        #  Then again... summon up a whole world of munged pain:
        # SELECT members.name, members.status, members.member_id, notes.notes from members left join notes on members.member_id = notes.member_id where members.status != '' and members.status != 'normal' and members.status != 'not member'  order by name LIMIT 1000;

        # Complete member join:
        # SELECT members.member_id, name, email, homepage, address, city, postcode, country, landline, mobile, last_updated, refuse_mailshot, status, notes, vol_roles_merged.* FROM members LEFT JOIN notes on members.member_id = notes.member_id LEFT JOIN vol_roles_merged on vol_roles_merged.member_id = members.member_id ORDER BY members.member_id LIMIT 1000

        # From which we conclude:
        status = r[11]
        if 'retired' in status or 'disgraced' in status or 'ex-voluneer' in status:
            # they're an ex-volunteer:
            import_volunteer(m, False, r[12])
        elif 'volunteer' in status:
            # they're a current volunteer:
            import_volunteer(m, True, r[12])
        else:
            pass

        # Print % progress
        count += 1
        if count % tenpc == 0:
            print ("\x1b[5D%3d%%" % pc),
            pc += 1
            sys.stdout.flush()

    cursor.close()

    logger.info("%d members" % count)

def main():
    global SITE_ROOT
    if len(sys.argv) == 1:
        print "Usage: {0} [Path to site root]".format(sys.argv[0])
        sys.exit(1)
    SITE_ROOT = sys.argv[1]
    if not os.path.isdir(SITE_ROOT):
        print "{0} is not a valid path to a directory".format(SITE_ROOT)
        sys.exit(2)

    conn = connect()
    # Create roles
    role_map = create_roles(conn)
    # Create event templates
    event_templates = load_event_templates(FORMATS_PATH)
    create_event_types(event_templates)
    # Create default tags
    create_default_tags()

    if role_map is None:
        return

    import_events(conn, role_map)
    import_ideas(conn)
    import_members(conn)
    conn.close ()

if __name__ == "__main__":
    main()
