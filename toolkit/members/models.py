import os.path
import PIL.Image
import logging

import django.db  # Used for raw query for stats
from django.conf import settings
from django.db import models

from toolkit.diary.models import Role
from toolkit.util import generate_random_string

logger = logging.getLogger(__name__)


class MemberManager(models.Manager):
    # Used with Member class, to encapsulate logic about selecting which
    # members should get the mailout, and other such things

    def mailout_recipients(self):
        """Get all members who should be sent the mailout"""
        return (self.filter(email__isnull=False)
                    .exclude(email='')
                    .exclude(mailout_failed=True)
                    .filter(mailout=True))

    # A few hard-coded SQL queries to get some of the more complex statistics:
    def get_stat_popular_email_domains(self):
        # Get 10 most popular email domains
        cursor = django.db.connection.cursor()
        cursor.execute("SELECT "
                       "   SUBSTRING_INDEX(`email`, '@', -1) AS domain, "
                       "   COUNT(1) AS num "
                       "FROM Members "
                       "WHERE email != '' "
                       "GROUP BY domain "
                       "ORDER BY num DESC "
                       "LIMIT 10")
        email_stats = [row for row in cursor.fetchall()]
        cursor.close()
        return email_stats

    def get_stat_popular_postcode_prefixes(self):
        # Get 10 most popular postcode prefixes
        cursor = django.db.connection.cursor()
        cursor.execute("SELECT "
                       "    SUBSTRING_INDEX(`postcode`, ' ', 1) AS firstbit, "
                       "     COUNT(1) AS num "
                       "FROM Members "
                       "WHERE postcode != '' "
                       "GROUP BY firstbit "
                       "ORDER BY num DESC "
                       "LIMIT 10")
        postcode_stats = [row for row in cursor.fetchall()]
        cursor.close()
        return postcode_stats


class Member(models.Model):

    # This is the primary key used in the old perl/bdb system, used as the
    # user-facing membership number (rather than using the private key).
    # Defaults to = pk. Note; not actually a number!
    number = models.CharField(max_length=10, editable=False)

    name = models.CharField(max_length=64)
    email = models.CharField(max_length=64, blank=True, null=True)  # , unique=True)

    address = models.CharField(max_length=128, blank=True, null=True)
    posttown = models.CharField(max_length=64, blank=True, null=True)
    postcode = models.CharField(max_length=16, blank=True, null=True)
    country = models.CharField(max_length=32, blank=True, null=True)

    website = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=64, blank=True, null=True)
    altphone = models.CharField(max_length=64, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    is_member = models.BooleanField(default=True)

    mailout = models.BooleanField(default=True)
    mailout_failed = models.BooleanField(default=False)
    # Used for "click to unsubscribe"/"edit details" etc:
    mailout_key = models.CharField(max_length=32, blank=False, null=False, editable=False,
                                   default=generate_random_string)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager, includes helpful methods for selecting members:
    objects = MemberManager()

    class Meta:
        db_table = 'Members'

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If a user number hasn't been set, save a placeholder, then re-save
        # with the private key as the number:
        set_number = False
        if self.number == '':
            set_number = True
            self.number = "?"

        result = super(Member, self).save(*args, **kwargs)

        if set_number:
            self.number = str(self.pk)
            self.save()

        return result

#    weak_email_validator = re.compile("""\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b""")
#    def weak_validate_email(self):
#        pass


class Volunteer(models.Model):

    member = models.OneToOneField('Member', related_name='volunteer')

    notes = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    portrait = models.ImageField(upload_to=settings.VOLUNTEER_PORTRAIT_DIR, max_length=256, null=True, blank=True)
    portrait_thumb = models.ImageField(upload_to=settings.VOLUNTEER_PORTRAIT_PREVIEW_DIR, max_length=256,
                                       null=True, blank=True, editable=False)

    # Roles
    roles = models.ManyToManyField(Role, db_table='Volunteer_Roles', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Volunteers'

    def save(self, *args, **kwargs):
        # Save the model.
        # If the filename of the 'portrait' has changed then regenerate the
        # thumbnail. (This means the thumbnail won't get updated if the filename
        # hasn't changed, but that shouldn't be the end of the world?)
        update_thumbnail = kwargs.pop('update_portrait_thumbnail', True)

        try:
            current_portrait_file = self.portrait.file.name
        except (IOError, OSError, ValueError):
            current_portrait_file = None

        if current_portrait_file != self.__original_portrait:
            # Delete old image:
            if self.__original_portrait:
                logging.info(u"Deleting old volunteer portrait '{0}'".format(self.__original_portrait))
                try:
                    os.unlink(self.__original_portrait)
                except (IOError, OSError) as err:
                    logging.error(u"Failed deleting old volunteer portrait '{0}': {1}"
                                  .format(self.__original_portrait, err))
                self.__original_portrait = None
            # update thumbnail
            if update_thumbnail:
                self._update_portrait_thumbnail()

        return super(Volunteer, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(Volunteer, self).__init__(*args, **kwargs)
        # Store current filename of portrait (if any) so that, at save, changes
        # can be detected and the thumbnail updated:
        try:
            self.__original_portrait = self.portrait.file.name if self.portrait else None
        except (IOError, OSError, ValueError):
            self.__original_portrait = None

    def _update_portrait_thumbnail(self):
        # Delete old thumbnail, if any:
        if self.portrait_thumb and self.portrait_thumb != '':
            logger.info(u"Deleting old portrait thumbnail for {0}, file {1}".format(self.pk, self.portrait_thumb))
            try:
                self.portrait_thumb.delete(save=False)
            except (IOError, OSError) as ose:
                logger.exception(u"Failed deleting old thumbnail: {0}".format(ose))

        # If there's not actually a new image to thumbnail, give up:
        if self.portrait is None or self.portrait == '':
            self.portrait_thumb = ''
            return

        try:
            image = PIL.Image.open(self.portrait.file)
        except (IOError, OSError) as ioe:
            logger.error(u"Failed to read image file {0}: {1}".format(self.portrait.file.name, ioe))
            return
        try:
            image.thumbnail(settings.THUMBNAIL_SIZE, PIL.Image.ANTIALIAS)
        except MemoryError:
            logger.error(u"Out of memory trying to create thumbnail for {0}".format(self.portrait))
        except (IOError, OSError) as ioe:
            # Emperically, if this happens the thumbnail still gets generated,
            # albeit with some junk at the end. So just log the error and plow
            # on regardless...
            logger.error(u"Error creating thumbnail: {0}".format(ioe))

        thumb_file = os.path.join(
            settings.MEDIA_ROOT,
            settings.VOLUNTEER_PORTRAIT_PREVIEW_DIR,
            os.path.basename(str(self.portrait))
        )
        # Make sure thumbnail file ends in jpg, to avoid confusion:
        if os.path.splitext(thumb_file.lower())[1] not in (u'.jpg', u'.jpeg'):
            thumb_file += ".jpg"
        try:
            # Convert image to RGB (can't save Paletted images as jpgs) and
            # save thumbnail as JPEG:
            image.convert("RGB").save(thumb_file, "JPEG")
            logger.info(u"Generated thumbnail portrait for volunteer '{0}' in file '{1}'".format(self.pk, thumb_file))
        except (IOError, OSError) as ioe:
            logger.error(u"Failed saving thumbnail: {0}".format(ioe))
            if os.path.exists(thumb_file):
                try:
                    os.unlink(thumb_file)
                except (IOError, OSError) as ioe:
                    pass
            return
        self.portrait_thumb = os.path.relpath(thumb_file, settings.MEDIA_ROOT)
