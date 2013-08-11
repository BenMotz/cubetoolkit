import re
import json

import pytz
from datetime import datetime, date

from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
import django.http
import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

from toolkit.diary.models import Showing, Event, Role, EventTag, DiaryIdea, EventTemplate, RotaEntry
from toolkit.members.models import Member, Volunteer


class DiaryTestsMixin(object):

    def setUp(self):
        self._setup_test_data()

        return super(DiaryTestsMixin, self).setUp()

    # Useful method:
    def assert_return_to_index(self, response):
        # Check status=200 and expected text included:
        self.assertContains(response,
            "<!DOCTYPE html><html>"
            "<head><title>-</title></head>"
            "<body onload='self.close(); opener.location.reload(true);'>Ok</body>"
            "</html>"
        )


    def _setup_test_data(self):

        self._fake_now = pytz.timezone("Europe/London").localize(datetime(2013, 6, 1, 11, 00))

        # Roles:
        r1 = Role(name=u"Role 1 (standard)", read_only=False, standard=True)
        r1.save()
        r2 = Role(name=u"Role 2 (nonstandard)", read_only=False, standard=False)
        r2.save()
        r3 = Role(name=u"Role 3", read_only=False, standard=False)
        r3.save()

        # Tags:
        t1 = EventTag(name=u"tag one", read_only=False)
        t1.save()
        t2 = EventTag(name=u"tag two", read_only=False)
        t2.save()
        t3 = EventTag(name=u"\u0167ag \u0165hre\u0119", read_only=False)
        t3.save()

        # Events:
        e1 = Event(
            name="Event one title",
            copy="Event one copy",
            copy_summary="Event one copy summary",
            duration="01:30:00",
        )
        e1.save()

        e2 = Event(
            name="Event two title",
            copy="Event two copy",
            copy_summary="Event two copy summary",
            duration="01:30:00",
            legacy_id="100",
        )
        e2.save()

        e3 = Event(
            name="Event three title",
            copy="Event three Copy",
            copy_summary="Copy three summary",
            duration="03:00:00",
            notes="Notes",
        )
        e3.save()
        e3.tags = [t2,]
        e3.save()

        e4 = Event(
            name=u"Event four titl\u0113",
            copy=u"Event four C\u014dpy",
            copy_summary=u"\u010copy four summary",
            duration="01:00:00",
            notes="\u0147otes on event fou\u0159",
        )
        e4.save()
        e4.tags = [t2,]
        e4.save()

        # Showings:
        s1 = Showing(
            start=pytz.timezone("Europe/London").localize(datetime(2013, 4, 1, 19, 00)),
            event=e2,
            booked_by="User",
        )
        s1.save(force=True)  # Force start date in the past

        s2 = Showing(
            start=pytz.timezone("Europe/London").localize(datetime(2013, 4, 13, 18, 00)),
            event=e3,
            booked_by="User Two",
            confirmed=True
        )
        s2.save(force=True)  # Force start date in the past

        # When the clock is patched to claim that it's 1/6/2013, this showing
        # will be in the future:
        s3 = Showing(
            start=pytz.timezone("Europe/London").localize(datetime(2013, 8, 13, 18, 00)),
            event=e4,
            booked_by=u"\u0102nother \u0170ser",
            confirmed=True
        )
        s3.save(force=True)  # Force start date in the past


        # Rota items:
        RotaEntry(showing=s1, role=r2, rank=1).save()
        RotaEntry(showing=s1, role=r3, rank=1).save()
        RotaEntry(showing=s2, role=r1, rank=1).save()
        RotaEntry(showing=s2, role=r1, rank=2).save()
        RotaEntry(showing=s2, role=r1, rank=3).save()
        RotaEntry(showing=s2, role=r1, rank=4).save()
        RotaEntry(showing=s2, role=r1, rank=5).save()
        RotaEntry(showing=s2, role=r1, rank=6).save()

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
        tmpl = EventTemplate(name="Template 1")
        tmpl.save()
        tmpl.roles = [r1]
        tmpl.tags = [t1]
        tmpl.save()

        tmpl = EventTemplate(name="Template 2")
        tmpl.save()
        tmpl.roles = [r2]
        tmpl.tags = [t2]
        tmpl.save()

        tmpl = EventTemplate(name="Template 3")
        tmpl.save()
        tmpl.roles = [r1, r2, r3]
        tmpl.save()

        # Members:
        m1 = Member(name="Member One", email="one@example.com", number="1", postcode="BS1 1AA")
        m1.save()
        m2 = Member(name="Two Member", email="two@example.com", number="2", postcode="")
        m2.save()
        m3 = Member(name="Volunteer One", email="volon@cube.test", number="3",
                    phone="0800 000 000", address="1 Road", posttown="Town", postcode="BS6 123", country="UK",
                    website="http://foo.test/")
        m3.save()
        m4 = Member(name="Volunteer Two", email="", number="4",
                    phone="", altphone="", address="", posttown="", postcode="", country="",
                    website="http://foo.test/")
        m4.save()
        m5 = Member(name="Volunteer Three", email="volthree@foo.test", number="4",
                    phone="", altphone="", address="", posttown="", postcode="", country="",
                    website="")
        m5.save()

        # Volunteers:
        v1 = Volunteer(member=m3)
        v1.save()
        v1.roles = [r1, r3]
        v1.save()

        v2 = Volunteer(member=m4)
        v2.save()

        v3 = Volunteer(member=m5)
        v3.save()
        v3.roles = [r3]
        v3.save()

        # System user:
        user_rw = auth_models.User.objects.create_user('admin', 'toolkit_admin@localhost', 'T3stPassword!')
        # Create dummy ContentType:
        ct = contenttypes.models.ContentType.objects.get_or_create(
            model='',
            app_label='toolkit'
        )[0]
        # Create 'write' permission:
        write_permission = auth_models.Permission.objects.get_or_create(
            name='Write access to all toolkit content',
            content_type=ct,
            codename='write'
        )[0]
        # Give "admin" user the write permission:
        user_rw.user_permissions.add(write_permission)


class PublicDiaryViews(DiaryTestsMixin, TestCase):
    """Basic test that all the public diary pages load"""

    def test_view_default(self):
        # Hard code root URL to assert that it gets something:
        response = self.client.get('/programme/')
        self.assertEqual(response.status_code, 200)

    def test_view_default_reversed(self):
        url = reverse("default-view")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_by_type(self):
        url = reverse("type-view", kwargs={"event_type": "film"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_by_year(self):
        url = reverse("year-view", kwargs={"year": "2013"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Should test the contents better, I suspect...
        self.assertContains(response, u'Event three title')
        self.assertContains(response, u'<p>Event three Copy</p>')
        # Not confirmed / private:
        self.assertNotContains(response, u'Event one title')
        self.assertNotContains(response, u'<p>Event one copy</p>')

    def test_view_by_month(self):
        url = reverse("month-view", kwargs={"year": "2010", "month": "12"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_by_day(self):
        url = reverse("day-view", kwargs={"year": "2010", "month": "12", "day": "31"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # JSON day data:
    def test_day_json(self):
        url = reverse("day-view-json", kwargs={"year": "2013", "month": "4", "day": "13"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        # Eh (shrug)
        self.assertEqual(data, [{
                         u"name": u"Event three title",
                         u"tags": u"tag two",
                         u"image": None,
                         u"start": u"13/04/2013 18:00",
                         u"link": u"/programme/event/id/3/",
                         u"copy": u"<p>Event three Copy</p>"
                         }])

    # View of individual showing:
    def test_view_showing(self):
        url = reverse("single-showing-view", kwargs={"showing_id": "1"})
        response = self.client.get(url)
        self.assertContains(response, u'Event two title')
        self.assertContains(response, u'<p>Event two copy</p>')
        self.assertEqual(response.status_code, 200)

    # Event series view:
    def test_view_event(self):
        url = reverse("single-event-view", kwargs={"event_id": "1"})
        response = self.client.get(url)
        # TODO: test data better, including media!
        self.assertContains(response, u'Event one title')
        self.assertContains(response, u'<p>Event one copy</p>')
        self.assertEqual(response.status_code, 200)

    def test_view_event_legacy(self):
        url = reverse("single-event-view-legacyid", kwargs={"legacy_id": "100"})
        response = self.client.get(url)
        # TODO: test data!
        self.assertEqual(response.status_code, 200)

    # TODO: Cancelled/confirmed/visible/TTT


class EditDiaryViewsLoginRequired(DiaryTestsMixin, TestCase):
    """Basic test that the private diary pages do not load without a login"""

    def test_urls(self):
        views_to_test = {
            "default-edit": {},
            "year-edit": {"year": "2013"},
            "month-edit": {"year": "2013", "month": "1"},
            "day-edit": {"year": "2013", "month": "1", "day": "1"},
            "edit-event-details-view": {"pk": "1"},
            "edit-event-details": {"event_id": "1"},
            "edit-showing": {"showing_id": "1"},
            "edit-ideas": {"year": "2012", "month": "1"},
            "add-showing": {"event_id": "1"},
            "delete-showing": {"showing_id": "1"},
            "add-event": {},

            "edit_event_templates": {},
            "edit_event_tags": {},
            "edit_roles": {},
            "members-mailout": {},
            "exec-mailout": {},
            "mailout-progress": {},
            "set_edit_preferences": {},
        }
        for view_name, kwargs in views_to_test.iteritems():
            url = reverse(view_name, kwargs=kwargs)
            expected_redirect = "{0}?next={1}".format(reverse("django.contrib.auth.views.login"), url)

            # Test GET:
            response = self.client.get(url)
            self.assertRedirects(response, expected_redirect)

            # Test POST:
            response = self.client.post(url)
            self.assertRedirects(response, expected_redirect)


class EditDiaryViews(DiaryTestsMixin, TestCase):
    """Basic test that the private diary pages load"""

    def setUp(self):
        super(EditDiaryViews, self).setUp()

        self.client.login(username="admin", password="T3stPassword!")

    def tearDown(self):
        self.client.logout()

    def test_view_default(self):
        url = reverse("default-edit")
        response = self.client.get(url)
        # self.assertIn(u'Event one title', response.content)
        # self.assertIn(u'<p>Event one copy</p>', response.content)
        self.assertEqual(response.status_code, 200)


class AddShowing(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(AddShowing, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def test_add_showing_must_post(self):
        # Add a new showing
        url = reverse("add-showing", kwargs={"event_id": 1})
        url += "?copy_from=2"
        # TODO: Add more query data that might work
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)

    def test_add_showing_no_copy_from(self):
        # No copy_from parameter: should return 404
        url = reverse("add-showing", kwargs={"event_id": 1})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_add_showing_no_start(self):
        url = reverse("add-showing", kwargs={"event_id": 1})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 1)

        response = self.client.post(url, data={
            "booked_by": "someone",
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before)

        self.assertFormError(response, 'clone_showing_form', 'clone_start', u'This field is required.')

    def test_add_showing_no_booked_by(self):
        url = reverse("add-showing", kwargs={"event_id": 1})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 1)

        # Start is in past, but should get error about missing booked_by
        response = self.client.post(url, data={
            "clone_start": "13/07/2010 20:00"
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before)

        self.assertFormError(response, 'clone_showing_form', 'booked_by', u'This field is required.')

    @patch('django.utils.timezone.now')
    def test_add_showing_in_past(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("add-showing", kwargs={"event_id": 1})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 1)

        # do add/clone:
        response = self.client.post(url, data={
            "booked_by": u"Someone",
            "clone_start": u"01/01/2010 20:00"  # The past!
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before)

        self.assertFormError(response, 'clone_showing_form', 'clone_start', u'Must be in the future')

    @patch('django.utils.timezone.now')
    def test_add_showing(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("add-showing", kwargs={"event_id": 1})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 1)

        # do add/clone:
        response = self.client.post(url, data={
            "booked_by": u"Someone or the other - \u20ac",
            "clone_start": "13/07/2013 20:00"
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before + 1)

        # Get clone:
        dest = list(source.event.showings.all())[-1]

        # Check "booked by":
        self.assertEqual(dest.booked_by, u"Someone or the other - \u20ac")

        # Check fields were cloned:
        self.assertEqual(source.event_id, dest.event_id)
        self.assertEqual(source.extra_copy, dest.extra_copy)
        self.assertEqual(source.extra_copy_summary, dest.extra_copy_summary)
        self.assertEqual(source.confirmed, dest.confirmed)
        self.assertEqual(source.hide_in_programme, dest.hide_in_programme)
        self.assertEqual(source.cancelled, dest.cancelled)
        self.assertEqual(source.discounted, dest.discounted)

        # Check rota cloned:
        src_rota = source.rotaentry_set.all()
        dst_rota = dest.rotaentry_set.all()

        self.assertEqual(
            len(src_rota),
            len(dst_rota)
        )

        for src_entry, dst_entry in zip(source.rotaentry_set.all(), dest.rotaentry_set.all()):
            self.assertEqual(src_entry.role, dst_entry.role)
            self.assertEqual(src_entry.rank, dst_entry.rank)

        self.assert_return_to_index(response)

class DeleteShowing(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(DeleteShowing, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def test_delete_showing_must_post(self):

        url = reverse("delete-showing", kwargs={"showing_id": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        Showing.objects.get(id=1)  # Will raise an exception if it doesn't exist

    @patch('django.utils.timezone.now')
    def test_delete_showing_in_past(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("delete-showing", kwargs={"showing_id": 1})
        response = self.client.post(url)

        # Should redirect to edit page:
        self.assertRedirects(response, reverse("edit-showing", kwargs={"showing_id": 1}))

        # Showing should still exist:
        Showing.objects.get(id=1)  # Will raise an exception if it doesn't exist

    @patch('django.utils.timezone.now')
    def test_delete_showing(self, now_patch):
        now_patch.return_value = self._fake_now

        self.assertTrue(Showing.objects.filter(id=3))

        url = reverse("delete-showing", kwargs={"showing_id": 3})
        response = self.client.post(url)

        # Showing should have been deleted
        self.assertFalse(Showing.objects.filter(id=3))

        self.assert_return_to_index(response)


class PreferencesTests(DiaryTestsMixin, TestCase):
    def setUp(self):
        super(PreferencesTests, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")


    def _get_edit_prefs(self, response):
        match = re.search(ur"var\s+edit_prefs\s*=\s*({.*?});", str(response), re.DOTALL)
        return json.loads(match.group(1))

    def test_set_pref(self):
        url = reverse("default-edit")

        # Get current prefs:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "true")

        # Set popups false:
        response = self.client.get(reverse("set_edit_preferences"),
            data={"popups": "false"})
        self.assertEqual(response.status_code, 200)

        # Verify change:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "false")

        # Back to true:
        response = self.client.get(reverse("set_edit_preferences"),
            data={"popups": "true"})
        self.assertEqual(response.status_code, 200)

        # Verify change:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "true")

    def test_bad_value(self):
        url = reverse("default-edit")

        # Set popups something stupid:
        response = self.client.get(reverse("set_edit_preferences"),
            data={"popups": "tralala"*100})
        self.assertEqual(response.status_code, 200)

        # Verify change:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "tralalatra")

    def test_bad_pref(self):
        url = reverse("default-edit")

        # Set weird value, verify it doesn't come out in the edit page:
        response = self.client.get(reverse("set_edit_preferences"),
            data={"nonsense": "tralala"})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs.keys(), ["popups"])

    def test_redirect_change(self):
        url = reverse("cancel-edit")
        # default to javscript hackery:
        response = self.client.get(url)
        self.assert_return_to_index(response)

        # Set popup preference false:
        response = self.client.get(reverse("set_edit_preferences"),
            data={"popups": "false"})
        self.assertEqual(response.status_code, 200)

        # should now 302 to edit list:
        response = self.client.get(url)
        self.assertRedirects(response, reverse("default-edit"))



class UrlTests(DiaryTestsMixin, TestCase):
    """Test the regular expressions in urls.py"""

    def test_diary_urls(self):
        # Test all basic diary URLs
        calls_to_test = {
            # '/diary': (), # This is a 302...
            '/programme/view/': {},
            '/programme/view/2012': {'year': '2012'},
            '/programme/view/2012/': {'year': '2012'},
            '/programme/view/2012/12': {'year': '2012', 'month': '12'},
            '/programme/view/2012/12/': {'year': '2012', 'month': '12'},
            '/programme/view/2012/12/30': {'year': '2012', 'month': '12', 'day': '30'},
            '/programme/view/2012/12/30/': {'year': '2012', 'month': '12', 'day': '30'},
            '/programme/view/films/': {'event_type': 'films'},
            # Tags that are similar to, but aren't quite the same as, years:
            '/programme/view/1/': {'event_type': '1'},
            '/programme/view/12/': {'event_type': '12'},
            '/programme/view/123/': {'event_type': '123'},
            '/programme/view/12345/': {'event_type': '12345'},
        }
        for query, response in calls_to_test.iteritems():
            match = resolve(query)
            self.assertEqual(match.func.__name__, "view_diary")
            for k, v in response.iteritems():
                self.assertEqual(match.kwargs[k], v)

    def test_diary_invalid_urls(self):
        # Test all basic diary URLs

        calls_to_test = (
            '/diary/123',
            '/diary/-123',
            '/diary/-2012/',
            '/diary/2012//',
            '/diary/2012///',
        )
        for query in calls_to_test:
            self.assertRaises(django.http.Http404, resolve, query)

    def test_diary_edit_urls(self):
        # Test all basic diary URLs

        calls_to_test = {
            '/diary/edit': {},
            '/diary/edit/': {},
            '/diary/edit/2012': {'year': '2012'},
            '/diary/edit/2012/': {'year': '2012'},
            '/diary/edit/2012/12': {'year': '2012', 'month': '12'},
            '/diary/edit/2012/12/': {'year': '2012', 'month': '12'},
            '/diary/edit/2012/12/30': {'year': '2012', 'month': '12', 'day': '30'},
            '/diary/edit/2012/12/30/': {'year': '2012', 'month': '12', 'day': '30'},
        }
        for query, response in calls_to_test.iteritems():
            match = resolve(query)
            self.assertEqual(match.func.__name__, "edit_diary_list")
            for k, v in response.iteritems():
                self.assertEqual(match.kwargs[k], v)

    def test_diary_rota_urls(self):
        # Test all basic diary URLs

        calls_to_test = {
            '/diary/rota': {'field': 'rota'},
            '/diary/rota/': {'field': 'rota'},
            '/diary/rota/2012/12': {'field': 'rota', 'year': '2012', 'month': '12'},
            '/diary/rota/2012/12/': {'field': 'rota', 'year': '2012', 'month': '12'},
            '/diary/rota/2012/12/30': {'field': 'rota', 'year': '2012', 'month': '12', 'day': '30'},
            '/diary/rota/2012/12/30/': {'field': 'rota', 'year': '2012', 'month': '12', 'day': '30'},
            '/diary/rota/2012/12//': {'field': 'rota', 'year': '2012', 'month': '12', 'day': ''},
        }
        # (rota URLS must have at least year/month, not just a year!)
        for query, response in calls_to_test.iteritems():
            match = resolve(query)
            self.assertEqual(match.func.__name__, "view_event_field")
            for k, v in response.iteritems():
                self.assertEqual(match.kwargs[k], v)
