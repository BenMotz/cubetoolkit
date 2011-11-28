from django.db import models

# Create your models here.


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

class Event(models.Model):

    name = models.CharField(max_length=256, blank=False)
    copy = models.TextField(max_length=8192, null=True)
    copy_summary = models.TextField(max_length=4096, null=True)

    image = models.FileField(upload_to="event", max_length=256, null=True)
    image_credit = models.CharField(max_length=64, null=True)

    # Event type?
    duration = models.TimeField(null=True)
    
    terms = models.TextField(max_length=4096, null=True)
    notes = models.TextField(max_length=4096, null=True)

    cancelled = models.BooleanField(default=False)
    outside_hire = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Events'
    def __unicode__(self):
        return "%s (%d)" % (self.name, self.id)

class Showing(models.Model):

    event = models.ForeignKey('Event')

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

class DiaryIdea(models.Model):
    month = models.DateField(editable=False)
    ideas = models.TextField(max_length=16384, null=True)
    
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
    role = models.ForeignKey(Role)
    showing = models.ForeignKey(Showing)

    required = models.BooleanField(default=True)
    rank = models.IntegerField(default=1)

    #created_at = models.DateTimeField(auto_now_add=True)
    #updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'RotaEntries'

    def __unicode__(self):
        return "%s %d" % (unicode(role), rank)
