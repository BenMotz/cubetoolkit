import json

from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
import django.http


class PublicDiaryViews(TestCase):
    """Basic test that all the public diary pages load"""

    # Some fixture data, so Showings don't 404
    fixtures = ['small_data_set.json']

    def test_view_default(self):
        # Hard code root URL to assert that it gets something:
        response = self.client.get('/diary/')
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
                         u"link": u"/diary/event/id/3/",
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


class EditDiaryViewsLoginRequired(TestCase):
    """Basic test that the private diary pages do not load without a login"""

    fixtures = ['small_data_set.json']

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


class EditDiaryViews(TestCase):
    """Basic test that the private diary pages load"""

    # Some fixture data, so Showings don't 404
    fixtures = ['small_data_set.json']

    def setUp(self):
        self.client.login(username="admin", password="T3stPassword!")

    def tearDown(self):
        self.client.logout()

    def test_view_default(self):
        url = reverse("default-edit")
        response = self.client.get(url)
        # self.assertIn(u'Event one title', response.content)
        # self.assertIn(u'<p>Event one copy</p>', response.content)
        self.assertEqual(response.status_code, 200)


class UrlTests(TestCase):
    """Test the regular expressions in urls.py"""

    def test_diary_urls(self):
        # Test all basic diary URLs
        calls_to_test = {
            # '/diary': (), # This is a 302...
            '/diary/view/': {},
            '/diary/view/2012': {'year': '2012'},
            '/diary/view/2012/': {'year': '2012'},
            '/diary/view/2012/12': {'year': '2012', 'month': '12'},
            '/diary/view/2012/12/': {'year': '2012', 'month': '12'},
            '/diary/view/2012/12/30': {'year': '2012', 'month': '12', 'day': '30'},
            '/diary/view/2012/12/30/': {'year': '2012', 'month': '12', 'day': '30'},
            '/diary/view/films/': {'event_type': 'films'},
            # Tags that are similar to, but aren't quite the same as, years:
            '/diary/view/1/': {'event_type': '1'},
            '/diary/view/12/': {'event_type': '12'},
            '/diary/view/123/': {'event_type': '123'},
            '/diary/view/12345/': {'event_type': '12345'},
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
