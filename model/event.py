from django.db import models

# Create your models here.

class Event(models.Model):

    class Meta:
        db_table = 'Events'

    name = models.CharField(max_length=256)
    copy = models.CharField(max_length=4096)
    copy_summary = models.CharField(max_length=4096)

    image = models.CharField()
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

class Showing(models.Model):
    class Meta:
        db_table = 'Showings'

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

class DiaryIdea(models.Model):
    class Meta:
        db_table = 'DiaryIdeas'
    month = models.DateTime()
    ideas = models.CharField(max_length=16384, default="")
    
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
class EventType(models.Model):
    class Meta:
        db_table = 'EventsTypes'
    name = models.CharField(max_length=32)
    shortname = models.CharField(max_length=32)
    description = models.CharField(max_length=64)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

class Role(models.Model):
    class Meta:
        db_table = 'Roles'

    name = models.CharField(max_length=32)
    description = models.CharField(max_length=64)
    shortcode = models.CharField(max_length=8)

    rota = models.BooleanField(default=False)

