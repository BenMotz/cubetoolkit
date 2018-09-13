'''
Columns in programming_event
id 	title 	summary 	body 	website 	notes 	programmer_id 	confirmed
private 	featured 	picture_id 	approval_id 	startDate 	startTime
endTime 	deleted

Partially inspired by import_script/import_database.py,
buried deep in the history of this repo.
I used d4e9757916fdf0b9aee0c907fd9aee08da922b19
'''

import datetime
import pytz

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import django.utils.timezone

from toolkit.diary.models import Event, EventTag, EventTemplate, Showing, Room

import MySQLdb


class Command(BaseCommand):
    help = "import events from legacy star and shadow django web site"

    def handle(self, *args, **options):

        try:
            self.stdout.write('Connecting to database...')
            db = MySQLdb.connect("localhost",
                                 "starshadow",
                                 "",
                                 "ssarchive")
        except MySQLdb.Error as e:
            self.stdout.write(self.style.ERROR(
                'Failed to connect to archive database'))
            return

        cursor = db.cursor()
        sql = "SELECT * FROM `programming_event` WHERE `deleted` = 0 AND `confirmed` = 1 AND `private` = 0 ORDER BY `startDate` DESC"
        cursor.execute(sql)  # returns number of rows
        events = cursor.fetchall()

        self.stdout.write('Found %d events' % len(events))

        for event in events:
            legacy_id = event[0]
            title = event[1]
            summary = event[2]
            body = event[3]
            website = event[4]
            notes = event[5]
            programmer_id = event[6]
            picture_id = event[10]
            startDate = event[12]  # class 'datetime.date'
            startTime = event[13]  # class 'datetime.timedelta'
            endTime = event[14]
            duration = endTime - startTime  # class datetime.timedelta
            if duration < datetime.timedelta(0):
                duration = datetime.timedelta(0)

            # id bane homePhone mobilePhone email notes user_id photo
            sql = "SELECT * FROM `programming_programmer` WHERE `id` = %d" % programmer_id
            cursor.execute(sql)
            programmer = cursor.fetchone()
            programmerName = programmer[1]
            programmerEmail = programmer[4]

            if picture_id:
                sql = "SELECT `file` FROM `fileupload_picture` WHERE `id` = %d" % picture_id
                cursor.execute(sql)  # returns number of rows
                picture_file = cursor.fetchone()[0]
            else:
                picture_file = ''

            self.stdout.write('%s "%s" %s %s "%s" %s <%s>' % (
                legacy_id,
                title,
                startDate,
                duration,
                picture_file,
                programmerName, programmerEmail
            ))

            duration = (datetime.datetime.min +
                        duration).time()  # class datetime.time
            startDateAsaTime = datetime.datetime.combine(
                startDate,
                datetime.datetime.min.time())
            startDateAsaTime = startDateAsaTime + startTime
            # date = datetime.strptime(startDate + startTime, '%Y-%m-%d %H:%M:%S')

            if picture_id:
                sql = "SELECT `file` FROM `fileupload_picture` WHERE `id` = %d" % picture_id
                cursor.execute(sql)  # returns number of rows
                picture_file = cursor.fetchone()[0]
            else:
                picture_file = ''

            # Attempt to create an cube toolkit style event
            e = Event()
            e.legacy_id = legacy_id
            e.name = title
            e.copy = '%s\n\n%s' % (body, website) or ''
            e.copy_summary = summary or ''
            e.legacy_copy = False
            if programmerEmail is not None and programmerEmail.strip() != '':
                e.notes = "%s\n\nBooked by %s <%s>" % (notes,
                                                       programmerName,
                                                       programmerEmail)
            else:
                e.notes = notes
            e.template = EventTemplate.objects.filter(name='Film (DVD)').first()
            if duration is not None and duration != '':
                e.duration = duration
            else:
                e.duration = datetime.time(0, 0)
            # TODO images
            e.full_clean()
            e.save()
            e.tags.add(EventTag.objects.filter(name='film').first())

            timezone = pytz.timezone("Europe/London")
            fake_start = django.utils.timezone.now() + datetime.timedelta(days=1)

            s = Showing()
            s.event = e
            # The full_clean checks that start is in the future
            # so set a valid start date now, and after the call to
            # full_clean change it to the actual value before saving
            s.start = fake_start
            if programmerName is not None and programmerName.strip() != '':
                s.booked_by = programmerName
            else:
                s.booked_by = 'unknown'
            s.confirmed = True
            s.cancelled = False
            s.discounted = False
            s.room = Room.objects.filter(name='Cinema').first()

            # self.stdout.write('"%s" %s %s %s' % (
            #     s.event.name,
            #     s.start,
            #     s.booked_by,
            #     s.room
            # ))

            s.full_clean()
            # Store datetime with timezone information
            s.start = timezone.localize(startDateAsaTime)
            s.save(force=True)  # Force, to allow saving of showing with start in past

        self.stdout.write(self.style.SUCCESS(
            '%d legacy events imported' % len(events)))

        db.close()
