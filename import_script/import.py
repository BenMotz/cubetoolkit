#!/usr/bin/python
import os
import sys
import datetime
import MySQLdb
import re
import logging

import diary.models

FORMATS_PATH="./formats"

MEDIA_PATH = "./media"
EVENT_IMAGES_PATH = "event"
EVENT_THUMB_IMAGES_PATH = "event_thumbnails"

def titlecase(string):
#   return string.title() # Really doesn't cope with apostrophes.
#   return " ".join([ word.capitalize() for word in  "This is the voice".split() ])
    if string is str:
        return re.sub("(^|\s)(\S)", lambda match : match.group(1) + match.group(2).upper(), string)
    else:
        return string

def connect():
    conn = MySQLdb.connect (host = "localhost",
                           user = "cube-import",
                           passwd = "spanner",
                           db = "toolkit",
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
                        rota_entry = diary.models.RotaEntry()
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

        s = diary.models.Showing()
        all_showings.append(s)
        s.event = event
        s.start = r[0]
        if r[2] is not None:
            s.booked_by = titlecase(decode(r[2]))
        
        s.confirmed = bool(r[3])

        if r[4]:
            cancelled_list.append(s)

        s.discounted = bool(r[5])
        aggregate_hire |= bool(r[6])
        if bool(r[7]):
            private_list.append(s)

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

    event.save()

    cursor.close()

    return all_showings

def import_ideas(connection):
    cursor = connection.cursor()
    results = cursor.execute("SELECT date, ideas FROM ideas ORDER BY date")

    for r in cursor.fetchall():
        i, created = diary.models.DiaryIdea.objects.get_or_create(month=r[0])
        i.ideas = decode(r[1])
        i.save()

    cursor.close()

def import_events(connection, role_map):
    cursor = connection.cursor()
    results = cursor.execute("SELECT event_id, event_name, copy, copy_summary, duration, image_credits, terms FROM events ORDER BY event_id")

    count = 0
    tenpc = results / 100
    pc = 1
    logging.info("%d events" % (results))
    for r in cursor.fetchall():
        r = [ decode(item) for item in r ]
        e = diary.models.Event()

        # Name
        e.name = titlecase(r[1])
        # Copy
        if r[2] is not None:
            e.copy = markdown_ify(r[2])
        else:
            logging.error("Missing copy for event [%s] %s", r[0], e.name)
            e.copy = ''
        # Copy summary
        e.copy_summary = r[3]
 
        # Duration:
        if r[4] is not None and r[4] != '':
            durn_hour, durn_min  = r[4].split('/')
            durn_hour = int_def(durn_hour,0)
            durn_min = int_def(durn_min,0)
            e.duration = datetime.time(durn_hour, durn_min) 

        # Image
        image_name = r[0].replace(" ","_") + ".jpg"
        image_path = os.path.join(MEDIA_PATH, EVENT_IMAGES_PATH, image_name)
        if os.path.exists(image_path):
            e.image = os.path.join(EVENT_IMAGES_PATH, image_name)
        # Thumbnail
        image_path = os.path.join(MEDIA_PATH, EVENT_THUMB_IMAGES_PATH, image_name)
        if os.path.exists(image_path):
            e.image_thumbnail = os.path.join(EVENT_THUMB_IMAGES_PATH, image_name)

        # Image credits
        e.image_credit = titlecase(r[5])
        # Terms
        e.terms = r[6]
        e.save()

        showings = import_event_showings(connection, e, r[0])
        import_event_roles(connection, showings, r[0], role_map)

        # Print % progress
        count += 1
        if count % tenpc == 0:
            print ("\x1b[5D%3d%%" % pc),
            pc += 1
            sys.stdout.flush()

    cursor.close()

    logging.info("%d events" % event_tot)

def create_roles(connection):
    roles = []
    cursor = connection.cursor()
    
    count = cursor.execute("SELECT * FROM roles_merged LIMIT 1")
    if count != 1:
        logging.warning("Nothing in the 'roles_merged' table!")
        cursor.close()
        return None 

    for column in cursor.description[1:]:
        role = diary.models.Role()
        role.name = titlecase(column[0]).replace("_", " ")
        role.save()
        logging.info("%s: %d" % (role.name, role.id))
        roles.append(role.id)

    cursor.close()

    return roles

###############################################################################
# Create event templates using dict { event_template_name : [ list of role names] }
def create_event_types(event_types):
    for e_type, roles in event_types.iteritems():
        e_type_o, created = diary.models.EventType.objects.get_or_create(name=e_type)
        if created:
            logging.info("Created event type: %s", e_type)
            e_type_o.shortname = e_type
            e_type_o.save()
        assigned_roles_keys = set([r['pk'] for r in e_type_o.roles.values('pk')])
        for role in roles:
            role = diary.models.Role.objects.get(name=role)
            if role.pk not in assigned_roles_keys:
                logging.info("Adding role %s to %s", role, e_type)
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
    logging.info("Loaded %d event types: %s", len(type_index), ",".join(type_index.keys()))
    return type_index

def main():

    conn = connect()
    # Create roles
    role_map = create_roles(conn)
    # Create event templates
    event_templates = load_event_templates(FORMATS_PATH)
    create_event_types(event_templates)

    if role_map is None:
        return

    import_events(conn, role_map)
    import_ideas(conn)
    conn.close ()


if __name__ == "__main__":
    main()
