import logging
import os.path
import datetime

import magic
import PIL.Image

from django.db import models
import django.conf
import django.core.exceptions

logger = logging.getLogger(__name__)

from toolkit.diary.validators import validate_in_future

class FutureDateTimeField(models.DateTimeField):
    """DateTime field that can only be set to times in the future.
    Used for Showing start times"""
    default_error_messages = {
            'invalid': 'Date may not be in the past',
    }
    default_validators = [ validate_in_future ]


class Role(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=64, null=True, blank=True)
    shortcode = models.CharField(max_length=8, null=True, blank=True, unique=True)

    # Can this role be added to the rota?
    rota = models.BooleanField(default=False)

    class Meta:
        db_table = 'Roles'

    def __unicode__(self):
        return self.name


class MediaItem(models.Model):
    """Media (eg. video, audio, html fragment?). Currently to be assoicated
    with events, in future with other things?"""

    media_file = models.FileField(upload_to="diary", max_length=256, null=True, blank=True, verbose_name='Image file')
    mimetype = models.CharField(max_length=64, editable=False)

    thumbnail = models.ImageField(upload_to="diary_thumbnails", max_length=256, null=True, blank=True, editable=False)
    credit = models.CharField(max_length=256, null=True, blank=True,
                              default="Internet scavenged", verbose_name='Image credit')
    caption = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        db_table = 'MediaItems'

    # Overloaded Django ORM method:

    def save(self, *args, **kwargs):
        # Before saving, update thumbnail and mimetype
        self.autoset_mimetype()
        update_thumbnail = kwargs.pop('update_thumbnail', True)
        result = super(MediaItem, self).save(*args, **kwargs)
        # Update thumbnail after save, to ensure image has been written to disk
        if update_thumbnail:
            self.update_thumbnail()
        return result

    # Extra, custom methods:

    def autoset_mimetype(self):
        # See lib/python2.7/site-packages/django/forms/fields.py for how to do
        # basic validation of PNGs / JPEGs
        # logging.info("set mimetype: '{0}'".format(self.media_file))
        if self.media_file and self.media_file != '':
            magic_wrapper = magic.Magic(mime=True)
            try:
                self.mimetype = magic_wrapper.from_buffer(self.media_file.file.read(4096))
            except IOError:
                logging.error("Failed to determine mimetype of file {0}".format(self.media_file.file.name))
                self.mimetype = "application/octet-stream"
            logging.debug("Mime type for {0} detected as {1}".format(self.media_file.file.name, self.mimetype))

    def update_thumbnail(self):
        if not self.mimetype.startswith("image"):
            logging.error("Creating thumbnails for non-image files not supported at this time")
            # Maybe have some default image for audio/video?
            return
        # Delete old thumbnail, if any:
        if self.thumbnail and self.thumbnail != '':
            logging.info("Updating thumbnail for media item {0}, file {1}".format(self.pk, self.media_file))
            try:
                self.thumbnail.delete(save=False)
            except (IOError, OSError) as ose:
                logging.error("Failed deleting old thumbnail: {0}".format(ose))
        try:
            image = PIL.Image.open(self.media_file.file.name)
        except (IOError, OSError) as ioe:
            logging.error("Failed to read image file: {0}".format(ioe))
            return
        try:
            image.thumbnail(django.conf.settings.THUMBNAIL_SIZE, PIL.Image.ANTIALIAS)
        except MemoryError:
            logging.error("Out of memory trying to create thumbnail for {0}".format(self.media_file))

        thumb_file = os.path.join(
            django.conf.settings.MEDIA_ROOT,
            "diary_thumbnails",
            os.path.basename(str(self.media_file))
        )
        # Make sure thumbnail file ends in jpg, to avoid confusion:
        if os.path.splitext(thumb_file.lower())[1] not in (u'.jpg', u'.jpeg'):
            thumb_file += ".jpg"
        try:
            # Convert image to RGB (can't save Paletted images as jpgs) and
            # save thumbnail as JPEG:
            image.convert("RGB").save(thumb_file, "JPEG")
        except (IOError, OSError) as ioe:
            logging.error("Failed saving thumbnail: {0}".format(ioe))
            if os.path.exists(thumb_file):
                try:
                    os.unlink(thumb_file)
                except (IOError, OSError) as ioe:
                    pass
            return
        self.thumbnail = os.path.relpath(thumb_file, django.conf.settings.MEDIA_ROOT)
        self.save(update_thumbnail=False)


class EventTag(models.Model):
    name = models.CharField(max_length=32, unique=True)
    read_only = models.BooleanField(default=False, editable=False)

    class Meta:
        db_table = 'EventTags'

    def __unicode__(self):
        return self.name

    # Overloaded Django ORM method:

    def save(self, *args, **kwargs):
        if self.pk and self.read_only:
            return False
        else:
            return super(EventTag, self).save(*args, **kwargs)

    # Extra, custom methods:

    def delete(self, *args, **kwargs):
        if self.pk and self.read_only:
            return False
        else:
            return super(EventTag, self).delete(*args, **kwargs)


class Event(models.Model):

    name = models.CharField(max_length=256, blank=False)

    # This is the primary key used in the old perl/bdb system
    legacy_id = models.CharField(max_length=256, null=True, editable=False)

    template = models.ForeignKey('EventTemplate', verbose_name='Event Type',
                                 related_name='template', null=True, blank=True)
    tags = models.ManyToManyField(EventTag, db_table='Event_Tags', blank=True)

    duration = models.TimeField(null=True)

    cancelled = models.BooleanField(default=False)
    outside_hire = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    media = models.ManyToManyField(MediaItem, db_table='Event_MediaItems')

    copy = models.TextField(max_length=8192, null=True, blank=True)
    copy_summary = models.TextField(max_length=4096, null=True, blank=True)

    terms = models.TextField(max_length=4096, default=django.conf.settings.DEFAULT_TERMS_TEXT, null=True, blank=True)
    notes = models.TextField(max_length=4096, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Events'

    def __unicode__(self):
        return "%s (%d)" % (self.name, self.id)

    def reset_tags_to_default(self):
        if self.template:
            for tag in self.template.tags.all():
                self.tags.add(tag)

    def delete(self, *args, **kwargs):
        # Don't allow Events to be deleted. This doesn't block deletes on
        # querysets, SQL, etc.
        raise django.db.IntegrityError("Event deletion not allowed")

class Showing(models.Model):

    event = models.ForeignKey('Event', related_name='showings')

    start = FutureDateTimeField()

    booked_by = models.CharField(max_length=64)

    extra_copy = models.TextField(max_length=4096, null=True, blank=True)
    extra_copy_summary = models.TextField(max_length=4096, null=True, blank=True)

    confirmed = models.BooleanField(default=False)
    hide_in_programme = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    discounted = models.BooleanField(default=False)

    # sales tables?

    # Rota entries
    roles = models.ManyToManyField(Role, through='RotaEntry')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Showings'

    def __init__(self, *args, **kwargs):
        # Allow "copy_from" and "start_offset" keyword args to be supplied.
        # If "copy_from" is supplied, all showing details except for rota
        # items (which require DB writes) aare copied from the supplied Showing
        # object.
        # If "start_offset" is passed and "copy_from" is also passed, then the
        # given TimeDelta is added to copy_from.start
        # (If start_offset is defined by copy_from is not then a ValueError is
        # raised)

        copy_from = kwargs.pop('copy_from', None)
        start_offset = kwargs.pop('start_offset', None)
        if start_offset and copy_from is None:
            raise ValueError("start_offset supplied with no copy_from")

        super(Showing, self).__init__(*args, **kwargs)

        if copy_from:
            logger.info("Cloning showing from existing showing (id %d)", copy_from.pk)
            # Manually copy fields, rather than using things from copy library,
            # as don't want to copy the rota (as that would make db writes)
            attributes_to_copy = ('event', 'start', 'booked_by', 'extra_copy',
                    'confirmed', 'hide_in_programme', 'cancelled', 'discounted')
            for attribute in attributes_to_copy:
                setattr(self, attribute, getattr(copy_from, attribute))
            if start_offset:
                self.start += start_offset

    def __unicode__(self):
        if self.start is not None and self.id is not None and self.event is not None:
            return "%s - %s (%d)" % (self.start.strftime("%H:%M %d/%m/%y"), self.event.name, self.id)
        else:
            return "[uninitialised]"

    # Overload django model methods:

    def save(self, *args, **kwargs):
        # Don't allow showings to be edited if they're finished. This isn't a
        # complete fix, as operations on querysets (or just SQL) will bypass
        # this, but this will stop the forms deleting records. (Stored procedures,
        # anyone?). This also doesn't stop showings having their start date
        # moved from the past to the future!
        #
        # (For the purposes of the import script, if force=True is passed then
        # this check is bypassed)
        force = kwargs.pop('force', False)
        if self.start is not None:
            if self.in_past() and not force:
                logger.error("Tried to update showing {0} with start time {1} in the past".format(self.pk, self.start))
                raise django.db.IntegrityError("Can't update showings that start in the past")
        return super(Showing, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Don't allow showings to be deleted if they're finished. This isn't a
        # complete fix, as operations on querysets (or just SQL) will bypass
        # this, but this will stop the forms deleting records.
        if self.start is not None:
            if self.in_past():
                logger.error("Tried to delete showing {0} with start time {1} in the past".format(self.pk, self.start))
                raise django.db.IntegrityError("Can't delete showings that start in the past")
        return super(Showing, self).delete(*args, **kwargs)

    # Extra, custom methods:

    @property
    def start_date(self):
        # Used by templates
        return self.start.date()

    def in_past(self):
        return self.start < datetime.datetime.now()

    def reset_rota_to_default(self):
        """Clear any existing rota entries. If the associated event has an event
        type defined then apply the default set of rota entries for that type"""

        # Delete all existing rota entries (if any)
        self.rotaentry_set.all().delete()

        if self.event.template is not None:
            # Add a rota entry for each role in the event type:
            for role in self.event.template.roles.all():
                RotaEntry(role=role, showing=self).save()

    def clone_rota_from_showing(self, source_showing):
        assert(self.pk is not None)
        for rota_entry in source_showing.rotaentry_set.all():
            new_entry = RotaEntry(showing=self, template=rota_entry)
            new_entry.save()


class DiaryIdea(models.Model):
    month = models.DateField(editable=False)
    ideas = models.TextField(max_length=16384, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'DiaryIdeas'

    def __unicode__(self):
        return "%d/%d" % (self.month.month, self.month.year)


class EventTemplate(models.Model):

    name = models.CharField(max_length=32)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Default roles for this event
    roles = models.ManyToManyField(Role, db_table='EventTemplates_Roles')
    # Default tags for this event
    tags = models.ManyToManyField(EventTag, db_table='EventTemplate_Tags', blank=True)

    class Meta:
        db_table = 'EventTemplates'

    def __unicode__(self):
        return self.name


class RotaEntry(models.Model):

    role = models.ForeignKey(Role)
    showing = models.ForeignKey(Showing)

    required = models.BooleanField(default=True)
    rank = models.IntegerField(default=1)

    #created_at = models.DateTimeField(auto_now_add=True)
    #updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'RotaEntries'

    def __unicode__(self):
        return "%s %d" % (unicode(self.role), self.rank)

    def __init__(self, *args, **kwargs):
        # Allow a template keyword arg to be supplied. If it is, copy rota
        # details across (except for the showing id, if that's set separately)
        if 'template' in kwargs:
            template = kwargs.pop('template')
        else:
            template = None

        super(RotaEntry, self).__init__(*args, **kwargs)

        if template:
            # Only use the showing from the template if one hasn't been set yet
            if self.showing is None:
                self.showing = template.showing
            self.role = template.role
            self.required = template.required
            self.rank = template.rank
            logger.info("Cloning rota entry from existing rota entry with role_id %d", template.role.pk)
