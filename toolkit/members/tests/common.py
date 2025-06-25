from datetime import date
from django.conf import settings
import django.contrib.contenttypes as contenttypes
import django.contrib.auth.models as auth_models

from toolkit.members.models import Member, Volunteer
from toolkit.diary.models import Role


class MembersTestsMixin:
    def setUp(self):
        self._setup_test_data()
        self._setup_test_users()

        return super().setUp()

    def _setup_test_data(self):
        # Roles:
        r1 = Role(name="Role 1 (standard)", read_only=False, standard=True)
        r1.save()
        r2 = Role(name="Role 2 (nonstandard)", read_only=False, standard=False)
        r2.save()
        r3 = Role(name="Role 3", read_only=False, standard=False)
        r3.save()

        # Members:
        self.mem_1 = Member(
            name="Member On\u0205",
            email="one@example.com",
            number="1",
            postcode="BS1 1AA",
        )
        self.mem_1.save()
        self.mem_2 = Member(
            name="Tw\u020d Member",
            email="two@example.com",
            number="02",
            postcode="",
            membership_expires=date(day=31, month=5, year=2010),
        )
        self.mem_2.save()
        self.mem_3 = Member(
            name="Some Third Chap",
            email="two@member.test",
            number="000",
            postcode="NORAD",
            membership_expires=date(day=1, month=6, year=2010),
        )
        self.mem_3.save()
        self.mem_4 = Member(
            name="Volunteer One",
            email="volon@cube.test",
            number="3",
            phone="0800 000 000",
            address="1 Road",
            posttown="Town of towns",
            postcode="BS6 123",
            country="UKountry",
            website="http://1.foo.test/",
        )
        self.mem_4.save()
        self.mem_5 = Member(
            name="Volunteer Two",
            email="",
            number="4",
            phone="",
            altphone="",
            address="",
            posttown="",
            postcode="",
            country="",
            website="http://two.foo.test/",
        )
        self.mem_5.save()
        self.mem_6 = Member(
            name="Volunteer Three",
            email="volthree@foo.test",
            number="4",
            phone="",
            altphone="",
            address="",
            posttown="",
            postcode="",
            country="",
            website="",
        )
        self.mem_6.save()
        self.mem_7 = Member(
            name="Volunteer Four",
            email="four4@foo.test",
            number="o4",
            phone="",
            altphone="",
            address="",
            posttown="",
            postcode="",
            country="",
            website="",
        )
        self.mem_7.save()
        self.mem_8 = Member(
            name="Number Eight, No mailout please",
            email="bart@bart.test",
            number="010",
            mailout=False,
        )
        self.mem_8.save()
        self.mem_8 = Member(
            name="Number Nine, mailout failed",
            email="frobney@squoo.test",
            number="010",
            mailout_failed=True,
        )
        self.mem_8.save()

        # Volunteers:
        self.vol_1 = Volunteer(
            member=self.mem_4,
            notes="Likes the $, the \u00a3 and the \u20ac",
            portrait=f"{settings.MEDIA_ROOT}/path/to/portrait",
        )
        self.vol_1.save()
        self.vol_1.roles.set([r1, r3])
        self.vol_1.save()

        self.vol_2 = Volunteer(member=self.mem_5)
        self.vol_2.save()

        self.vol_3 = Volunteer(member=self.mem_6)
        self.vol_3.save()
        self.vol_3.roles.set([r3])
        self.vol_3.save()

        self.vol_4 = Volunteer(
            member=self.mem_7, active=False, notes="Subliminal, superluminous"
        )
        self.vol_4.save()
        self.vol_4.roles.set([r3])
        self.vol_4.save()

    def _setup_test_users(self):
        # Read/write user:
        user_rw = auth_models.User.objects.create_user(
            "admin", "toolkit_admin@localhost", "T3stPassword!"
        )
        # read only user:
        user_r = auth_models.User.objects.create_user(
            "read_only", "toolkit_admin@localhost", "T3stPassword!1"
        )
        # no permission user:
        auth_models.User.objects.create_user(
            "no_perm", "toolkit_admin@localhost", "T3stPassword!2"
        )
        # Create dummy ContentType:
        ct = contenttypes.models.ContentType.objects.get_or_create(
            model="", app_label="toolkit"
        )[0]
        # Create 'read' and 'write' permissions:
        write_permission = auth_models.Permission.objects.get_or_create(
            name="Write access to all toolkit content",
            content_type=ct,
            codename="write",
        )[0]

        read_permission = auth_models.Permission.objects.get_or_create(
            name="Read access to all toolkit content",
            content_type=ct,
            codename="read",
        )[0]
        # Set user permissions, r/w:
        user_rw.user_permissions.add(write_permission)
        user_rw.user_permissions.add(read_permission)
        # read only:
        user_r.user_permissions.add(read_permission)
