import re
import logging
import os.path

from django.db import models
from django.conf import settings
import django.utils.timezone
import django.core.exceptions
from django.utils.safestring import mark_safe
from django.db.models.query import QuerySet

from south.modelsinspector import add_introspection_rules

logger = logging.getLogger(__name__)

from toolkit.diary.validators import validate_in_future
import toolkit.util.image as imagetools


class FutureDateTimeField(models.DateTimeField):
    """DateTime field that can only be set to times in the future.
    Used for Showing start times"""
    default_error_messages = {
        'invalid': 'Date may not be in the past',
    }
    default_validators = [validate_in_future]

# Having defined a custom field, need to tell South that it doesn't need to do
# anything special when creating/applying database migrations:
add_introspection_rules([], [r"^toolkit\.diary\.models\.FutureDateTimeField"])


class Role(models.Model):
    name = models.CharField(max_length=64, unique=True)

    standard = models.BooleanField(default=False,
                                   help_text="Should this role be presented in the main list of roles for events")

    # Allow role to be edited/deleted
    read_only = models.BooleanField(default=False)

    class Meta:
        db_table = 'Roles'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        result = super(Role, self).__init__(*args, **kwargs)
        # Store original value of name, so it can't be edited for
        # read only roles
        self._original_name = self.name
        return result

    def save(self, *args, **kwargs):
        if self.read_only and self._original_name != self.name:
            logger.error(u"Tried to edit read-only role {0}".format(self.name))
            return
        else:
            return super(Role, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Don't allow read_only roles to be deleted
        if self.pk and self.read_only:
            logger.error(u"Tried to delete read-only role {0}".format(self.name))
            return False
        else:
            return super(Role, self).delete(*args, **kwargs)


class MediaItem(models.Model):
    """Media (eg. video, audio, html fragment?). Currently to be assoicated
    with events, in future with other things?"""

    media_file = models.FileField(upload_to="diary", max_length=256, null=True, blank=True, verbose_name='Image file')
    mimetype = models.CharField(max_length=64, editable=False)

    credit = models.CharField(max_length=256, null=True, blank=True,
                              default="Internet scavenged", verbose_name='Image credit')
    caption = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        db_table = 'MediaItems'

    def __unicode__(self):
        return u"{0}: {1}".format(self.pk, self.media_file)

    # Overloaded Django ORM method:

    def save(self, *args, **kwargs):
        # Before saving, update mimetype field:
        # (do this even if file name has stayed the same, as file may have been
        # overwritten)
        self.autoset_mimetype()

        return super(MediaItem, self).save(*args, **kwargs)

    # Extra, custom methods:
    def autoset_mimetype(self):
        # See lib/python2.7/site-packages/django/forms/fields.py for how to do
        # basic validation of PNGs / JPEGs
        if self.media_file and self.media_file.name != '':
            try:
                self.mimetype = imagetools.get_mimetype(self.media_file.file)
            except IOError:
                logger.error(u"Failed to determine mimetype of file {0}".format(self.media_file.file.name))
                self.mimetype = "application/octet-stream"
            logger.debug(u"Mime type for {0} detected as {1}".format(self.media_file.file.name, self.mimetype))


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

    outside_hire = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    media = models.ManyToManyField(MediaItem, db_table='Event_MediaItems')

    copy = models.TextField(max_length=8192, null=True, blank=True)
    copy_summary = models.TextField(max_length=4096, null=True, blank=True)

    # Following flag is True when the event copy has been imported from the
    # "legacy" toolkit; the bizarre text wrapping will be fixed up before
    # display, regex will be applied to turn http://.* into links, etc.
    legacy_copy = models.BooleanField(default=False, null=False, editable=False)

    terms = models.TextField(max_length=4096, default=settings.DEFAULT_TERMS_TEXT, null=True, blank=True)
    notes = models.TextField(max_length=4096, null=True, blank=True, verbose_name="Programmer's notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Events'

    def __unicode__(self):
        return u"{0} ({1})".format(self.name, self.id)

    def reset_tags_to_default(self):
        if self.template:
            for tag in self.template.tags.all():
                self.tags.add(tag)

    def delete(self, *args, **kwargs):
        # Don't allow Events to be deleted. This doesn't block deletes on
        # querysets, SQL, etc.
        raise django.db.IntegrityError("Event deletion not allowed")

    # Extra, custom methods:
    def clear_main_mediaitem(self):
        if self.media.count() == 0:
            return
        media_item = self.media.all()[0]
        logger.info(u"Removing media file {0} from event {1}".format(media_item, self.pk))
        self.media.remove(media_item)
        ## If the media item isn't associated with any events, delete it:
        ## ACTUALLY: let's keep it. Disk space is cheap, etc.
        # if media_item.event_set.count() == 0:
        #    media_item.delete()

    def set_main_mediaitem(self, media_file):
        self.clear_main_mediaitem()
        logger.info(u"Adding media file {0} to event {1}".format(media_file, self.pk))
        self.media.add(media_file)

    def get_main_mediaitem(self):
        if self.media.count() == 0:
            return None
        return self.media.all()[0]

    # Regular expressions for mangling legacy copy:
    _wrap_re = re.compile(r'(.{70,})\n')
    _lotsofnewlines_re = re.compile(r'\n\n+')
    # Catch well-formatted links (ie. beginning http://)
    _link_re_1 = re.compile(r'(http:\/\/\S{4,})')
    # Optimistic stab at spotting other things that are probably links, based on
    # a smattering of TLDs:
    _link_re_2 = re.compile(r'(\s)(www\.[\w.]+\.(com|org|net|uk|de|ly|us|tk)[^\t\n\r\f\v\. ]*)')

    @property
    def copy_html(self):
        """If self.legacy_copy == True, then try to mangle self.copy into
        sane HTML fragment. Otherwise return self.copy
        (Legacy cube copy has line breaks around the 70-80 character mark, and no
        hyperlinks)"""

        if not self.legacy_copy:
            return mark_safe(self.copy)
        else:
            # remove all whitespace from start and end of line:
            result = self.copy.strip()
            # Strip out carriage returns:

            result = result.strip().replace('\r', '')
            # Strip out new lines when they occur after 70 other characters (try to fix wrapping)
            result = self._wrap_re.sub(r'\1 ', result)
            # Replace a sequence of 2+ new lines with a double line break;
            result = self._lotsofnewlines_re.sub(' <br><br>', result)

            # Now replace all new lines with a single line break;
            result = result.replace('\n', ' <br>\n')

            # Attempt to magically convert any links to markdown:
            result = self._link_re_1.sub(r'<a href="\1">\1</a>', result)
            result = self._link_re_2.sub(r'\1<a href="http://\2">\2</a>', result)

            return mark_safe(result)


class ShowingQuerySet(QuerySet):
    """
    This class provides some custom methods to make searching and selecting
    sets of Showings clearer
    """
    def start_in_range(self, startdate, enddate):
        """Filter showings that have a start date in the given range"""
        return self.filter(start__range=[startdate, enddate])

    def public(self):
        """
        Filters so only showings that should be visible to the general public
        are included. (ie. exclude unconfirmed, hidden in programme)
        """
        return (self.filter(event__private=False)
                    .filter(confirmed=True)
                    .filter(hide_in_programme=False))

    def not_cancelled(self):
        """Filter out cancelled showings"""
        return self.filter(cancelled=False)

    def confirmed(self):
        """Filter out unconfirmed showings"""
        return self.filter(confirmed=True)


class ShowingManager(models.Manager):
    """
    Glue class to allow the ShowingQuerySet to be transparently used with the
    Showing model
    """
    def get_query_set(self):
        return ShowingQuerySet(self.model, using=self._db)

    def __getattr__(self, name):
        try:
            return getattr(self.__class__, name)
        except AttributeError:
            return getattr(self.get_query_set(), name)


class Showing(models.Model):

    event = models.ForeignKey('Event', related_name='showings')

    start = FutureDateTimeField(db_index=True)

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

    # Custom manager, with some extra methods:
    objects = ShowingManager()

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
            logger.info(u"Cloning showing from existing showing (id {0})".format(copy_from.pk))
            # Manually copy fields, rather than using things from copy library,
            # as don't want to copy the rota (as that would make db writes)
            attributes_to_copy = ('event', 'start', 'booked_by', 'extra_copy', 'confirmed',
                                  'hide_in_programme', 'cancelled', 'discounted')
            for attribute in attributes_to_copy:
                setattr(self, attribute, getattr(copy_from, attribute))
            if start_offset:
                self.start += start_offset

    def __unicode__(self):
        if self.start is not None and self.id is not None and self.event is not None:
            return u"{0} - {1} ({2})".format(self.start.strftime("%H:%M %Z%z %d/%m/%y"), self.event.name, self.id)
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
                logger.error(u"Tried to update showing {0} with start time {1} in the past".format(self.pk, self.start))
                raise django.db.IntegrityError("Can't update showings that start in the past")
        return super(Showing, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Don't allow showings to be deleted if they're finished. This isn't a
        # complete fix, as operations on querysets (or just SQL) will bypass
        # this, but this will stop the forms deleting records.
        if self.start is not None:
            if self.in_past():
                logger.error(u"Tried to delete showing {0} with start time {1} in the past".format(self.pk, self.start))
                raise django.db.IntegrityError("Can't delete showings that start in the past")
        return super(Showing, self).delete(*args, **kwargs)

    # Extra, custom methods:

    @property
    def start_date(self):
        # Used by templates
        return self.start.date()

    def in_past(self):
        return self.start < django.utils.timezone.now()

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

    def update_rota(self, _rota):
        """Update rota from supplied dict. Dict should be a map of
        role_id: no. entries
        If no. entries is 0, any existing RotaEntries are deleted. If it's greater
        than the number of RotaEntries, they'r added as required. If a role_id is
        not in the dict, then any RotaEntries aren't affected"""

        # copy rota:
        rota = dict(_rota)

        # Build map of rota entries by role id
        rota_entries_by_id = {}
        for re in self.rotaentry_set.select_related():
            rota_entries_by_id.setdefault(re.role.pk, []).append(re)

        for role_id, count in rota.iteritems():
            # Number of existing rota entries for this role_id.
            # Remove from dict, so anything left in the dict at the end
            # is an error...
            existing_entries = rota_entries_by_id.pop(role_id, [])
            # delete highest ranked instances
            while count < len(existing_entries):
                logger.info(u"Removing role {0} from showing {1}".format(role_id, self.pk))
                highest_ranked = max(existing_entries, key=lambda re: re.rank)
                highest_ranked.delete()
                existing_entries.remove(highest_ranked)
            # add required entries
            while count > len(existing_entries):
                logger.info(u"Adding role {0} to showing {1}".format(role_id, self.pk))
                # add rotaentries
                new_re = RotaEntry(role_id=role_id, showing=self)
                if len(existing_entries) > 0:
                    new_re.rank = 1 + max(existing_entries, key=lambda re: re.rank).rank
                new_re.save()
                existing_entries.append(new_re)


class DiaryIdea(models.Model):
    month = models.DateField(editable=False)
    ideas = models.TextField(max_length=16384, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'DiaryIdeas'

    def __unicode__(self):
        return u"{0}/{1}".format(self.month.month, self.month.year)


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

    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'RotaEntries'

    def __unicode__(self):
        return u"{0} {1}".format(unicode(self.role), self.rank)

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
            logger.info(u"Cloning rota entry from existing rota entry with role_id {0}".format(template.role.pk))
