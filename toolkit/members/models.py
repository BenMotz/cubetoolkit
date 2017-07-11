import os.path
import logging
import binascii

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
        with django.db.connection.cursor() as cursor:
            cursor.execute("SELECT "
                           " SUBSTRING_INDEX(`email`, '@', -1) AS domain, "
                           " COUNT(1) AS num "
                           "FROM Members "
                           "WHERE email != '' "
                           "GROUP BY domain "
                           "ORDER BY num DESC "
                           "LIMIT 10")
            email_stats = [row for row in cursor.fetchall()]
        return email_stats

    def get_stat_popular_postcode_prefixes(self):
        # Get 10 most popular postcode prefixes
        with django.db.connection.cursor() as cursor:
            cursor.execute("SELECT "
                           " SUBSTRING_INDEX(`postcode`, ' ', 1) AS firstbit, "
                           " COUNT(1) AS num "
                           "FROM Members "
                           "WHERE postcode != '' "
                           "GROUP BY firstbit "
                           "ORDER BY num DESC "
                           "LIMIT 10")
            postcode_stats = [row for row in cursor.fetchall()]
        return postcode_stats


class Member(models.Model):

    # This is the primary key used in the old perl/bdb system, used as the
    # user-facing membership number (rather than using the private key).
    # Defaults to = pk. Note; not actually a number!
    number = models.CharField(max_length=10, editable=False)

    name = models.CharField(max_length=64)
    email = models.EmailField(max_length=64, blank=True, null=True)

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
    mailout_key = models.CharField(max_length=32, blank=False, null=False,
                                   editable=False,
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
            self.number = self._generate_membership_number()
            self.save()

        return result

    def _generate_membership_number(self):
        membership_no = "?"

        if not self.pk:
            # No private key! Use a hash of the name:
            logger.error("Trying to generate membership number without a "
                         "private key. Falling back to hash of name.")
            membership_no = binascii.crc32(self.name) & 0xffffffff
        else:
            offset = 0
            # If private key is already in use as a membership number try
            # multiples of 100000 higher...
            while Member.objects.filter(number=str(self.pk + offset)).count():
                offset += 100000
            membership_no = str(self.pk + offset)

        return membership_no

#    weak_email_validator = \
#       re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b")
#    def weak_validate_email(self):
#        pass


class Volunteer(models.Model):

    member = models.OneToOneField('Member', related_name='volunteer')

    notes = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    portrait = models.ImageField(
        upload_to=settings.VOLUNTEER_PORTRAIT_DIR, max_length=256, null=True,
        blank=True)

    # Roles
    roles = models.ManyToManyField(
        Role, db_table='Volunteer_Roles', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Volunteers'

    def save(self, *args, **kwargs):
        # Save the model.
        try:
            current_portrait_file = self.portrait.file.name
        except (IOError, OSError, ValueError):
            current_portrait_file = None

        if current_portrait_file != self.__original_portrait:
            # Delete old image:
            if self.__original_portrait:
                logging.info(u"Deleting old volunteer portrait '{0}'".format(
                    self.__original_portrait))
                try:
                    os.unlink(self.__original_portrait)
                except (IOError, OSError) as err:
                    logging.error(
                        u"Failed deleting old volunteer portrait '{0}': {1}"
                        .format(self.__original_portrait, err))
                self.__original_portrait = None

        return super(Volunteer, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(Volunteer, self).__init__(*args, **kwargs)
        # Store current filename of portrait (if any) so that, at save, changes
        # can be detected and the old image deleted:
        try:
            self.__original_portrait = (
                self.portrait.file.name if self.portrait else None)
        except (IOError, OSError, ValueError):
            self.__original_portrait = None
