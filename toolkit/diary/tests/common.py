import pytz
from datetime import datetime, date
import fixtures

import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

from toolkit.diary.models import (Showing, Event, Role, EventTag, DiaryIdea,
                                  EventTemplate, RotaEntry, Room)
from toolkit.members.models import Member, Volunteer


class DiaryTestsMixin(fixtures.TestWithFixtures):

    def setUp(self):
        self._setup_test_data()
        self.useFixture(ToolkitUsersFixture())

    # Useful method:
    def assert_return_to_index(self, response):
        # Check status=200 and expected text included:
        self.assertContains(
            response,
            "<!DOCTYPE html><html>"
            "<head><title>-</title></head>"
            "<body onload='"
            "try{self.close();}catch(e){}"
            "try{parent.$.fancybox.close();}catch(e){}"
            "try{opener.location.reload(true);}catch(e){}"
            "'>Ok</body>"
            "</html>"
        )

    def assert_has_message(self, response, msg, level):
        self.assertContains(
            response,
            u'<li class="{0}">{1}</li>'.format(level, msg)
        )

    def _setup_test_data(self):

        self._fake_now = pytz.timezone(
            "Europe/London").localize(datetime(2013, 6, 1, 11, 00))

        # Roles:
        r1 = Role(name=u"Role 1 (standard)", read_only=False, standard=True)
        r1.save()
        r2 = Role(name=u"Role 2 (nonstandard)",
                  read_only=False, standard=False)
        r2.save()
        r3 = Role(name=u"Role 3", read_only=False, standard=False)
        r3.save()

        # Tags:
        t1 = EventTag(name=u"tag one", slug=u"tag-one", read_only=False)
        t1.save()
        t2 = EventTag(name=u"tag two", slug=u"tag-two",
                      promoted=True, sort_order=2, read_only=False)
        t2.save()
        # 'ag-three' is what slugify() gives for that name:
        t3 = EventTag(name=u"\u0167ag \u0165hre\u0119",
                      slug=u"ag-three", sort_order=1, promoted=True,
                      read_only=False)
        t3.save()

        Room(name="Room one", colour="#Ff0000").save()
        self.room_2 = Room(name="Room two", colour="#00abcd")
        self.room_2.save()

        # Event  outside_hire   private   Tags
        # ---------------------------------------
        # e1     True           False
        # e2     False          False
        # e3     False          False    t2
        # e4     False          False    t2
        # e5     False          True
        # e6     True           True     t3

        # Showing Event  Date    Confirmed  Hiddn  Cnclld  Dscnt|E: oside pvate
        # ------------------------------------------------------|--------------
        # e2s1    e2    1/4/13   F          F      F      F     |   F      F
        # e2s2    e2    2/4/13   T          F      F      F     |   F      F
        # e2s3    e2    3/4/13   T          F      T      F     |   F      F
        # e2s4    e2    4/4/13   T          T      F      F     |   F      F
        # e2s5    e2    5/4/13   T          T      T      F     |   F      F

        # s2      e3    13/4/13  T          F      F      F     |   F      F
        # s3      e4    9/6/13   T          F      F      F     |   F      F
        # s4      e4    14/9/13  F          F      F      F     |   F      F
        # s5      e5    14/2/13  T          F      F      F     |   F      T
        # s6      e1    15/2/13  T          T      F      F     |   F      F

        # Events:
        e1 = Event(
            name="Event one title",
            pricing="PRICING_ONE",
            copy="Event one copy",
            pre_title="PRETITLE One",
            post_title="POSTTITLE One",
            film_information="FILM_INFO_One",
            copy_summary="Event one copy summary",
            duration="01:30:00",
            outside_hire=True,
        )
        e1.save()

        self.e2 = Event(
            name="Event two title",
            # newlines will be stripped at legacy conversion:
            copy="Event\n two\n copy",
            pricing="Pricing TWO",
            copy_summary="Event two\n copy summary",
            duration="01:30:00",
            legacy_id="100",
            legacy_copy=True,
        )
        self.e2.save()

        e3 = Event(
            name="Event three title",
            pricing="Pricing THREE",
            copy="Event three Copy",
            pre_title="PRETITLE THREE",
            post_title="POSTTITLE THREE",
            film_information="FILM_INFO_THREE",
            copy_summary="Copy three summary",
            duration="03:00:00",
            notes="Notes",
        )
        e3.save()
        e3.tags.set([t2, ])
        e3.save()

        e4 = Event(
            name=u"Event four titl\u0113",
            copy=u"Event four C\u014dpy",
            pricing=u"\u00a3milliion per thing",
            pre_title=u"Pretitle four",
            post_title=u"Posttitle four",
            film_information=u"Film info for four",
            copy_summary=u"\u010copy four summary",
            terms=u"Terminal price: \u00a31 / \u20ac3",
            duration="01:00:00",
            notes=u"\u0147otes on event fou\u0159",
        )
        e4.save()
        e4.tags.set([t2, ])
        e4.save()

        e5 = Event(
            name=u"PRIVATE Event FIVE titl\u0113!",
            copy=u"PRIVATE Event 5ive C\u014dpy",
            copy_summary=u"\u010copy five summary",
            terms=u"More terms; price: \u00a32 / \u20ac5",
            duration="10:00:00",
            notes=u"\u0147otes on event five",
            private=True
        )
        e5.save()

        e6 = Event(
            name=u"PRIVATE OUTSIDE Event (Six)",
            copy=u"PRIVATE OUTSIDE Event 6ix copy",
            copy_summary=u"OUTSIDE PRIVATE \u010copy six summary",
            terms=u"Ever More terms; price: \u00a32 / \u20ac5",
            duration="4:00:00",
            notes=u"\u0147otes on private/outwide event six",
            outside_hire=True,
            private=True
        )
        e6.save()
        e6.tags.set([t3, ])
        e6.save()

        # Showings:
        self.e2s1 = Showing(  # pk :1
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 4, 1, 19, 00)),
            event=self.e2, booked_by="User",
            confirmed=False, hide_in_programme=False,
            cancelled=False, discounted=False)
        self.e2s1.save(force=True)
        self.e2s2 = Showing(  # pk :2
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 4, 2, 19, 00)),
            event=self.e2, booked_by="User",
            confirmed=True, hide_in_programme=False,
            cancelled=False, discounted=False)
        self.e2s2.save(force=True)
        e2s3 = Showing(  # pk :3
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 4, 3, 19, 00)),
            event=self.e2, booked_by="User",
            confirmed=True, hide_in_programme=False,
            cancelled=True, discounted=False)
        e2s3.save(force=True)
        e2s4 = Showing(  # pk :4
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 4, 4, 19, 00)),
            event=self.e2, booked_by="User",
            confirmed=True, hide_in_programme=True,
            cancelled=False, discounted=False)
        e2s4.save(force=True)
        e2s5 = Showing(  # pk :5
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 4, 5, 19, 00)),
            event=self.e2, booked_by="User",
            confirmed=True, hide_in_programme=True,
            cancelled=True, discounted=False)
        e2s5.save(force=True)

        s2 = Showing(
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 4, 13, 18, 00)),
            event=e3,
            booked_by="User Two",
            confirmed=True
        )
        s2.save(force=True)  # Force start date in the past

        # When the clock is patched to claim that it's 1/6/2013, this showing
        # will be in the future:
        self.e4s3 = Showing(
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 6, 9, 18, 00)),
            event=e4,
            booked_by=u"\u0102nother \u0170ser",
            confirmed=True,
            rota_notes="Some notes about the Rota!",
        )
        self.e4s3.save(force=True)  # Force start date in the past

        s4 = Showing(
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 9, 14, 18, 00)),
            event=e4,
            booked_by="User Two",
            hide_in_programme=True,
            confirmed=False
        )
        s4.save(force=True)  # Force start date in the past

        s5 = Showing(
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 2, 14, 18, 00)),
            event=e5,
            booked_by="Yet another user",
            confirmed=True,
        )
        s5.save(force=True)

        s6 = Showing(
            start=pytz.timezone(
                "Europe/London").localize(datetime(2013, 2, 15, 18, 00)),
            event=e1,
            booked_by="Blah blah",
            confirmed=True,
            hide_in_programme=True,
        )
        s6.save(force=True)

        # Rota items:
        RotaEntry(showing=self.e2s1, role=r2, rank=1).save()
        RotaEntry(showing=self.e2s1, role=r3, rank=1).save()
        RotaEntry(showing=s2, role=r1, rank=1).save()
        RotaEntry(showing=s2, role=r1, rank=2).save()
        RotaEntry(showing=s2, role=r1, rank=3).save()
        RotaEntry(showing=s2, role=r1, rank=4).save()
        RotaEntry(showing=s2, role=r1, rank=5).save()
        RotaEntry(showing=s2, role=r1, rank=6).save()
        RotaEntry(showing=self.e4s3, role=r2, rank=1).save()

        # Ideas:
        i = DiaryIdea(
            ideas="April 2013 ideas",
            month=date(year=2013, month=4, day=1)
        )
        i.save()
        i = DiaryIdea(
            ideas="May 2013 ideas",
            month=date(year=2013, month=5, day=1)
        )
        i.save()

        # Templates:
        # One role, one tag, pricing
        self.tmpl1 = EventTemplate(name="Template 1")
        self.tmpl1.save()
        self.tmpl1.roles.set([r1])
        self.tmpl1.tags.set([t1])
        self.tmpl1.pricing = u"Entry: \u00a35 / \u20ac10"
        self.tmpl1.save()

        # Two roles, two tags
        self.tmpl2 = EventTemplate(name="Template 2")
        self.tmpl2.save()
        self.tmpl2.roles.set([r1, r2])
        self.tmpl2.tags.set([t1, t3])
        self.tmpl2.save()

        # No roles, no tags, no pricing
        self.tmpl3 = EventTemplate(name="Template 3")
        self.tmpl3.save()

        # Members:
        m1 = Member(name="Member One", email="one@example.com", number="1",
                    postcode="BS1 1AA")
        m1.save()
        m2 = Member(name="Two Member", email="two@example.com", number="2",
                    postcode="")
        m2.save()
        m3 = Member(name="Volunteer One", email="volon@cube.test", number="3",
                    phone="0800 000 000", address="1 Road", posttown="Town",
                    postcode="BS6 123", country="UK",
                    website="http://foo.test/")
        m3.save()
        m4 = Member(name="Volunteer Two", email="", number="4",
                    phone="", altphone="", address="", posttown="",
                    postcode="", country="", website="http://foo.test/")
        m4.save()
        m5 = Member(name="Volunteer Three", email="volthree@foo.test",
                    number="4", phone="", altphone="", address="", posttown="",
                    postcode="", country="", website="")
        m5.save()

        # Volunteers:
        v1 = Volunteer(member=m3)
        v1.save()
        v1.roles.set([r1, r3])
        v1.save()

        v2 = Volunteer(member=m4)
        v2.save()

        v3 = Volunteer(member=m5)
        v3.save()
        v3.roles.set([r3])
        v3.save()


class ToolkitUsersFixture(fixtures.Fixture):
    def _setUp(self):
        # Read/write user:
        user_rw = auth_models.User.objects.create_user(
            'admin', 'toolkit_admin@localhost', 'T3stPassword!')
        # read only user:
        user_r = auth_models.User.objects.create_user(
            'read_only', 'toolkit_admin@localhost', 'T3stPassword!1')
        # no permission user:
        auth_models.User.objects.create_user(
            'no_perm', 'toolkit_admin@localhost', 'T3stPassword!2')
        # rota edit only user:
        user_rota = auth_models.User.objects.create_user(
            'rota_editor', 'toolkit_admin@localhost', 'T3stPassword!3')

        # Create dummy ContentType:
        ct = contenttypes.models.ContentType.objects.get_or_create(
            model='',
            app_label='toolkit'
        )[0]
        # Create 'read' and 'write' permissions:
        write_permission = auth_models.Permission.objects.get_or_create(
            name='Write access to all toolkit content',
            content_type=ct,
            codename='write'
        )[0]

        read_permission = auth_models.Permission.objects.get_or_create(
            name='Read access to all toolkit content',
            content_type=ct,
            codename='read'
        )[0]

        # retrieve permission for editing diary.models.RotaEntry rows:
        diary_content_type = contenttypes.models.ContentType.objects.get(
            app_label='diary',
            model='rotaentry',
        )

        edit_rota_permission = auth_models.Permission.objects.get(
            codename='change_rotaentry',
            content_type=diary_content_type
        )

        # Set user permissions, r/w:
        user_rw.user_permissions.add(write_permission)
        user_rw.user_permissions.add(read_permission)
        # read only:
        user_r.user_permissions.add(read_permission)
        # rota_editor:
        user_rota.user_permissions.add(edit_rota_permission)
