from django.db import models

# Create your models here.

class Event(models.Model):

    name = models.CharField(max_length=256)
    copy = models.CharField(max_length=4096)
    copy_summary = models.CharField(max_length=4096)

    image = models.CharField(max_length=256)
    image_credit = models.CharField(max_length=64)

    # Event type?
    
    terms = models.CharField(max_length=4096)
    notes = models.CharField(max_length=4096)
    
    booked_by = models.CharField(max_length=64)

    confirmed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    outside_hire = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'Events'

class Showing(models.Model):

    event = models.ForeignKey('Event')

    start = models.DateTimeField()
    time = models.TimeField()

    extra_copy = models.CharField(max_length=4096)
    extra_copy_summary = models.CharField(max_length=4096)

    hide_in_programme = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    discounted = models.BooleanField(default=False)

    # sales tables?
    
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'Showings'

class DiaryIdea(models.Model):
    month = models.DateTimeField()
    ideas = models.CharField(max_length=16384, default="")
    
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    class Meta:
        db_table = 'DiaryIdeas'

class Role(models.Model):

    name = models.CharField(max_length=32)
    description = models.CharField(max_length=64)
    shortcode = models.CharField(max_length=8)

    # Can this role be added to the rota?
    rota = models.BooleanField(default=False)

    class Meta:
        db_table = 'Roles'

class EventType(models.Model):

    name = models.CharField(max_length=32)
    shortname = models.CharField(max_length=32)
    description = models.CharField(max_length=64)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    roles = models.ManyToManyField(Role, db_table='EventTypes_Roles')

    class Meta:
        db_table = 'EventTypes'
