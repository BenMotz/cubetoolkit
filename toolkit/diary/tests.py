"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json

from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
import django.http
from mock import patch


class PublicDiaryViews(TestCase):

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
        url = reverse("year-view", kwargs={"year": "2010"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

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
                         u"name": u"Event two",
                         u"tags": u"tag two",
                         u"image": None,
                         u"start": u"13/04/2013 18:00",
                         u"link": u"/diary/event/id/3/",
                         u"copy": u"<p>Copy</p>"
                         }])

    # View of individual showing:
    def test_view_showing(self):
        url = reverse("single-showing-view", kwargs={"showing_id": "1"})
        response = self.client.get(url)
        # TODO: test data!
        self.assertEqual(response.status_code, 200)

    # Event series view:
    def test_view_event(self):
        url = reverse("single-event-view", kwargs={"event_id": "1"})
        response = self.client.get(url)
        # TODO: test data!
        self.assertEqual(response.status_code, 200)

    def test_view_event_legacy(self):
        url = reverse("single-event-view-legacyid", kwargs={"legacy_id": "100"})
        response = self.client.get(url)
        # TODO: test data!
        self.assertEqual(response.status_code, 200)


class UrlTests(TestCase):
    # Some fixture data, so Showings don't 404
    fixtures = ['small_data_set.json']

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
