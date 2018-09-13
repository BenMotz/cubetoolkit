'''# https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/
Columns in programming_event
id 	title 	summary 	body 	website 	notes 	programmer_id 	confirmed
private 	featured 	picture_id 	approval_id 	startDate 	startTime
endTime 	deleted
'''

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from datetime import datetime

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
        sql = "SELECT * FROM `programming_event` WHERE `deleted` = 0 AND `confirmed` = 1 AND `private` = 0"

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
            duration = endTime - startTime
            # date = datetime.strptime(startDate + startTime, '%Y-%m-%d %H:%M:%S')

            if picture_id:
                sql = "SELECT `file` FROM `fileupload_picture` WHERE `id` = %d" % picture_id
                cursor.execute(sql)  # returns number of rows
                picture_file = cursor.fetchone()[0]
            else:
                picture_file = ''

            # id bane homePhone mobilePhone email notes user_id photo
            sql = "SELECT * FROM `programming_programmer` WHERE `id` = %d" % programmer_id
            cursor.execute(sql)
            programmer = cursor.fetchone()
            programmerName = programmer[1]
            programmerEmail = programmer[4]

            self.stdout.write('%s %s %s %s "%s" %s <%s>' % (
                legacy_id,
                title,
                startDate,
                duration,
                picture_file,
                programmerName, programmerEmail
            ))

        self.stdout.write(self.style.SUCCESS(
            '%d legacy events imported' % len(events)))

        db.close()
