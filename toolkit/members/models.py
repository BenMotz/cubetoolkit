# import re
# import magic
# import PIL.Image

from django.db import models

from toolkit.diary.models import Role

class Member(models.Model):

    # This is the primary key used in the old perl/bdb system, used as the
    # user-facing membership number (rather than using the private key). 
    # Defaults to = pk. Note; not actually a number!
    number = models.CharField(max_length=10, null=False, blank=False, editable=False)

    name = models.CharField(max_length=64, blank=False, null=False)
    email = models.CharField(max_length=64, blank=True, null=True) # , unique=True)

    address = models.CharField(max_length=128, blank=True, null=True)
    posttown = models.CharField(max_length=64, blank=True, null=True)
    postcode = models.CharField(max_length=16, blank=True, null=True)
    country = models.CharField(max_length=32, blank=True, null=True)

    website = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=64, blank=True, null=True)
    altphone = models.CharField(max_length=64, blank=True, null=True)
    notes = models.CharField(max_length=1024, blank=True, null=True)

    mailout = models.BooleanField(default=True, blank=False, null=False)
    mailout_failed = models.BooleanField(default=False, blank=False, null=False)

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

    notes = models.CharField(max_length=4096, blank=True, null=True)
    active = models.BooleanField(default=True, blank=False, null=False)

    portrait = models.ImageField(upload_to="volunteers", max_length=256, null=True, blank=True)
    portrait_thumb = models.ImageField(upload_to="volunteers_thumbnails", max_length=256, null=True, blank=True, editable=False)

    # Roles
    roles = models.ManyToManyField(Role, db_table='Volunteer_Roles')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Volunteers'
