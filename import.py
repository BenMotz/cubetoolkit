#!/usr/bin/python
import sys
import datetime
import MySQLdb
import re

import diary.models

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
                           db = "toolkit")
    return conn

def decode(string):
    if string is None:
        return None
    else:
        return string.decode("Windows-1252")

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

event_tot = 0

def import_event_roles(connection, showings, legacy_event_id, role_map):
    cursor = connection.cursor()

    # *cough*
    result_count = cursor.execute("SELECT * from roles_merged WHERE event_id = %s", legacy_event_id)

    for ev in cursor:
        event_id = ev[0]
        col_no = 0
        for role_col in ev[1:]:
            if role_col == 1L:
                for s in showings:
                    rota_entry = diary.models.RotaEntry()
                    rota_entry.role_id = role_map[col_no]

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

def import_events(connection, role_map):
    cursor = connection.cursor()
    results = cursor.execute("SELECT event_id, event_name, copy, copy_summary, duration, image_credits, terms FROM events ORDER BY event_id")

    count = 0
    tenpc = results / 100
    pc = 1
    print "%d results" % (results)
    for r in cursor.fetchall():
        e = diary.models.Event()

        e.name = titlecase(decode(r[1]))
        e.copy = html_ify(decode(r[2]))
        e.copy_summary = decode(r[3])
        
        # Duration:
        if r[4] is not None and r[4] != '':
            durn_hour, durn_min  = decode(r[4]).split('/')
            durn_hour = int_def(durn_hour,0)
            durn_min = int_def(durn_min,0)
            e.duration = datetime.time(durn_hour, durn_min) 

        e.image_credits = titlecase(decode(r[5]))
        e.terms = decode(r[6])
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

    print "%d events" % event_tot

def create_roles(connection):
    roles = []
    cursor = connection.cursor()
    
    count = cursor.execute("SELECT * FROM roles_merged LIMIT 1")
    if count != 1:
        print "Nothing in the 'roles_merged' table!"
        cursor.close()
        return None 

    for column in cursor.description[1:]:
        role = diary.models.Role()
        role.name = titlecase(column[0]).replace("_", " ")
        role.save()
        print "%s: %d" % (role.name, role.id)
        roles.append(role.id)

    cursor.close()

    return roles

def main():
    conn = connect()
    role_map = create_roles(conn)
    if role_map is None:
        return

    import_events(conn, role_map)
    conn.close ()

if __name__ == "__main__":
    main()
