import logging
import os.path

import magic
import PIL.Image

from django.db import models
import django.conf

logger = logging.getLogger(__name__)

class Role(models.Model):
    name = models.CharField(max_length=64, blank=False)
    description = models.CharField(max_length=64, null=True)
    shortcode = models.CharField(max_length=8, null=True)

    # Can this role be added to the rota?
    rota = models.BooleanField(default=False)

    class Meta:
        db_table = 'Roles'

    def __unicode__(self):
        return self.name

class MediaItem(models.Model):
    """Media (eg. video, audio, html fragment?). Currently to be assoicated
    with events, in future with other things?"""

    def __init__(self, *args, **kwargs):
        if 'media_file' in kwargs and 'mimetype' not in kwargs:
            kwargs['mimetype'] = self._detect_mime_type(os.path.join(django.conf.settings.MEDIA_ROOT, kwargs['media_file']))
        super(MediaItem, self).__init__(*args, **kwargs)

    media_file = models.FileField(upload_to="diary", max_length=256, null=True, blank=True, verbose_name='Image file')
    mimetype = models.CharField(max_length=64, null=True, blank=True)

    thumbnail = models.ImageField(upload_to="diary_thumbnails", max_length=256, null=True, blank=True)
    credit = models.CharField(max_length=64, null=True, blank=True, default="Internet scavenged", verbose_name='Image credit')
    caption = models.CharField(max_length=128, null=True, blank=True)

    def _detect_mime_type(self, file_path):
        # See lib/python2.7/site-packages/django/forms/fields.py for how to do
        # basic validation of PNGs / JPEGs
        m = magic.Magic(mime=True)
        try:
            mimetype = m.from_file(file_path)
        except IOError:
            logging.error("Failed to determine mimetype of file {0}".format(file_path))
            mimetype = "application/octet-stream"
        logging.debug("Mime type for {0} detected as {1}".format(file_path, mimetype))
        return mimetype

    def autoset_mimetype(self):
        if self.media_file and self.media_file != '':
            self.mimetype = self._detect_mime_type(self.media_file.file.name)

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
                logging.exception("Failed deleting old thumbnail: {0}".format(ose))
        try:
            im = PIL.Image.open(self.media_file.file.name)
        except (IOError, OSError) as ioe:
            logging.error("Failed to read image file: {0}".format(ioe))
            return
        try:
            im.thumbnail(django.conf.settings.THUMBNAIL_SIZE, PIL.Image.ANTIALIAS)
        except MemoryError :
            logging.error("Out of memory trying to create thumbnail for {0}".format(self.media_file))
        thumb_file = os.path.join(django.conf.settings.MEDIA_ROOT, "diary_thumbnails", os.path.basename(str(self.media_file)))
        # Make sure thumbnail file ends in jpg, to avoid confusion:
        if os.path.splitext(thumb_file.lower())[1] not in (u'.jpg',u'.jpeg'):
            thumb_file += ".jpg"
        try:
            # Convert image to RGB (can't save Paletted images as jpgs) and 
            # save thumbnail as JPEG:
            im.convert("RGB").save(thumb_file, "JPEG")
        except (IOError, OSError) as ioe:
            logging.error("Failed saving thumbnail: {0}".format(ioe))
            if os.path.exists(thumb_file):
                try:
                    os.unlink(thumb_file)
                except (IOError, OSError) as ioe:
                    pass
            return
        self.thumbnail = thumb_file
        self.save()

    class Meta:
        db_table = 'MediaItems'

class Event(models.Model):

    name = models.CharField(max_length=256, blank=False)

    etype = models.ForeignKey('EventType', verbose_name='Event Type', related_name='etype', null=True, blank=True)
    duration = models.TimeField(null=True)

    cancelled = models.BooleanField(default=False)
    outside_hire = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    media = models.ManyToManyField(MediaItem, db_table='Event_MediaItems')
    # primary_media = models.ForeignKey('MediaItem', related_name='+', null=True, blank=True)
    # related_name="+" means that given MediaItem won't have a backlink to this model

    copy = models.TextField(max_length=8192, null=True, blank=True)
    copy_summary = models.TextField(max_length=4096, null=True, blank=True)

    terms = models.TextField(max_length=4096, null=True, blank=True)
    notes = models.TextField(max_length=4096, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Events'
    def __unicode__(self):
        return "%s (%d)" % (self.name, self.id)

class Showing(models.Model):

    event = models.ForeignKey('Event', related_name='showings')

    start = models.DateTimeField()

    booked_by = models.CharField(max_length=64, blank=False)

    @property
    def start_date(self):
        return self.start.date()

    extra_copy = models.TextField(max_length=4096, null=True)
    extra_copy_summary = models.TextField(max_length=4096, null=True)

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

    def __unicode__(self):
        if self.start is not None and self.id is not None and self.event is not None:
            return "%s - %s (%d)" % (self.start.strftime("%H:%M %d/%m/%y"), self.event.name, self.id) 
        else:
            return "[uninitialised]"

    def reset_rota_to_default(self):
        """Clear any existing rota entries. If the associated event has an event
        type defined then apply the default set of rota entries for that type"""

        # Delete all existing rota entries (if any)
        self.rotaentry_set.all().delete()

        if self.event.etype is not None:
            # Add a rota entry for each role in the event type:
            for role in self.event.etype.roles.all():
                RotaEntry(role=role, showing=self).save()


class DiaryIdea(models.Model):
    month = models.DateField(editable=False)
    ideas = models.TextField(max_length=16384, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'DiaryIdeas'
    def __unicode__(self):
        return "%d/%d" % (self.month.month, self.month.year)

class EventType(models.Model):

    name = models.CharField(max_length=32, blank=False)
    shortname = models.CharField(max_length=32, blank=False)
    description = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Default roles for this event
    roles = models.ManyToManyField(Role, db_table='EventTypes_Roles')

    class Meta:
        db_table = 'EventTypes'

    def __unicode__(self):
        return self.name

class RotaEntry(models.Model):

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
