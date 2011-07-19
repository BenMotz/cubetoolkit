from django.db import models

# Create your models here.

class Event(models.Model):

    name = models.CharField(max_length=256, blank=False)
    copy = models.CharField(max_length=8192, null=True)
    copy_summary = models.CharField(max_length=4096, null=True)

    image = models.FileField(upload_to="event", max_length=256, null=True)
    image_credit = models.CharField(max_length=64, null=True)

    # Event type?
    duration = models.TimeField(null=True)
    
    terms = models.CharField(max_length=4096, null=True)
    notes = models.CharField(max_length=4096, null=True)
    
    booked_by = models.CharField(max_length=64, blank=False)

    confirmed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    outside_hire = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Events'

class Showing(models.Model):

    event = models.ForeignKey('Event')

    start = models.DateTimeField()

    extra_copy = models.CharField(max_length=4096, null=True)
    extra_copy_summary = models.CharField(max_length=4096, null=True)

    hide_in_programme = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    discounted = models.BooleanField(default=False)

    # sales tables?
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Showings'

class DiaryIdea(models.Model):
    month = models.DateField()
    ideas = models.CharField(max_length=16384, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'DiaryIdeas'

class Role(models.Model):

    name = models.CharField(max_length=32, blank=False)
    description = models.CharField(max_length=64, null=True)
    shortcode = models.CharField(max_length=8, blank=False)

    # Can this role be added to the rota?
    rota = models.BooleanField(default=False)

    class Meta:
        db_table = 'Roles'

class EventType(models.Model):

    name = models.CharField(max_length=32, blank=False)
    shortname = models.CharField(max_length=32, blank=False)
    description = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    roles = models.ManyToManyField(Role, db_table='EventTypes_Roles')

    class Meta:
        db_table = 'EventTypes'

