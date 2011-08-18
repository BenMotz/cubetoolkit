#!/usr/bin/python
import sys
import datetime
import MySQLdb

import diary.models

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

def import_event_showings(connection, event, legacy_event_id):
    global event_tot
    # Some slightly funky logic to do the mapping:
    #
    aggregate_hire = False 
    cancelled_list = []
    private_list = []
    

    cursor = connection.cursor()
    showing_count = cursor.execute("SELECT datetime, event_id, booked_by, confirmed, cancelled, discounted, outside_hire, private_event FROM diary WHERE event_id = '%s' ORDER BY datetime" % legacy_event_id)
    event_tot += showing_count

    results = cursor.fetchall()
    
    for r in results:

        s = diary.models.Showing()
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

def import_event_roles():
    pass

def import_events(connection):
    cursor = connection.cursor()
    results = cursor.execute("SELECT event_id, event_name, copy, copy_summary, duration, image_credits, terms FROM events ORDER BY event_id")

    count = 0
    tenpc = results / 100
    pc = 1
    print "%d results" % (results)
    for r in cursor.fetchall():
        e = diary.models.Event()

        e.name = decode(r[1])
        e.copy = html_ify(decode(r[2]))
        e.copy_summary = decode(r[3])
        
        # Duration:
        if r[4] is not None and r[4] != '':
            durn_hour, durn_min  = decode(r[4]).split('/')
            durn_hour = int_def(durn_hour,0)
            durn_min = int_def(durn_min,0)
            e.duration = datetime.time(durn_hour, durn_min) 

        e.image_credits = decode(r[5])
        e.terms = decode(r[6])
        e.save()

        import_event_showings(connection, e, r[0])

        # Print % progress
        count += 1
        if count % tenpc == 0:
            print ("\x1b[5D%3d%%" % pc),
            pc += 1
            sys.stdout.flush()

    cursor.close()

    print "%d events" % event_tot


def main():
    conn = connect()
    import_events(conn)
    conn.close ()

if __name__ == "__main__":
    main()
