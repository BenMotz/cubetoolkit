import os.path
# import re
# import magic
import PIL.Image
import logging

from django.conf import settings
from django.db import models

from toolkit.diary.models import Role

logger = logging.getLogger(__name__)


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

    mailout = models.BooleanField(default=True)
    mailout_failed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    portrait = models.ImageField(upload_to="volunteers", max_length=256, null=True, blank=True)
    portrait_thumb = models.ImageField(upload_to="volunteers_thumbnails", max_length=256,
                                       null=True, blank=True, editable=False)

    # Roles
    roles = models.ManyToManyField(Role, db_table='Volunteer_Roles', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Volunteers'

    def save(self, *args, **kwargs):
        # Before saving, if portrait has changed:
        update_thumbnail = kwargs.pop('update_portrait_thumbnail', False)

        result = super(Volunteer, self).save(*args, **kwargs)

        try:
            current_portrait_file = self.portrait.file.name
        except (IOError, OSError, ValueError):
            current_portrait_file = None

        if current_portrait_file != self.original_portrait:
            # Delete old image:
            if self.original_portrait:
                logging.info("Deleting old volunteer portrait '%s'", self.original_portrait)
                try:
                    os.unlink(self.original_portrait)
                except (IOError, OSError) as err:
                    logging.error("Failed deleting old volunteer portrait '%s': %s", self.original_portrait, err)
                self.original_portrait = None
            # update thumbnail (after save, to ensure image has been written to disk)
            if update_thumbnail:
                self.update_portrait_thumbnail()
        return result

    def __init__(self, *args, **kwargs):
        super(Volunteer, self).__init__(*args, **kwargs)
        try:
            self.original_portrait = self.portrait.file.name if self.portrait else None
        except (IOError, OSError, ValueError):
            self.original_portrait = None

    def update_portrait_thumbnail(self):
        # Delete old thumbnail, if any:
        if self.portrait_thumb and self.portrait_thumb != '':
            logger.info("Deleting old portrait thumbnail for {0}, file {1}".format(self.pk, self.portrait_thumb))
            try:
                self.portrait_thumb.delete(save=False)
            except (IOError, OSError) as ose:
                logger.exception("Failed deleting old thumbnail: {0}".format(ose))

        # If there's not actually a new image to thumbnail, give up:
        if self.portrait is None or self.portrait == '':
            return

        try:
            if not os.path.isfile(self.portrait.file.name):
                return
        except (OSError, IOError) as err:
            logger.error("Failed detecting if portrait exists and is a file (%s): %s", self.portrait.file.name, err)
            return

        try:
            image = PIL.Image.open(self.portrait.file.name)
        except (IOError, OSError) as ioe:
            logger.error("Failed to read image file {0}: {1}".format(self.portrait.file.name, ioe))
            return
        try:
            image.thumbnail(settings.THUMBNAIL_SIZE, PIL.Image.ANTIALIAS)
        except MemoryError:
            logger.error("Out of memory trying to create thumbnail for {0}".format(self.portrait))

        thumb_file = os.path.join(settings.MEDIA_ROOT, "volunteers_thumbnails", os.path.basename(str(self.portrait)))

        # Make sure thumbnail file ends in jpg, to avoid confusion:
        if os.path.splitext(thumb_file.lower())[1] not in (u'.jpg', u'.jpeg'):
            thumb_file += ".jpg"
        try:
            # Convert image to RGB (can't save Paletted images as jpgs) and
            # save thumbnail as JPEG:
            image.convert("RGB").save(thumb_file, "JPEG")
            logger.info("Generated thumbnail portrait for volunteer '%s' in file '%s'", self.pk, thumb_file)
        except (IOError, OSError) as ioe:
            logger.error("Failed saving thumbnail: {0}".format(ioe))
            if os.path.exists(thumb_file):
                try:
                    os.unlink(thumb_file)
                except (IOError, OSError) as ioe:
                    pass
            return
        self.portrait_thumb = os.path.relpath(thumb_file, settings.MEDIA_ROOT)
        self.save(update_portrait_thumbnail=False)
