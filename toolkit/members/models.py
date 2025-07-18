import os
import logging
import binascii
import datetime

from monthdelta import monthdelta

import django.db  # Used for raw query for stats
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.timezone import now as timezone_now
from django.core.exceptions import ValidationError

from toolkit.diary.models import Role
from toolkit.util import generate_random_string

logger = logging.getLogger(__name__)


class MemberManager(models.Manager):
    # Used with Member class, to encapsulate logic about selecting which
    # members should get the mailout, and other such things

    def mailout_recipients(self):
        """Get all members who should be sent the mailout"""
        return (
            self.filter(email__isnull=False)
            .exclude(email="")
            .exclude(mailout_failed=True)
            .filter(mailout=True)
        )

    # A few hard-coded SQL queries to get some of the more complex statistics:
    def get_stat_popular_email_domains(self) -> dict[str, int]:
        # Get 10 most popular email domains amongst active subscribers
        with django.db.connection.cursor() as cursor:
            cursor.execute(
                "SELECT "
                " SUBSTRING_INDEX(`email`, '@', -1) AS domain, "
                " COUNT(1) AS num "
                "FROM Members "
                "WHERE email != '' "
                "AND mailout_failed = FALSE "
                "AND mailout = TRUE "
                "GROUP BY domain "
                "ORDER BY num DESC "
                "LIMIT 10"
            )
            return dict(cursor.fetchall())

    def get_stat_popular_postcode_prefixes(self):
        # Get 10 most popular postcode prefixes
        with django.db.connection.cursor() as cursor:
            cursor.execute(
                "SELECT "
                " SUBSTRING_INDEX(`postcode`, ' ', 1) AS firstbit, "
                " COUNT(1) AS num "
                "FROM Members "
                "WHERE postcode != '' "
                "GROUP BY firstbit "
                "ORDER BY num DESC "
                "LIMIT 10"
            )
            postcode_stats = [row for row in cursor.fetchall()]
        return postcode_stats

    def expired(self):
        """Get all members with an expiry date defined, where that date is in
        the past"""
        return self.filter(membership_expires__isnull=False).filter(
            membership_expires__lt=timezone_now().date()
        )

    def unexpired(self):
        """Get all members either without an expiry date defined, or with an
        expiry date in the future (or today)"""
        return self.filter(
            Q(membership_expires__isnull=True)
            | Q(membership_expires__gte=timezone_now().date())
        )


def get_default_membership_expiry():
    if settings.MEMBERSHIP_EXPIRY_ENABLED:
        return timezone_now().date() + datetime.timedelta(
            days=settings.MEMBERSHIP_LENGTH_DAYS
        )
    else:
        return None


class Member(models.Model):

    # This is the primary key used in the old perl/bdb system, used as the
    # user-facing membership number (rather than using the private key).
    # Defaults to = pk. Note; not actually a number!
    number = models.CharField(max_length=10, editable=False)

    name = models.CharField(max_length=64)
    email = models.EmailField(max_length=64, blank=True)

    address = models.CharField(max_length=128, blank=True)
    posttown = models.CharField(max_length=64, blank=True)
    postcode = models.CharField(max_length=16, blank=True)
    country = models.CharField(max_length=32, blank=True)

    website = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    altphone = models.CharField(max_length=64, blank=True)
    personal_pronouns = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)

    is_member = models.BooleanField(default=True)
    membership_expires = models.DateField(
        null=True, blank=True, default=get_default_membership_expiry
    )

    mailout = models.BooleanField(default=True)
    mailout_failed = models.BooleanField(default=False)
    # Used for "click to unsubscribe"/"edit details" etc:
    mailout_key = models.CharField(
        max_length=32,
        blank=False,
        null=False,
        editable=False,
        default=generate_random_string,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    gdpr_opt_in = models.DateTimeField(null=True, blank=True)

    # Custom manager, includes helpful methods for selecting members:
    objects = MemberManager()

    class Meta:
        db_table = "Members"

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        # If a user number hasn't been set, save a placeholder, then re-save
        # with the private key as the number:
        set_number = False
        if self.number == "":
            set_number = True
            self.number = "?"

        result = super().save(*args, **kwargs)

        if set_number:
            self.number = self._generate_membership_number()
            self.save()

        return result

    def _generate_membership_number(self):
        membership_no = "?"

        if not self.pk:
            # No private key! Use a hash of the name:
            logger.error(
                "Trying to generate membership number without a "
                "private key. Falling back to hash of name."
            )
            membership_no = binascii.crc32(self.name) & 0xFFFFFFFF
        else:
            offset = 0
            # If private key is already in use as a membership number try
            # multiples of 100000 higher...
            while Member.objects.filter(number=str(self.pk + offset)).count():
                offset += 100000
            membership_no = str(self.pk + offset)

        return membership_no

    def has_expired(self):
        if settings.MEMBERSHIP_EXPIRY_ENABLED and self.membership_expires:
            return self.membership_expires < timezone_now().date()
        else:
            return False


#    weak_email_validator = \
#       re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b")
#    def weak_validate_email(self):
#        pass


class Volunteer(models.Model):

    member = models.OneToOneField(
        "Member", related_name="volunteer", on_delete=models.CASCADE
    )

    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    portrait = models.ImageField(
        upload_to=settings.VOLUNTEER_PORTRAIT_DIR,
        max_length=256,
        null=True,
        blank=True,
    )

    # Roles
    roles = models.ManyToManyField(
        Role, db_table="Volunteer_Roles", blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Volunteers"

    def save(self, *args, **kwargs):
        # Save the model.
        try:
            current_portrait_file = self.portrait.file.name
        except (OSError, ValueError):
            current_portrait_file = None

        if current_portrait_file != self.__original_portrait:
            # Delete old image:
            if self.__original_portrait:
                logging.info(
                    f"Deleting old volunteer portrait '{self.__original_portrait}'"
                )
                try:
                    os.unlink(self.__original_portrait)
                except OSError as err:
                    logging.error(
                        f"Failed deleting old volunteer portrait '{self.__original_portrait}': {err}"
                    )
                self.__original_portrait = None

        return super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store current filename of portrait (if any) so that, at save, changes
        # can be detected and the old image deleted:
        try:
            self.__original_portrait = (
                self.portrait.file.name if self.portrait else None
            )
        except (OSError, ValueError):
            self.__original_portrait = None

    def is_old(self):
        return (
            self.created_at
            and self.created_at.date() <= settings.DAWN_OF_TOOLKIT
        )

    def latest_general_training_record(self):
        if self.pk is None:
            return None
        records = self.training_records.filter(
            training_type=TrainingRecord.GENERAL_TRAINING
        ).order_by("-training_date")[:1]
        return records[0] if records else None


class TrainingRecord(models.Model):
    ROLE_TRAINING = "R"
    GENERAL_TRAINING = "G"
    GENERAL_TRAINING_DESC = "General Safety Training"

    TRAINING_TYPE_CHOICES = (
        (ROLE_TRAINING, "Role Specific Training"),
        (GENERAL_TRAINING, GENERAL_TRAINING_DESC),
    )

    class Meta:
        db_table = "TrainingRecords"
        ordering = ["role", "training_date", "volunteer"]

    volunteer = models.ForeignKey(
        Volunteer, related_name="training_records", on_delete=models.CASCADE
    )
    training_type = models.CharField(
        max_length=1, choices=TRAINING_TYPE_CHOICES, blank=False
    )

    role = models.ForeignKey(
        Role,
        related_name="training_records",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # Default to when the record is created:
    training_date = models.DateField(default=datetime.date.today)
    trainer = models.CharField(max_length=128)
    notes = models.TextField(blank=True)

    def __repr__(self):
        return (
            f"TrainingRecord(volunteer={self.volunteer_id}, type={self.training_type}, "
            f"role={self.role_id}, date={self.training_date} trainer={self.trainer})"
        )

    def clean(self):
        if self.training_type == self.ROLE_TRAINING and self.role is None:
            raise ValidationError({"role": "This field is required."})
        elif (
            self.training_type == self.GENERAL_TRAINING
            and self.role is not None
        ):
            raise ValidationError(
                {
                    "role": "Training role must not be set for 'General Safety' "
                    "training records."
                }
            )

    def save(self, *args, **kwargs):
        if self.training_type not in (
            self.GENERAL_TRAINING,
            self.ROLE_TRAINING,
        ):
            raise django.db.IntegrityError("training_type invalid or missing")
        if self.training_type == self.ROLE_TRAINING and self.role is None:
            raise django.db.IntegrityError(
                "role not defined but training_type is role"
            )
        return super().save(*args, **kwargs)

    def has_expired(self, expiry_age=None):
        # Don't use settings. in declaration, as it makes it impossible to mock
        if expiry_age is None:
            expiry_age = settings.DEFAULT_TRAINING_EXPIRY_MONTHS
        threshold = timezone_now().date() - monthdelta(expiry_age)
        return self.training_date and self.training_date < threshold
