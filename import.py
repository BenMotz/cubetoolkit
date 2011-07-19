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

def import_event_showings(connection, event):
    cursor = connection.cursor()
    results = cursor.execute("SELECT datetime, event_id, booked_by, confirmed, cancelled, discounted, outside_hire, private_event FROM diary WHERE event_id = %d" % event.id)
    
    for r in cursor.fetchall():
        s = diary.models.Showing()
        s.event = event
        s.start = r[0]

        s.save()

    cursor.close()

def import_events(connection):
    cursor = connection.cursor()
    results = cursor.execute("SELECT event_id, event_name, copy, copy_summary, duration, image_credits, terms FROM events")

    count = 0
    tenpc = results / 10
    print "%d results, . every %d" % (results, tenpc)
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

        import_event_showings(connection, e)

        count += 1

        if count % tenpc == 0:
            print ".",
            sys.stdout.flush()

    cursor.close()


def main():
    conn = connect()
    import_events(conn)
    conn.close ()

if __name__ == "__main__":
    main()
